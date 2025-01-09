<p align="center">
  <img src="docs/images/OmAgent-banner.png" width="400"/>
</p>

<div>
    <h1 align="center">🌟 Build Multimodal Language Agents with Ease 🌟</h1>
</div>


<p align="center">
  <a href="https://twitter.com/intent/follow?screen_name=OmAI_lab" target="_blank">
    <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/OmAI_lab">
  </a>
  <a href="https://discord.gg/G9n5tq4qfK" target="_blank">
    <img alt="Discord" src="https://img.shields.io/discord/1296666215548321822?style=flat&logo=discord">
  </a>
</p>

<p align="center">
    <a>English</a> | <a href="README_ZH.md">中文</a>
</p>

## 📖 Introduction
OmAgent is an open-source agent framework designed to streamlines the development of on-device multimodal agents. Our goal is to enable agents that can empower various hardware devices, ranging from smart phone, smart wearables (e.g. glasses), IP cameras to futuristic robots. As a result, OmAgent creates an abstraction over various types of device and simplifies the process of connecting these devices to the state-of-the-art multimodal foundation models and agent algorithms, to allow everyone build the most interesting on-device agents. Moreover, OmAgent focuses on optimize the end-to-end computing pipeline, on in order to provides the most real-time user interaction experience out of the box. 

In conclusion, key features of OmAgent include:

- **Easy Connection to Diverse Devices**: we make it really simple to connect to physical devices, e.g. phone, glasses and more, so that agent/model developers can build the applications that not running on web page, but running on devices. We welcome contribution to support more devices! 

- **Speed-optimized SOTA Mutlimodal Models**: OmAgent integrates the SOTA commercial and open-source foundation models to provide application developers the most powerful intelligence. Moreover, OmAgent streamlines the audio/video processing and computing process to easily enable natural and fluid interaction between the device and the users. 

- **SOTA Multimodal Agent Algorihtms**: OmAgent provides an easy workflow orchestration interface for researchers and developers implement the latest agent algorithms, e.g. ReAct, DnC and more. We welcome contributions of any new agent algorithm to enable more complex problem solving abilities.

- **Scalability and Flexibility**: OmAgent provides an intuitive interface for building scalable agents, enabling developers to construct agents tailored to specific roles and highly adaptive to various applications. 


## 🛠️ How To Install
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
- Other requirements
  ```bash
  cd ..
  pip install -r requirements.txt
  ```
- Set Up Conductor Server (Docker-Compose) Docker-compose includes conductor-server, Elasticsearch, and Redis.
  ```bash
  cd docker
  docker-compose up -d
  ```

- Optional: Install Milvus VectorDB for Long-Term Memory  

  ```shell
  # Download Milvus startup script
  curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
  # Start Milvus in standalone mode
  bash standalone_embed.sh start
  ```  
  You can skip this step because the system defaults to using Milvus Lite.

## 🚀 Quick Start 
### Hello World
### 1、Configuration

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

3. Update settings in the generated `container.yaml`:
      - Configure Redis connection settings, including host, port, credentials, and both `redis_stream_client` and `redis_stm_client` sections.
   - Update the Conductor server URL under conductor_config section
   - Adjust any other component settings as needed


For more information about the container.yaml configuration, please refer to the [container module](./docs/concepts/container.md)

### 2、Running the Example

1. Run the simple VQA example:

   For terminal/CLI usage: Input and output are in the terminal window
   ```bash
   cd examples/step1_simpleVQA
   python run_cli.py
   ```

   For app/GUI usage: Input and output are in the app
   ```bash
   cd examples/step1_simpleVQA
   python run_app.py
   ```
   For app backend deployment, please refer to [here](docker/README.md)  
   For the connection and usage of the OmAgent app, please check [app usage documentation](./docs/concepts/clients/app.md)

## 🏗 Architecture
The design architecture of OmAgent adheres to three fundamental principles: 
1. Graph-based workflow orchestration; 
2. Native multimodality; 
3. Device-centricity. 
With OmAgent, one has the opportunity to craft a bespoke intelligent agent program.

