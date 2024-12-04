# Client

Currently, there are three clients: `DefaultClient`, `AppClient`, and `WebpageClient`.

`DefaultClient` is the default client used for interacting with users via the command line. 
- The parameters of `DefaultClient` include `interactor`, `processor`, `config_path`, `workers`, and `input_prompt`.
- Among them, either `interactor` or `processor` must be chosen to be passed in. `interactor` is the workflow used for interaction, and `processor` is the workflow used for image processing.
- At least one of `config_path` and `workers` must be passed in, or both can be passed. `config_path` is the path to the worker configuration file, and `workers` is a list of `Worker` instances.
- `input_prompt` is the prompt message for user input, which defaults to None. If you need to provide a prompt message after startup, you need to pass it in. Alternatively, you can set `input_prompt` in the `self.input.read_input()` method of your first worker node.

`AppClient` is used for interacting with users within an app.
- The parameters of `AppClient` include `interactor`, `processor`, `config_path`, and `workers`.
- Among them, either `interactor` or `processor` must be chosen to be passed in. `interactor` is the workflow used for interaction, and `processor` is the workflow used for image processing.
- At least one of `config_path` and `workers` must be passed in, or both can be passed. `config_path` is the path to the worker configuration file, and `workers` is a list of `Worker` instances.

`WebpageClient` is a web page chat window implemented with gradio, which can be used for interaction.
- The parameters of `WebpageClient` include `interactor`, `processor`, `config_path`, and `workers`.
- Among them, either `interactor` or `processor` must be chosen to be passed in.
- `interactor` is the workflow used for interaction, with a default port of **7860** after startup, and the access address is `http://127.0.0.1:7860`.
- `processor` is the workflow used for image processing, with a default port of **7861** after startup, and the access address is `http://127.0.0.1:7861`.
- At least one of `config_path` and `workers` must be passed in, or both can be passed. `config_path` is the path to the worker configuration file, and `workers` is a list of `Worker` instances.


The input for `DefaultClient` uses `AppInput`, and the output uses `DefaultCallback`. The input for `AppClient` uses `AppInput`, and the output uses `AppCallback`. The input for `WebpageClient` uses `AppInput`, and the output uses `AppCallback`.

When writing an agent worker, you don't need to worry about which one to use. Simply call `self.input.read_input()` and `self.callback.send_xxx()`. Depending on whether `DefaultClient` or `AppClient` or `WebpageClient` is instantiated, different input and output logic will be followed.

The input has only one method:
- `read_input(workflow_instance_id: str, input_prompt = "")`
  - `workflow_instance_id` is the ID of the workflow instance.
  - `input_prompt` is the information prompting the user on what to input, which can be empty.

The callback has five methods:
- `send_incomplete(agent_id, msg, took=0, msg_type=MessageType.TEXT.value, prompt_tokens=0, output_tokens=0, filter_special_symbols=True)`
- `send_block(agent_id, msg, took=0, msg_type=MessageType.TEXT.value, interaction_type=InteractionType.DEFAULT.value, prompt_tokens=0, output_tokens=0, filter_special_symbols=True)`
- `send_answer(agent_id, msg, took=0, msg_type=MessageType.TEXT.value, prompt_tokens=0, output_tokens=0, filter_special_symbols=True)`

  - `send_incomplete` (the conversation content is not yet complete), `send_block` (a single conversation has ended, but the overall result is not finished), `send_answer` (the overall return is complete).
  - The required parameters for these three methods are `agent_id` and `msg`. `agent_id` is the ID of the workflow instance, and `msg` is the message content.
  - `took`, `msg_type`, `interaction_type`, `prompt_tokens`, and `output_tokens` are optional parameters, chosen based on the actual situation.
  - `took` is the time consumed by the program, in seconds.
  - `msg_type` is the message type, with three options: `MessageType.TEXT.value`, `MessageType.IMAGE_URL.value`, `MessageType.IMAGE_BASE64.value`. The default is `MessageType.TEXT.value`.
  - `interaction_type` is the interaction type, with two options: `InteractionType.DEFAULT.value`, `InteractionType.INPUT.value`. The default is `InteractionType.DEFAULT.value`, which means doing nothing. `InteractionType.INPUT.value` means that after this message is output, user input is required.
  - `prompt_tokens` is the number of input tokens, and `output_tokens` is the number of output tokens.
  - `filter_special_symbols` is a boolean parameter, in `AppClient` it defaults to `True`, and special symbols such as `*`, `#`, `-` will be filtered out from the message content when the message type is `MessageType.TEXT.value`.
  - `send_incomplete` must be followed by a `send_block`.
  - The last message must be `send_answer`.

- `info(agent_id, progress, message)`
  - The required parameters for the `info` method are `agent_id`, `progress`, and `message`. `agent_id` is the ID of the workflow instance, `progress` is the program name, and `message` is the progress information.

- `error(agent_id, error_code, error_info, **kwargs)`
  - The required parameters for the `error` method are `agent_id`, `error_code`, and `error_info`. `agent_id` is the ID of the workflow instance, `error_code` is the error code, and `error_info` is the error information.
