# ProcBench Environment

OpenReward environment for the **ProcBench** benchmark - a multi-step procedural reasoning evaluation suite for large language models.

## Overview

ProcBench is designed to evaluate LLM capabilities in:
- **Instruction followability**: Following explicit, step-by-step procedures
- **Multi-step reasoning**: Executing sequential operations correctly
- **Procedural problem-solving**: Tasks emphasizing process adherence over implicit knowledge

The benchmark contains:
- **5,520 total examples** (240 examples per task)
- **23 distinct procedural tasks** (task01-task23)
- Examples covering various domains: string manipulation, list operations, arithmetic procedures, and more

## Task Structure

Each task provides:
- **Prompt**: Detailed procedural instructions explaining the step-by-step algorithm
- **Initial state**: Starting input for the problem
- **Expected final answer**: Target output after completing all steps
- **Intermediate states**: Expected values after each step (useful for debugging/analysis)

## Environment Details

- **Type**: Single-turn QA environment
- **Evaluation**: LLM grader (gpt-5-mini) compares answers, accounting for format variations
- **Reward**: Binary (1.0 for correct, 0.0 for incorrect)
- **Split**: "test" (all 5,520 examples)
- **API Key Required**: OpenAI API key for grading (passed via secrets)

## Tools

### `submit_answer`

Submit your final answer after following all procedural steps.

**Parameters:**
- `answer` (string): The final answer

**Evaluation:**
- Uses LLM grader (gpt-5-mini) to compare your answer with the expected answer
- Accounts for formatting differences and equivalent representations
- Provides reasoning for the grading decision

**Returns:**
- Grader feedback with reasoning
- Reward (1.0 for correct, 0.0 for incorrect)
- Metadata including task information, expected answer, and grader reasoning

## Local Development

### Prerequisites

- Python 3.11+
- OpenReward SDK
- Dataset downloaded locally (see instructions below)

### Download Dataset

```bash
# Install dependencies
pip install datasets pandas pyarrow

# Run the download script (or see DATA_UPLOAD.md for full code)
python -c "
from datasets import load_dataset
import pandas as pd
import json

all_data = []
for i in range(1, 24):
    task_name = f'task{i:02d}'
    ds = load_dataset('ifujisawa/procbench', task_name, split='train')
    df = ds.to_pandas()
    df['init'] = df['label'].apply(lambda x: str(x['init']))
    df['final'] = df['label'].apply(lambda x: str(x['final']))
    df['intermediate'] = df['label'].apply(lambda x: json.dumps([str(v) for v in x['intermediate']]))
    df = df.drop('label', axis=1)
    all_data.append(df)

df = pd.concat(all_data, ignore_index=True)
df.to_parquet('procbench_data.parquet')
print(f'Downloaded {len(df)} examples')
"
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Local Server

```bash
python server.py
```

The server will start on `http://0.0.0.0:8000`

### Test with Sample Agent

```bash
export OPENAI_API_KEY=your_key_here
export MODEL_NAME=gpt-4  # optional
python sample_agent.py
```

## Docker Testing

### Build Image

```bash
docker build -t procbench:test .
```

### Run Container

```bash
docker run -p 8000:8000 procbench:test
```

### Test Endpoints

```bash
# List splits
curl http://localhost:8000/list_splits

# List tasks
curl http://localhost:8000/list_tasks?split=test

# List tools
curl http://localhost:8000/list_tools?format=openai
```

## Production Deployment

### 1. Upload Dataset

Follow instructions in [DATA_UPLOAD.md](DATA_UPLOAD.md) to upload the dataset to your OpenReward namespace storage.

### 2. Deploy to OpenReward

1. Push this repository to GitHub under `EnvCommons/procbench`
2. Go to https://openreward.ai/environments/new
3. Connect the GitHub repository
4. Set namespace to `EnvCommons/procbench`
5. Deploy

### 3. Verify Deployment

```python
from openreward import AsyncOpenReward

or_client = AsyncOpenReward()
environment = or_client.environments.get(name="EnvCommons/procbench")
tasks = await environment.list_tasks(split="test")
print(f"Environment deployed with {len(tasks)} tasks")
```

## Example Usage

```python
import asyncio
from openreward import AsyncOpenReward
from openai import AsyncOpenAI

async def run_task():
    # Initialize clients
    or_client = AsyncOpenReward()
    oai_client = AsyncOpenAI(api_key="your-key")

    # Get environment and tasks
    environment = or_client.environments.get(name="EnvCommons/procbench")
    tasks = await environment.list_tasks(split="test")
    tools = await environment.list_tools(format="openai")

    # Run a task
    task = tasks[0]
    async with environment.session(
        task=task,
        secrets={"openai_api_key": "your-openai-key"}
    ) as session:
        prompt = await session.get_prompt()

        # Agent reasoning loop
        response = await oai_client.responses.create(
            model="gpt-4",
            tools=tools,
            input=[{"role": "user", "content": prompt[0].text}]
        )

        # Submit answer
        for item in response.output:
            if item.type == "function_call":
                result = await session.call_tool(
                    item.name,
                    {"answer": "your_answer"}
                )
                print(f"Reward: {result.reward}")

asyncio.run(run_task())
```

## Example Task

```
Task: task01 (String Sorting Algorithm)

Prompt:
"Sort a given string into alphabetical order step by step by swapping two characters.
Starting with the first alphabet in alphabetical order 'a' and the first position
of the string, repeat the following process until the end of the alphabetical order 'z'.
1. Search the string from left to right for the character.
2. If the character is found, swap it with the character at the current position and
   move to the next position. If not found, stay at the same position and proceed
   to the next character in alphabetical order."

Input: "itstb"
Expected Output: "bistt"
Intermediate: ["btsti"]
```

## File Structure

```
procbench/
├── procbench.py              # Main environment class
├── server.py                 # Server wrapper
├── sample_agent.py           # OpenAI test agent
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container configuration
├── DATA_UPLOAD.md            # Data upload instructions
├── README.md                 # This file
├── .gitignore                # Git ignore rules
└── procbench_data.parquet    # Dataset (local dev only, not in git)
```

## Citation

If you use the ProcBench dataset, please cite:

```bibtex
@misc{procbench,
  title={ProcBench: Benchmark for Multi-Step Reasoning with Procedure Cloning},
  author={Fujisawa, Ippei and others},
  year={2024},
  url={https://huggingface.co/datasets/ifujisawa/procbench}
}
```

## License

This environment implementation is provided under the MIT License.
The ProcBench dataset is licensed under CC-BY-4.0.

## Support

For issues or questions:
- Environment issues: Open an issue on this repository
- Dataset questions: See https://huggingface.co/datasets/ifujisawa/procbench
- OpenReward platform: https://openreward.ai