For a deeper comprehension of OmAgent, let us elucidate key terms:
**Devices**: Central to OmAgent's vision is the empowerment of intelligent hardware devices through artificial intelligence agents, rendering devices a pivotal component of OmAgent's essence. By leveraging the downloadable mobile application we have generously provided, your mobile device can become the inaugural foundational node linked to OmAgent. Devices serve to intake environmental stimuli, such as images and sounds, potentially offering responsive feedback. We have evolved a streamlined backend process to manage the app-centric business logic, thereby enabling developers to concentrate on constructing the intelligence agent's logical framework.

**Workflow**: Within the OmAgent Framework, the architectural structure of intelligent agents is articulated through graphs. Developers possess the liberty to innovate, configure, and sequence node functionalities at will. Presently, we have opted for Conductor-OSS as the workflow orchestration engine, lending support to intricate operations like switch-case, fork-join, and do-while.

**Task and Worker**: Throughout the OmAgent workflow development journey, Task and Worker stand as pivotal concepts. Worker embodies the actual operational logic of workflow nodes, whereas Task oversees the orchestration of the workflow's logic. Tasks are categorized into Operators, managing workflow logic (e.g., looping, branching), and Simple Tasks, representing nodes customized by developers. Each Simple Task is correlated with a Worker; when the workflow progresses to a given Simple Task, the task is dispatched to the corresponding worker for execution. 


## 📚 Examples & Tutorials
You can find the full list of examples in the [examples](./examples/) directory.

TODO: add tutorial link and brief example just like below. The format can be same as old one. 


### 🤖 Basic Principles of Building an Agent
- **Modularity**: Break down the agent's functionality into discrete workers, each responsible for a specific task.

- **Reusability**: Design workers to be reusable across different workflows and agents.

- **Scalability**: Use workflows to scale the agent's capabilities by adding more workers or adjusting the workflow sequence.

- **Interoperability**: Workers can interact with various backends, such as LLMs, databases, or APIs, allowing agents to perform complex operations.

- **Asynchronous Execution**: The workflow engine and task handler manage the execution asynchronously, enabling efficient resource utilization.


## 💻 API Documentation
The API documentation is available [here](https://om-ai-lab.github.io/OmAgentDocs/).

## 🔗 Related works
If you are intrigued by multimodal large language models, and agent technologies, we invite you to delve deeper into our research endeavors:  
🔆 [How to Evaluate the Generalization of Detection? A Benchmark for Comprehensive Open-Vocabulary Detection](https://arxiv.org/abs/2308.13177) (AAAI24)   
🏠 [GitHub Repository](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet: Large-scale vision-language multi-dataset pre-training with multimodal detection network](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268) (IET Computer Vision)  
🏠 [Github Repository](https://github.com/om-ai-lab/OmDet)

## ⭐️ Citation

If you find our repository beneficial, please cite our paper:  
```angular2
@article{zhang2024omagent,
  title={OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer},
  author={Zhang, Lu and Zhao, Tiancheng and Ying, Heting and Ma, Yibo and Lee, Kyusong},
  journal={arXiv preprint arXiv:2406.16620},
  year={2024}
}
```

## Star History
[![Star History Chart](https://api.star-history.com/svg?repos=om-ai-lab/OmAgent&type=Date)](https://star-history.com/#om-ai-lab/OmAgent&Date)







## 🗓️ Updates
* 11/12/2024: OmAgent v0.2.0 is officially released! We have completely rebuilt the underlying framework of OmAgent, making it more flexible and easy to extend. The new version added the concept of devices, making it easier to develop quickly for smart hardware.
* 10/20/2024: We are actively engaged in developing version 2.0.0 🚧 Exciting new features are underway! You are welcome to join us on X and Discord~
* 09/20/2024: Our paper has been accepted by EMNLP 2024. See you in Miami!🏝
* 07/04/2024: The OmAgent open-source project has been unveiled. 🎉
* 06/24/2024: [The OmAgent research paper has been published.](https://arxiv.org/abs/2406.16620)
