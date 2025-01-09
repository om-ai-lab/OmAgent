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
TODO: Add here a very simple example that

1. **Adjust Python Path**: The script modifies the Python path to ensure it can locate necessary modules. Verify the path is correct for your setup:

   ```python
    # Set current working directory path
    CURRENT_PATH = Path(__file__).parents[0]
   ```


2. **Initialize Logging**: The script sets up logging to track application events. You can adjust the logging level (`INFO`, `DEBUG`, etc.) as needed:

   ```python
   logging.init_logger("omagent", "omagent", level="INFO")
   ```

3. **Create and Execute Workflow**: The script creates a workflow and adds a task to it. It then starts the agent client to execute the workflow:

   ```python
    from examples.step1_simpleVQA.agent.simple_vqa.simple_vqa import SimpleVQA
    from examples.step1_simpleVQA.agent.input_interface.input_interface import InputIterface

    # Import registered modules
    registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))

    container.register_stm("RedisSTM")
    # Load container configuration from YAML file
    container.from_config(CURRENT_PATH.joinpath('container.yaml'))

    workflow = ConductorWorkflow(name='step1_simpleVQA')
    task1 = simple_task(task_def_name='InputIterface', task_reference_name='input_task')
    task2 = simple_task(task_def_name='SimpleVQA', task_reference_name='simple_vqa', inputs={'user_instruction': task1.output('user_instruction')})
    workflow >> task1 >> task2
    
    
    workflow.register(True)
    
    agent_client = DefaultClient(interactor=workflow, config_path='examples/step1_simpleVQA/configs', workers=[InputIterface()])
    agent_client.start_interactor()
   ```

   - **Workflow**: Defines the sequence of tasks. 'name' is the name of the workflow.
   - **Task**: Represents a unit of work, in this case, we use SimpleVQA from the examples. 'task_def_name' represents the corresponding class name, 'task_reference_name' represents the name in the conductor.
   - **DefaultClient**: Starts the agent client to execute the workflow. Here we use DefaultClient, if you want to use app client, please use AppClient.
   - **agent_client.start_interactor()**: This will start the worker corresponding to the registered task, in this case, it will start SimpleVQA and wait for the conductor's scheduling.

4. **Run Configuration**

- Connection Configuration
   - Navigate to the directory: `cd examples/step1_simpleVQA`
   - Execute `python compile_container.py` to generate configuration files needed for connection components. After execution, a `container.yaml` file will be generated.
   - Modify the `container.yaml` file to update the configurations to your actual settings.

- Agent Configuration
   - Navigate to the directory: `cd examples/step1_simpleVQA/configs/llms`
   - Modify the `gpt.yml` file to update the configurations to your actual settings.


5. **Run the Script**

Execute the script using Python:

```bash
cd examples/step1_simpleVQA
python run_cli.py
```

- Ensure all services (like Redis) are running before executing the script.

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
