# Run the full version of OmAgent
OmAgent now supports free switching between Full and Lite versions, the differences between the two versions are as follows:
- The Full version has better concurrency performance, can view workflows as well as run logs with the help of the orchestration system GUI, and supports more device types (e.g. smartphone apps). Note that running the Full version requires a Docker deployment middleware dependencies.
- The Lite version is suitable for developers who want to get started faster. It eliminates the steps of installing and deploying Docker, and is suitable for rapid prototyping and debugging.

## Instruction of how to use Full version
### 🛠️ How To Install
- python >= 3.10
- Install omagent_core  
  Use pip to install omagent_core latest release.
  ```bash
  pip install omagent-core
  ```
  Or install the latest version from the source code like below.
  ```bash
  pip install -e omagent-core
  ```
- Set Up Conductor Server (Docker-Compose) Docker-compose includes conductor-server, Elasticsearch, and Redis.
  ```bash
  cd docker
  docker-compose up -d
  ```

### 🚀 Quick Start 
#### Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   cd examples/step1_simpleVQA
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/step1_simpleVQA`.



2. Configure your LLM settings in `configs/llms/gpt.yml`:

   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```
   You can use a locally deployed Ollama to call your own language model. The tutorial is [here](docs/concepts/models/Ollama.md).

3. Update settings in the generated `container.yaml`:
      - Configure Redis connection settings, including host, port, credentials, and both `redis_stream_client` and `redis_stm_client` sections.
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed


For more information about the container.yaml configuration, please refer to the [container module](./docs/concepts/container.md)

#### Run the demo

1. Set the OmAgent to Full version by setting environment variable `OMAGENT_MODE`
   ```bash
   export OMAGENT_MODE=full
   ```
   or
   ```pyhton
   os.environ["OMAGENT_MODE"] = "full"
   ```
2. Run the simple VQA demo with webpage GUI:

   For WebpageClient usage: Input and output are in the webpage
   ```bash
   cd examples/step1_simpleVQA
   python run_webpage.py
   ```
   Open the webpage at `http://127.0.0.1:7860`, you will see the following interface:  
   <img src="docs/images/simpleVQA_webpage.png" width="400"/>