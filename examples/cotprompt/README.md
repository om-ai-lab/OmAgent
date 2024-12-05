# Chain-of-Thought Prompting Elicits Reasoning in Large Language Models

## Overview

This example contains code to implement the basic COT in the paper [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903) by Wei, et al. 

## Running the Example

For terminal/CLI usage: Input and output are in the terminal window

```bash
cd examples/cotprompt
python run_cli.py
```

An example input and output(by GPT-4o-mini).

```
> Input: Which is bigger, 9.9 or 9.11?
> Reasoning output: 

1. **Analyze the Question**: The question asks which of the two numbers, 9.9 or 9.11, is larger. To answer this, we must understand the place values and numerical representation of both numbers.

2. **Consider the Values**: 9.9 can be broken down into 9 plus 0.9, while 9.11 can be broken down into 9 plus 0.11. This shows that both numbers start with the same whole number part (9).

3. **Compare the Decimal Parts**: We need to compare the decimal portions: 0.9 and 0.11. The number 0.9 can also be expressed as 0.90 for comparison purposes, thus making it easier to analyze alongside 0.11.

4. **Evaluate the Decimal Comparison**: Now we compare the decimals: 0.90 (equivalent to 0.9) and 0.11. Here, we observe that 0.90 is greater than 0.11 because in the tenths place, 0.90 has a 9 compared to 0.11’s 1, which indicates a larger value.

5. **Conclude Comparison Process**: Since both numbers share the same whole number part of 9, the larger value will depend solely on the larger decimal part, which we have determined through comparison.

At this point, we have thoroughly analyzed the components of each number and identified that the key to determining which is larger lies in the comparison of their decimal parts.

>Final answer: 9.9 is bigger than 9.11.
```

## Citation
```
@article{wei2022chain,
  title={Chain-of-thought prompting elicits reasoning in large language models},
  author={Wei, Jason and Wang, Xuezhi and Schuurmans, Dale and Bosma, Maarten and Xia, Fei and Chi, Ed and Le, Quoc V and Zhou, Denny and others},
  journal={Advances in neural information processing systems},
  volume={35},
  pages={24824--24837},
  year={2022}
}
```