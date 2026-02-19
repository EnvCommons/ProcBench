# Data Upload Requirements for ProcBench

## Overview
This environment requires the ProcBench dataset to be uploaded to OpenReward cloud storage.

## Directory Structure
```
/orwd_data/
└── procbench_data.parquet (Size: ~1.7 MB)
```

## File Description
- **procbench_data.parquet**: Complete ProcBench dataset containing 5,520 examples across 23 procedural reasoning tasks
  - 240 examples per task
  - Fields: prompt, task_name, example_name, problem_name, init, final, intermediate

## Download Instructions

You can download the dataset from HuggingFace using the following Python script:

```python
from datasets import load_dataset
import pandas as pd
import json

# Load all tasks (task01-task23)
all_data = []
for i in range(1, 24):
    task_name = f'task{i:02d}'
    print(f'Loading {task_name}...')
    ds = load_dataset('ifujisawa/procbench', task_name, split='train')
    df = ds.to_pandas()

    # Flatten the label structure
    df['init'] = df['label'].apply(lambda x: str(x['init']))
    df['final'] = df['label'].apply(lambda x: str(x['final']))
    df['intermediate'] = df['label'].apply(lambda x: json.dumps([str(v) for v in x['intermediate']]))
    df = df.drop('label', axis=1)

    all_data.append(df)

# Concatenate and save
df = pd.concat(all_data, ignore_index=True)
df.to_parquet('procbench_data.parquet')
print(f"Saved {len(df)} examples to procbench_data.parquet")
```

## Upload to OpenReward

After downloading:
1. Go to https://openreward.ai
2. Navigate to your namespace (e.g., EnvCommons)
3. Upload `procbench_data.parquet` to the root of your namespace storage
4. The file will be automatically mounted at `/orwd_data/procbench_data.parquet` when the environment runs

## Dataset Citation

If you use this dataset, please cite:

```
@misc{procbench,
  title={ProcBench: Benchmark for Multi-Step Reasoning with Procedure Cloning},
  author={Fujisawa, Ippei and others},
  year={2024},
  url={https://huggingface.co/datasets/ifujisawa/procbench}
}
```
