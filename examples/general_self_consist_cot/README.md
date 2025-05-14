# SELF-CONSISTENCY IMPROVES CHAIN OF THOUGHT REASONING IN LANGUAGE MODELS

## Overview

This example contains code to implement the self-consistency COT in the paper [SELF-CONSISTENCY IMPROVES CHAIN OF THOUGHT REASONING IN LANGUAGE MODELS](https://arxiv.org/pdf/2203.11171) by Wang, et al. 
Please note:
The algorithm in original paper is designed only for math reasoning, the implementation here is for general reasoning.

## Running the Example

You can run the example in two modes:

### Lite Mode (Local Execution)
Set the environment variable before running:
```bash
export OMAGENT_MODE="lite"
```
This mode runs the workflow locally without requiring a Conductor server.

### Conductor Mode (Distributed Execution)
Set the environment variable (or don't set it, as this is the default):
```bash
export OMAGENT_MODE="conductor"  # or just don't set OMAGENT_MODE
```
This mode requires a running Conductor server for workflow orchestration.

For terminal/CLI usage: Input and output are in the terminal window

```bash
cd examples/self_consist_cot
python run_cli.py
```

An example input and output(by GPT-4o-mini).

```
> Input: Which is bigger, 9.9 or 9.11?
> Reasoning paths: ["9.9 is bigger than 9.11.", "9.9 is bigger than 9.11.", "9.9 is bigger than 9.11."] 

> Final answer: 9.9 is bigger than 9.11.
```

## Citation
```
@inproceedings{DBLP:conf/iclr/0002WSLCNCZ23,
  author       = {Xuezhi Wang and
                  Jason Wei and
                  Dale Schuurmans and
                  Quoc V. Le and
                  Ed H. Chi and
                  Sharan Narang and
                  Aakanksha Chowdhery and
                  Denny Zhou},
  title        = {Self-Consistency Improves Chain of Thought Reasoning in Language Models},
  booktitle    = {{ICLR}},
  publisher    = {OpenReview.net},
  year         = {2023}
}
```