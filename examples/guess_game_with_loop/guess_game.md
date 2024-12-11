# Guessing Game with Loop Example

This example demonstrates how to use the framework for a guessing game with loop functionality. The example code can be found in the `examples/guess_game_with_loop` directory.
```bash
   cd examples/guess_game_with_loop
```

## Overview

This example implements an interactive guessing person game workflow that uses a loop-based approach to refine guesses based on user feedback. The workflow consists of the following key components:

1. **Initial Person Input**
   - Input: Handles the input and processing of the initial guess
   - Serves as the starting point for the guessing process

2. **Interactive QA Loop**
   - GuessQA: Conducts an interactive Q&A session to gather feedback on the guess
   - GuessDecider: Evaluates if the correct person has been guessed based on:
     - User feedback
   - Uses DoWhileTask to continue the loop until the correct person is guessed
   - Loop terminates when GuessDecider returns decision=true

3. **Final Outcome**
   - GuessOutcome: Displays the final outcome based on:
     - The correct person guessed
     - Information collected during the Q&A loop

4. **Workflow Flow**
   ```
   Start -> GuessQA Loop (QA + WebSearch + Decision) -> Final Outcome -> End
   ```

The workflow leverages Redis for state management and the Conductor server for workflow orchestration. This architecture enables:
- Interactive guessing person game
- Feedback-based refinement through structured Q&A
- Persistent state management across the workflow

## Prerequisites

- Python 3.10+
- Required packages installed (see requirements.txt)
- Redis server running locally or remotely
- Conductor server running locally or remotely

## Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system, including Conductor connections, Redis connections, and other service configurations. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/guess_game_with_loop`.

2. Update settings in the generated `container.yaml`:
   - Modify Redis connection settings:
     - Set the host, port and credentials for your Redis instance
     - Configure both `redis_stream_client` and `redis_stm_client` sections
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

## Running the Example

1. Run the guessing person game workflow:

   For terminal/CLI usage:
   ```bash
   python run_cli.py
   ```

   For app/GUI usage:
   ```bash
   python run_app.py
   ```

## Troubleshooting

If you encounter issues:
- Verify Redis is running and accessible
- Ensure all dependencies are installed correctly
- Review logs for any error messages
- Confirm Conductor server is running and accessible
- Check Redis Stream client and Redis STM client configuration

## Building the Example

Coming soon! This section will provide detailed instructions for building the guess_game_with_loop example step by step.