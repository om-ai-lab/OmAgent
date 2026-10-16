# Input and Callback

When writing an agent worker, you don't need to worry about which one to use. Simply call `self.input.read_input()` and `self.callback.send_xxx()`. Depending on whether `DefaultClient` or `AppClient` or `WebpageClient` is instantiated, different input and output logic will be followed.

The input has only one method:
- `read_input(workflow_instance_id: str, input_prompt = "")`
  - `workflow_instance_id` is the ID of the workflow instance.
  - `input_prompt` is the information prompting the user on what to input, which can be empty.

The callback has the following methods:
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

- `show_image(agent_id, progress, image)`
  - Displays an image in the main chat interface.
  - `agent_id` is the ID of the workflow instance.
  - `progress` is a short description of what the image represents (not displayed in the interface).
  - `image` can be any of the following formats:
    - URL string (starting with 'http://' or 'https://')
    - base64 encoded image string
    - PIL Image object (will be converted to PNG)
  - In CLI mode, this will just log a message about the image, but in WebpageClient it will display the actual image in the main chat area.

- `info_image(agent_id, progress, image)`
  - Displays an image in the info panel (right side) only.
  - `agent_id` is the ID of the workflow instance.
  - `progress` is a short description of what the image represents (shown in the info panel).
  - `image` can be any of the following formats:
    - URL string (starting with 'http://' or 'https://')
    - base64 encoded image string
    - PIL Image object (will be converted to PNG)
  - In CLI mode, this will just log a message about the image, but in WebpageClient it will display the actual image in the info panel.

- `error(agent_id, error_code, error_info, **kwargs)`
  - The required parameters for the `error` method are `agent_id`, `error_code`, and `error_info`. `agent_id` is the ID of the workflow instance, `error_code` is the error code, and `error_info` is the error information.
