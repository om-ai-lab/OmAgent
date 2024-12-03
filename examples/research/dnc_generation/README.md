# Control Large Language Models via Divide and Conquer
## Introduction
This project implements the Divide-and-Conquer (DnC) text generation method described in the paper ["Control Large Language Models via Divide and Conquer"](https://arxiv.org/abs/2410.04628) by Li, Bingxuan, et al., in the OmAgent framework. 

## Overview
The DnCGeneration worker iteratively generates text that satisfies specified constraints (keywords). If any constraints are not met in the initial generation, the process continues by focusing on the unmet constraints and merging the results until all constraints are satisfied or the maximum iterations (k) are reached. 


## Running the Example
For terminal/CLI usage: Input and output are in the terminal window
```
cd examples/research/dnc_generation
python run_cli.py
```

An example input and output.
```
Input: "Ben Smith, 29-year-old"
Output: 
{
  "final_response": "Ben Smith, a 29-year-old entrepreneur known for his innovative contributions to the tech industry, recently celebrated his birthday with friends in Seattle while making waves with his startup.",
  "record": [
    {
      "rest_set": ["29-year-old"],
      "old_response": "Ben Smith is an entrepreneur.",
      "new_response": "He is a 29-year-old making waves in tech.",
      "merged_response": "Ben Smith, a 29-year-old entrepreneur making waves in tech."
    }
  ],
  "success": true
}
```

## Citation
```angular2
@article{li2024control,
  title={Control Large Language Models via Divide and Conquer},
  author={Li, Bingxuan and Wang, Yiwei and Meng, Tao and Chang, Kai-Wei and Peng, Nanyun},
  journal={arXiv preprint arXiv:2410.04628},
  year={2024}
}
```


