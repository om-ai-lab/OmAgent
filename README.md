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
OmAgent is python library for building multimodal language agents with ease. We try to keep the library **simple** without too much overhead like other agent framework.   
 - We wrap the complex engineering (worker orchestration, task queue, node optimization, etc.) behind the scene and only leave you with a super-easy-to-use interface to define your agent.   
 - We further enable useful abstractions for reusable agent components, so you can build complex agents aggregating from those basic components.   
 - We also provides features required for multimodal agents, such as native support for VLM models, video processing, and mobile device connection to make it easy for developers and researchers building agents that can reason over not only text, but image, video and audio inputs. 

## 🔑 Key Features  
 - A flexible agent architecture that provides graph-based workflow orchestration engine and various memory type enabling contextual reasoning.  
 - native multimodal interaction support include VLM models, real-time API, computer vision models, mobile connection and etc.   
 - A suite of state-of-the-art unimodal and multimodal agent algorithms that goes beyond simple LLM reasoning, e.g. ReAct, CoT, SC-Cot etc.   


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
- Set Up Conductor Server (Docker-Compose) Docker-compose includes conductor-server, Elasticsearch, and Redis.
  ```bash
  cd docker
  docker-compose up -d
  ```

## 🚀 Quick Start 
### Configuration

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

### Run the demo

1. Run the simple VQA demo with webpage GUI:

   For WebpageClient usage: Input and output are in the webpage
   ```bash
   cd examples/step1_simpleVQA
   python run_webpage.py
   ```
   Open the webpage at `http://127.0.0.1:7860`, you will see the following interface:
   <img src="docs/images/simpleVQA_webpage.png" width="400"/>

## 🤖  Example Projects
### Video QA Agents
Build a system that can answer any questions about uploaded videos with video understanding agents. See Details [here](examples/video_understanding/README.md).  
More about the video understanding agent can be found in [paper](https://arxiv.org/abs/2406.16620).

### Mobile Personal Assistant
Build your personal mulitmodal assistant just like Google Astral in 2 minutes. See Details [here](examples/step3_outfit_with_loop/README.md).
<p >
  <img src="docs/images/readme_app.png" width="200"/>
</p>


### Agentic Operators
Compare different agent reasoning algorithms with reproducible and fair conditions. See Details [here]（docs/concepts/agent_operators.md）.

| **Rank** | **Algorithm** | **Eval Time** |  **LLM**  | **Average** | **gsm8k-score** | **gsm8k-cost($)** | **AQuA-score** | **AQuA-cost($)** |
| :------------: | :-----------------: | :-----------------: | :-------------: | :---------------: | :-------------------: | :-----------------------------------------------------------: | :---: | :----: |
|  **10**  |         IO         |      2025/1/7      |  gpt-3.5-turbo  |       38.40       |         37.83         |                            0.3328                            | 38.98 | 0.0380 |
|  **6**  |         COT         |      2025/1/7      |  gpt-3.5-turbo  |       69.86       |         78.70         |                            0.6788                            | 61.02 | 0.0957 |
|  **5**  |       SC-COT       |      2025/1/7      |  gpt-3.5-turbo  |       73.69       |         80.06         |                            5.0227                            | 67.32 | 0.6491 |
|  **9**  |         POT         |      2025/1/7      |  gpt-3.5-turbo  |       64.42       |         76.88         |                            0.6902                            | 51.97 | 0.1557 |
|  **7**  |      ReAct-Pro*      |      2025/1/7      |  gpt-3.5-turbo  |       69.74       |         74.91         |                            3.4633                            | 64.57 | 0.4928 |
|  **4**  |         IO         |      2025/1/7      | Doubao-lite-32k |       75.58       |         72.02         |                            0.0354                            | 79.13 | 0.0058 |
|  **2**  |         COT         |      2025/1/7      | Doubao-lite-32k |       85.99       |         89.31         |                            0.0557                            | 82.68 | 0.0066 |
|  **1**  |       SC-COT       |      2025/1/7      | Doubao-lite-32k |       86.05       |         88.63         |                            0.1533                            | 83.46 | 0.0409 |
|  **8**  |         POT         |      2025/1/7      | Doubao-lite-32k |       65.76       |         79.15         |                            0.0575                            | 52.36 | 0.0142 |
|  **3**  |      ReAct-Pro*      |      2025/1/7      | Doubao-lite-32k |       81.58       |         85.60         |                            0.2513                            | 77.56 | 0.0446 |

More Details in our new repo [open-agent-leaderboard](https://github.com/om-ai-lab/open-agent-leaderboard) and [Hugging Face space](https://huggingface.co/spaces/omlab/open-agent-leaderboard)


## 💻 Documentation
More detailed documentation is available [here](https://om-ai-lab.github.io/OmAgentDocs/).

## 🤝 Contributing
For more information on how to contribute, see [here](CONTRIBUTING.md).  
We value and appreciate the contributions of our community. Special thanks to our contributors for helping us improve OmAgent.

<a href="https://github.com/om-ai-lab/OmAgent/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=om-ai-lab/OmAgent" />
</a>

## 🔔 Follow us
You can follow us on [X](https://x.com/OmAI_lab) and [Discord](https://discord.gg/G9n5tq4qfK) for more updates and discussions.  

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