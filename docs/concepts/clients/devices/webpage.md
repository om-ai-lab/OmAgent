# WebpageClient

## Introduction
`WebpageClient` is a web-based chat interface implemented with Gradio, designed for interactive communication.

## Initialization Parameters
- `interactor`: Optional parameter, workflow used for interaction
- `processor`: Optional parameter, workflow used for image processing
- `config_path`: Optional parameter, path to the worker configuration file
- `workers`: Optional parameter, list of Worker instances

Note:
1. Either `interactor` or `processor` must be provided
2. At least one of `config_path` or `workers` must be provided, or both can be used
3. When using `interactor`:
   - Default port: **7860**
   - Access URL: `http://127.0.0.1:7860`
4. When using `processor`:
   - Default port: **7861**
   - Access URL: `http://127.0.0.1:7861`

## Input and Output
- Input: Uses `AppInput`
- Output: Uses `AppCallback`