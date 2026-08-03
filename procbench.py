from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import openai
import pandas as pd
from openreward.environments import Environment, JSONObject, TextBlock, ToolOutput, tool
from pydantic import BaseModel, Field


# How many times to attempt the grader completion before giving up. A failed
# grader call is an infrastructure failure, not a wrong answer, so it is worth
# retrying; once the budget is exhausted _grade_answer RAISES rather than
# fabricating a reward.
RETRY_BUDGET = int(os.environ.get("RETRY_BUDGET", "3"))


# Data loading with intelligent fallback (production vs dev)
if os.path.exists("/orwd_data"):
    DATA_PATH = Path("/orwd_data")
else:
    DATA_PATH = Path(__file__).parent

# Load parquet at module import time
tasks_df = pd.read_parquet(DATA_PATH / "procbench_data.parquet")

# Clean up: drop unnecessary columns and handle NaN values
if '__index_level_0__' in tasks_df.columns:
    tasks_df = tasks_df.drop('__index_level_0__', axis=1)
tasks_df = tasks_df.fillna('')

tasks_list = tasks_df.to_dict(orient="records")

# Normalize data structure for OpenReward
for task in tasks_list:
    task['id'] = task['problem_name']
    # Parse intermediate from JSON string back to list
    if isinstance(task['intermediate'], str):
        task['intermediate'] = json.loads(task['intermediate'])
    # Ensure all fields are strings
    task['init'] = str(task['init'])
    task['final'] = str(task['final'])
    task['intermediate'] = [str(x) for x in task['intermediate']]


class ProcBenchTaskSpec(BaseModel):
    """Task specification schema for ProcBench."""
    id: str
    prompt: str
    init: str
    final: str
    intermediate: list[str]
    task_name: str
    example_name: str


class SubmitAnswerParams(BaseModel):
    """Parameters for submitting an answer."""
    answer: str = Field(..., description="Final answer after completing all procedural steps")


class ProcBench(Environment):
    """
    ProcBench environment - a multi-step procedural reasoning benchmark.

    Dataset contains 5,520 examples across 23 different procedural tasks.
    Each task requires following explicit step-by-step instructions to arrive at the final answer.
    """

    def __init__(self, task_spec: JSONObject = {}, secrets: dict[str, str] = {}) -> None:
        super().__init__(task_spec)
        self.config = ProcBenchTaskSpec.model_validate(task_spec)

        # Initialize OpenAI client for grading
        api_key = secrets.get("openai_api_key")
        if not api_key:
            raise ValueError(
                "OpenAI API key required in secrets (key: 'openai_api_key')"
            )
        self.grader_client = openai.AsyncClient(api_key=api_key)

    @classmethod
    def list_splits(cls) -> list[str]:
        """List available data splits."""
        return ["test"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        """List all tasks for a given split."""
        if split == "test":
            return tasks_list
        raise ValueError(f"Unknown split: {split}. Available splits: {cls.list_splits()}")

    async def get_prompt(self) -> list[TextBlock]:
        """Get the task prompt as a list of TextBlocks."""
        return [TextBlock(type="text", text=self.config.prompt)]

    @tool
    async def submit_answer(self, params: SubmitAnswerParams) -> ToolOutput:
        """
        Submit your final answer after following all procedural steps.

        The answer will be evaluated by an LLM grader that compares your answer
        to the expected answer, accounting for equivalent formats and minor variations.

        Args:
            params: SubmitAnswerParams containing the final answer

        Returns:
            ToolOutput with grader feedback, reward, and finished flag
        """
        submitted = params.answer.strip()
        expected = self.config.final.strip()

        # Use LLM grader to evaluate the answer
        grading_result = await self._grade_answer(submitted, expected)

        return ToolOutput(
            blocks=[TextBlock(type="text", text=grading_result["message"])],
            metadata={
                "task_id": self.config.id,
                "task_name": self.config.task_name,
                "example_name": self.config.example_name,
                "submitted_answer": submitted,
                "expected_answer": expected,
                "correct": grading_result["correct"],
                "grader_reasoning": grading_result["reasoning"],
                "init_state": self.config.init,
                "expected_intermediate": self.config.intermediate,
            },
            reward=grading_result["reward"],
            finished=True,
        )

    async def _grade_answer(self, submitted: str, expected: str) -> dict[str, Any]:
        """
        Grade the submitted answer against the expected answer using LLM.

        Uses gpt-5-mini to determine if the answers are equivalent,
        accounting for formatting differences and minor variations.

        Args:
            submitted: The answer submitted by the agent
            expected: The expected correct answer

        Returns:
            dict with keys: correct (bool), reward (float), reasoning (str), message (str)
        """
        grader_prompt = f"""You are evaluating whether a submitted answer is correct for a procedural reasoning task.

SUBMITTED ANSWER: {submitted}
EXPECTED ANSWER: {expected}

Determine if the submitted answer is equivalent to the expected answer. Consider:
- Minor formatting differences (spacing, capitalization)
- Equivalent representations (e.g., "1.5" vs "1.50")
- The essential correctness of the procedural result

Respond with a JSON object containing:
{{
  "correct": true or false,
  "reasoning": "Brief 1-2 sentence explanation"
}}"""

        last_error: Exception | None = None
        result: dict[str, Any] | None = None

        for attempt in range(1, RETRY_BUDGET + 1):
            try:
                response = await self.grader_client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": grader_prompt}],
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)
                break
            except Exception as e:
                last_error = e
                print(
                    f"[GRADER ERROR] attempt {attempt}/{RETRY_BUDGET} failed: {e}"
                )
                if attempt < RETRY_BUDGET:
                    await asyncio.sleep(2 ** (attempt - 1))

        if result is None:
            # Every attempt failed, so we could not grade this submission. RAISE —
            # do NOT fabricate a reward. Returning 0.0 (or falling back to an exact
            # string match, which a verbose answer will essentially always fail)
            # would record an infrastructure failure as a genuine wrong answer:
            # indistinguishable from a real zero downstream, and it trains the agent
            # against a failure it did not cause. Raising lets the platform retry the
            # tool call and, on persistent failure, end the rollout with no reward.
            raise RuntimeError(
                f"Grader failed after {RETRY_BUDGET} attempt(s); cannot grade "
                f"this submission: {last_error}"
            ) from last_error

        is_correct = result.get("correct", False)
        reasoning = result.get("reasoning", "No reasoning provided")

        if is_correct:
            message = f"✓ Correct! {reasoning}"
            reward = 1.0
        else:
            message = f"✗ Incorrect. {reasoning}\n\nExpected: {expected}"
            reward = 0.0

        return {
            "correct": is_correct,
            "reward": reward,
            "reasoning": reasoning,
            "message": message,
        }
