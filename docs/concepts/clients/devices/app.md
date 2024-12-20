# AppClient

## Introduction
`AppClient` is a client tool designed for user interaction within applications.

## Initialization Parameters
- `interactor`: Optional parameter, workflow used for interaction
- `processor`: Optional parameter, workflow used for image processing
- `config_path`: Optional parameter, path to the worker configuration file
- `workers`: Optional parameter, list of Worker instances

Note:
1. Either `interactor` or `processor` must be provided
2. At least one of `config_path` or `workers` must be provided, or both can be used

## Input and Output
- Input: Uses `AppInput`
- Output: Uses `AppCallback`