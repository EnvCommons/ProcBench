"""
Sample agent for testing ProcBench environment with OpenAI's Responses API.

Usage:
    export OPENAI_API_KEY=your_key_here
    export MODEL_NAME=gpt-4  # optional, defaults to gpt-4
    python sample_agent.py
"""

import asyncio
import json
import os

from openai import AsyncOpenAI
from openreward import AsyncOpenReward

# Configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-5.2")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")


async def main() -> None:
    """Run a sample agent on a ProcBench task."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable must be set")

    # Initialize clients
    or_client = AsyncOpenReward()
    oai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    # Connect to environment
    environment = or_client.environments.get(
        name="local/ProcBench",
        base_url=BASE_URL
    )

    # Get tasks and tools
    tasks = await environment.list_tasks(split="test")
    tools = await environment.list_tools(format="openai")

    print(f"Loaded {len(tasks)} tasks from ProcBench")
    print(f"Number of available tools: {len(tools)}")

    # Run on first task (you can change this)
    task = tasks[600]
    print(f"\nRunning on first task...")

    async with environment.session(
        task=task,
        secrets={"openai_api_key": OPENAI_API_KEY}
    ) as session:
        # Get the initial prompt
        prompt = await session.get_prompt()
        prompt_text = prompt if isinstance(prompt, str) else prompt[0].text

        print(f"\nPrompt: {prompt_text}...")

        # Initialize conversation
        input_list = [{"role": "user", "content": prompt_text}]
        finished = False
        turn = 0

        # Agent loop
        while not finished:
            turn += 1
            print(f"\n--- Turn {turn} ---")

            # Call model
            response = await oai_client.responses.create(
                model=MODEL_NAME,
                tools=tools,
                reasoning={"effort": "high"},
                input=input_list,
            )

            # Process response
            tool_called = False
            for item in response.output:
                if item.type == "function_call":
                    tool_called = True
                    print(f"Tool call: {item.name}")
                    print(f"Arguments: {item.arguments}")

                    # Execute tool
                    tool_result = await session.call_tool(
                        item.name,
                        json.loads(str(item.arguments)),
                    )

                    finished = tool_result.finished
                    print(f"Result: {tool_result.blocks[0].text if tool_result.blocks else 'No text'}")
                    print(f"Reward: {tool_result.reward}")
                    print(f"Finished: {finished}")

                    # Add tool result to conversation history (Responses API format)
                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps({
                            "result": tool_result.blocks[0].text if tool_result.blocks else ""
                        })
                    })

                elif item.type == "text":
                    print(f"Model response: {item.text[:200]}...")

            # If no tool was called, we're done
            if not tool_called:
                print("No tool call made, ending episode")
                break

            # Safety: max 10 turns
            if turn >= 10:
                print("Max turns reached, ending episode")
                break

    print("\n=== Episode Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
