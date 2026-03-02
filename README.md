# ProcBench

[![⭐ OpenReward Environment](https://img.shields.io/badge/%E2%AD%90%20OpenReward-Environment-f7e6cc)](https://openreward.ai/GeneralReasoning/ProcBench)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-orange)](https://huggingface.co/datasets/ifujisawa/procbench)

## Description

ProcBench is a multi-step procedural reasoning benchmark that evaluates whether language models can follow explicit step-by-step procedures to produce correct output. The benchmark covers 23 procedural task types -- including string manipulation, list operations, and arithmetic -- with 240 examples each, for a total of 5,520 tasks.

## Capabilities

- Multi-step procedural reasoning
- Instruction following
- Algorithmic execution

## Compute Requirements

No sandbox is needed. ProcBench uses standard defaults.

## License

MIT (environment) + CC-BY-4.0 (dataset).

## Tasks

There are 5,520 tasks in a single `test` split, spanning 23 procedural task types (task01 through task23) with 240 examples each. Each task provides detailed procedural instructions, an initial input state, expected intermediate states, and a final expected answer.

## Reward Structure

Binary reward: 1.0 for correct, 0.0 for incorrect. Answers are graded by an LLM (gpt-5-mini) that compares the submitted answer to the expected answer, accounting for minor formatting differences such as spacing, capitalization, and equivalent numeric representations. On grader failure, the environment falls back to exact string match.

No temperature parameter is passed to the grader.

## Data

The dataset (`procbench_data.parquet`, approximately 1.7 MB) is sourced from [HuggingFace ifujisawa/procbench](https://huggingface.co/datasets/ifujisawa/procbench) and stored on the OpenReward platform. Each record contains the fields: `prompt`, `task_name`, `example_name`, `problem_name`, `init`, `final`, and `intermediate`.

## Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `submit_answer` | `answer: str` | Submit final answer after completing all procedural steps. Ends the episode. |

## Time Horizon

Single-turn. The agent receives the procedural prompt and submits one answer.

## Environment Difficulty

Complexity increases with longer step sequences. Even strong models show significant performance drops on tasks requiring many intermediate steps.

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
