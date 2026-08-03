# ProcBench

[![⭐ OpenReward Environment](https://img.shields.io/badge/%E2%AD%90%20OpenReward-Environment-f7e6cc)](https://openreward.ai/GeneralReasoning/ProcBench) [![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-orange)](https://huggingface.co/datasets/ifujisawa/procbench)

## Description

ProcBench is a multi-step procedural reasoning benchmark that evaluates whether language models can follow explicit step-by-step procedures to produce correct output. The benchmark covers 23 procedural task types -- including string manipulation, list operations, and arithmetic -- with 240 examples each, for a total of 5,520 tasks.

## Capabilities

- Multi-step procedural reasoning
- Instruction following
- Algorithmic execution

## Compute Requirements

No sandbox is needed. ProcBench uses standard defaults.

## License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

## Tasks

There are 5,520 tasks in a single `test` split, spanning 23 procedural task types (task01 through task23) with 240 examples each. Each task provides detailed procedural instructions, an initial input state, expected intermediate states, and a final expected answer.

## Reward Structure

Binary reward: 1.0 for correct, 0.0 for incorrect. Answers are graded by an LLM (gpt-5-mini) that compares the submitted answer to the expected answer, accounting for minor formatting differences such as spacing, capitalization, and equivalent numeric representations. The grader call is retried up to `N_OPENAI_COMPLETIONS` times (default 3, overridable by environment variable); if every attempt fails the environment raises rather than returning a reward, so a couldn't-grade infrastructure failure is never recorded as a wrong answer.

No temperature parameter is passed to the grader.

## Data

The dataset (`procbench_data.parquet`, approximately 1.7 MB) is sourced from [HuggingFace ifujisawa/procbench](https://huggingface.co/datasets/ifujisawa/procbench) and stored on the OpenReward platform. Each record contains the fields: `prompt`, `task_name`, `example_name`, `problem_name`, `init`, `final`, and `intermediate`.

## Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `submit_answer` | `answer: str` | Submit final answer after completing all procedural steps. Ends the episode. |

## Time Horizon

Single-turn. The agent receives the procedural prompt and submits one answer for a total of one tool call.

## Environment Difficulty

The original paper evaluates frontier models on ProcBench (Prefix Accuracy / Sequential Match):

| Model | PA | SM |
|-------|-----|-----|
| o1-preview | 69.8% | 49.6% |
| o1-mini | 64.1% | 43.2% |
| GPT-4o | 44.3% | 27.8% |
| Claude-3.5-Sonnet | 37.8% | 23.0% |
| Mistral-Large | 36.2% | 22.9% |
| GPT-4o-mini | 23.0% | 9.3% |
| Gemini-1.5-Pro | 22.4% | 11.0% |

Performance degrades significantly with task complexity. On longer tasks (17-25 steps), even o1-preview drops to 59.9% PA.

## Other Environment Requirements

Requires an `openai_api_key` secret for gpt-5-mini answer evaluation.

## Safety

No safety concerns. The agent processes algorithmic instructions and text. There is no access to external systems, sandboxes, or sensitive data.

## Citations

```bibtex
@misc{fujisawa2024procbench,
  title={ProcBench: Benchmark for Multi-Step Reasoning and Following Procedure},
  author={Ippei Fujisawa and Sensho Nobe and Hiroki Seto and Rina Onda and Yoshiaki Uchida and Hiroki Ikoma and Pei-Chun Chien and Ryota Kanai},
  year={2024},
  eprint={2410.03117},
  archivePrefix={arXiv},
  primaryClass={cs.AI}
}
```
