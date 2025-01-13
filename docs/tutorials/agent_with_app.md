# Use agent with smart phone app
## How To Install

### 1. Deploy the Workflow Orchestration Engine  
OmAgent utilizes [Conductor](https://github.com/conductor-oss/conductor) as its workflow orchestration engine. Conductor is an open-source, distributed, and scalable workflow engine that supports a variety of programming languages and frameworks. By default, it uses Redis for persistence and Elasticsearch (7.x) as the indexing backend.  
It is recommended to deploy Conductor using Docker:
```bash
docker-compose -f docker/conductor/docker-compose.yml up -d
```
- Once deployed, you can access the Conductor UI at `http://localhost:5001`. (Note: Mac system will occupy port 5000 by default, so we use 5001 here. You can specify other ports when deploying Conductor.)
- The Conductor API can be accessed via `http://localhost:8080`.
- More details about the deployment can be found [here](docker/README.md).

### 2. Install OmAgent  
- **Python Version**: Ensure Python 3.10 or higher is installed.
- **Install `omagent_core`**:
  ```bash
  pip install -e omagent-core
  ```
- **Install dependencies for the sample project**:
  ```bash
  pip install -r requirements.txt
  ```

- **Install Optional Components**: 
  - Install Milvus VectorDB for enhanced support of long-term memory.
OmAgent uses Milvus Lite as the default vector database for storing vector data related to long-term memory. To utilize the full Milvus service, you may deploy the [Milvus vector database](https://milvus.io/docs/install_standalone-docker.md) via Docker.
  - Pull git lfs files.
We provide sample image files for our examples in the `examples/step4_outfit_with_ltm/wardrobe_images` directory. To use them, ensure Git LFS is installed. You can install it with the following command:
      ```bash
      git lfs install
      ```
      Then, pull the files by executing:
      ```bash
      git lfs pull
      ```
  


### 3. Connect Devices  
If you wish to use smart devices to access your agents, we provide a smartphone app and corresponding backend, allowing you to focus on agent functionality without worrying about complex device connection issues.  
- **Deploy the app backend**   
    The APP backend comprises the backend program, along with two middleware components: the MySQL database and MinIO object storage. For installation and deployment instructions, please refer to [this link](docs/concepts/app_backend.md).
- **Download, install, and debug the smartphone app**  
  At present, we offer an Android APP available for download and testing. For detailed instructions on acquiring and using it, please refer to [here](docs/concepts/app.md). The iOS version is currently under development and will be available soon.


## Quick Start 
### 1、Configuration

The container.yaml file is a configuration file that manages dependencies and settings for different components of the system. To set up your configuration:

1. Generate the container.yaml file:
   ```bash
   cd examples/step2_outfit_with_switch
   python compile_container.py
   ```
   This will create a container.yaml file with default settings under `examples/step2_outfit_with_switch`.



2. Configure your LLM settings in `configs/llms/gpt.yml` and `configs/llms/text_res.yml`:

   - Set your OpenAI API key or compatible endpoint through environment variable or by directly modifying the yml file
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```

3. Update settings in the generated `container.yaml`:
      - Configure Redis connection settings, including host, port, credentials, and both `redis_stream_client` and `redis_stm_client` sections.
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed

4. Websearch gives multiple providers, you can choose one of them by modifying the `configs/tools/all_tools.yml` file.
   1. [**Recommend**] Use Tavily as the websearch tool, `all_tools.yml` file should be like this:
   ```yaml
   llm: ${sub|text_res}
   tools:
       - ...other tools...
       - name: TavilyWebSearch
         tavily_api_key: ${env|tavily_api_key, null}
   ```
   You can get the `tavily_api_key` from [here](https://app.tavily.com/home). It start with `tvly-xxx`. By setting the `tavily_api_key`, you can get better search results.
   2. Use bing search or duckduckgo search, `all_tools.yml` file should be like this:
   ```yaml
   llm: ${sub|text_res}
   tools:
       - ...other tools...
       - name: WebSearch
         bing_api_key: ${env|bing_api_key, null}
   ```
   For better results, it is recommended to configure [Bing Search](https://www.microsoft.com/en-us/bing/apis/pricing) setting the `bing_api_key`.

For more information about the container.yaml configuration, please refer to the [container module](./docs/concepts/container.md)

### 2、Running the Example

1. Run the outfit with switch example:

   For terminal/CLI usage: Input and output are in the terminal window
   ```bash
   cd examples/step2_outfit_with_switch
   python run_cli.py
   ```

   For app/GUI usage: Input and output are in the app
   ```bash
   cd examples/step2_outfit_with_switch
   python run_app.py
   ```
   For app backend deployment, please refer to [here](docker/README.md)  
   For the connection and usage of the OmAgent app, please check [app usage documentation](./docs/concepts/app.md)

