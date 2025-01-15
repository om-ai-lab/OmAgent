# DefaultClient

## Introduction
`DefaultClient` is the default client used for interacting with users via the command line.

## Initialization Parameters
- `interactor`: Optional parameter, workflow used for interaction
- `processor`: Optional parameter, workflow used for image processing
- `config_path`: Optional parameter, path to the worker configuration file
- `workers`: Optional parameter, list of Worker instances
- `input_prompt`: Optional parameter, prompt message for user input (defaults to None)

Note:
1. Either `interactor` or `processor` must be provided
2. At least one of `config_path` or `workers` must be provided, or both can be used
3. If you need a prompt message after startup, you can either:
   - Pass it through the `input_prompt` parameter
   - Set it in the `self.input.read_input()` method of your first worker node

## Input and Output
- Input: Uses `AppInput`
- Output: Uses `DefaultCallback`