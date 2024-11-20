<div>
    <h1> <img src="docs/images/logo.png" height=30 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/intro.png" width="600"/>
</p>

<p align="center">
  <a href="https://twitter.com/intent/follow?screen_name=OmAI_lab" target="_blank">
    <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/OmAI_lab">
  </a>
  <a href="https://discord.gg/Mkqs8z5U" target="_blank">
    <img alt="Discord" src="https://img.shields.io/discord/1296666215548321822?style=flat&logo=discord">
  </a>
</p>

<p align="center">
    <a href="README.md">English</a> | <a>中文</a>
</p>


## 🗓️ 更新
* 11/12/2024: OmAgent v0.2.0 正式发布！我们完全重构了OmAgent的底层框架，使其更加灵活和易于扩展。新版本加入了设备的概念，使你可以更简单的面向智能硬件进行快速开发~
* 10/20/2024: 我们正在积极开发版本0.2.0 🚧 激动人心的新功能正在路上！欢迎在X和Discord上加入我们~
* 09/20/2024: 我们的论文已经被 EMNLP 2024 收录。 迈阿密见！🏝
* 07/04/2024: OmAgent开源项目发布 🎉
* 06/24/2024: [OmAgent论文发布](https://arxiv.org/abs/2406.16620)


## 📖 介绍
OmAgent 是一个开源的智能体框架，旨在简化设备上多模态智能体的开发。我们的目标是使智能体能够增强各种硬件设备的功能，从智能手机、智能可穿戴设备（如眼镜）、IP 摄像头到未来的机器人。因此，OmAgent 对各种类型的设备进行抽象，并简化了将这些设备连接到最先进的多模态基础模型和智能体算法的过程，以便每个人都能构建最有趣的设备上智能体。此外，OmAgent 专注于优化端到端计算管道，以提供开箱即用的实时用户交互体验。

总之，OmAgent 的关键特性包括：

- **轻松连接多样化设备**：我们使连接物理设备变得非常简单，例如手机、眼镜等，以便智能体/模型开发者可以构建不仅在网页上运行而是在设备上运行的应用程序。我们欢迎对更多设备的支持贡献！

- **速度优化的最先进多模态模型**：OmAgent 集成了最先进的商业和开源基础模型，为应用开发者提供最强大的智能。此外，OmAgent 简化了音频/视频处理和计算过程，轻松实现设备与用户之间自然流畅的交互。

- **最先进的多模态智能体算法**：OmAgent 为研究人员和开发者提供了一个简单的工作流编排接口，以实现最新的智能体算法，例如 ReAct、DnC 等。我们欢迎任何新智能体算法的贡献，以实现更复杂的问题解决能力。

- **可扩展性和灵活性**：OmAgent 提供了一个直观的界面，用于构建可扩展的智能体，使开发者能够构建适合特定角色并高度适应各种应用的智能体。

## 🛠️ 如何安装
### 1. 部署工作流编排引擎  
OmAgent 使用 [Conductor](https://github.com/conductor-oss/conductor) 作为工作流编排引擎。Conductor 是一个开源的、分布式的、可扩展的工作流引擎，支持多种编程语言和框架。它默认使用 Redis 进行持久化，Elasticsearch(7.x) 作为索引后端。  
推荐使用docker部署Conductor：
```bash
docker compose -f docker/conductor/docker-compose.yml up -d
```
- 部署完成后可以通过访问 `http://localhost:5001` 访问Conductor UI。（注：Mac系统默认会占用5000端口，因此我们使用5001端口，你可以在部署Conductor的时候指定其它端口。）
- 通过 `http://localhost:8080` 调用Conductor API。
- 更多部署细节请参考 [这里](docker/README.md)

### 2. 安装OmAgent  
- **Python 版本**: 确保已安装 Python 3.10 或更高版本。
- **安装 `omagent_core`**:
  ```bash
  pip install -e omagent-core
  ```
- **安装示例项目所需的依赖**:
  ```bash
  pip install -r requirements.txt
  ```

- **安装可选组件**: 
  - 安装 Milvus VectorDB 以更好支持长期记忆
  OmAgent默认使用Milvus Lite作为智能体长期记忆的向量数据库存储向量数据。如果你希望使用完整的Milvus服务，可以使用docker部署[milvus向量数据库](https://milvus.io/docs/install_standalone-docker.md)。

### 3. 连接设备  
如果你希望使用智能设备来访问你的智能体，我们提供了智能手机APP以及对应的后端程序，这样你可以专注于实现智能体功能，而无需担心复杂的设备连接问题。  
- APP后端部署  
  APP后端包含后端程序以及Mysql数据库和minio对象存储两个中间件。安装部署方法请参考[这里](docs/concepts/app_backend.md)。
- 手机APP下载安装以及调试  
  当前我们提供了Android APP供大家下载测试，具体的获取和使用方法请参考[这里](docs/concepts/app.md)。IOS版本正在开发中， 很快会和大家见面。

## 🚀 快速开始 
### Hello World
### 1、配置

`container.yaml` 文件是一个管理系统中不同组件的依赖和设置的配置文件。按以下步骤设置您的配置：

1. 生成 `container.yaml` 文件：
   ```bash
   cd examples/step2_outfit_with_switch
   python compile_container.py
   ```
   这将在 `examples/step2_outfit_with_switch` 下创建一个具有默认设置的 `container.yaml` 文件。

2. 在 `configs/llms/gpt.yml` 和 `configs/llms/text_res.yml` 中配置您的 LLM 设置：

   - 通过环境变量或直接修改 yml 文件来设置您的 OpenAI API 密钥或兼容的 endpoint
   ```bash
   export custom_openai_key="your_openai_api_key"
   export custom_openai_endpoint="your_openai_endpoint"
   ```

3. 更新生成的 `container.yaml` 中的设置：
   - 配置 Redis 连接设置，主要是主机地址、端口、密码凭证，包括 `redis_stream_client` 和 `redis_stm_client` 部分都要进行设置。
   - 在 `conductor_config` 下更新 Conductor 服务器的 URL
   - 根据需要调整其他组件设置

4. websearch 默认使用的是 duckduckgo，如果要更好的效果建议配置[bing搜索](https://www.microsoft.com/en-us/bing/apis/pricing)，修改 `configs/tools/websearch.yml` 文件，设置 `bing_api_key`。

有关 `container.yaml` 配置的更多信息，请参阅 [container 模块](./docs/concepts/container.md)

### 2、运行示例

1. 运行 outfit with switch 示例：

   对于终端/CLI 使用：输入和输出在终端窗口中
   ```bash
   cd examples/step2_outfit_with_switch
   python run_cli.py
   ```

   对于app/GUI 使用：输入和输出在应用程序中
   ```bash
   cd examples/step2_outfit_with_switch
   python run_app.py
   ```
   部署app后端服务请参考 [这里](docker/README.md)  
   OmAgent 的 app 的连接和使用方式请参考 [app使用文档](./docs/concepts/app.md)

## 🏗 架构
OmAgent的设计架构遵循三项基本原则：  
1. 基于图的工作流编排；  
2. 本地多模态；  
3. 设备中心化。  
通过OmAgent，您有机会打造一个定制的智能智能体程序。  

为了更深入地理解OmAgent，让我们阐明一些关键术语： 

<p align="center">
  <img src="docs/images/architecture.jpg" width="700"/>
</p>  


**Devices**：OmAgent愿景的核心是通过人工智能智能体赋予智能硬件设备力量，使设备成为OmAgent本质的关键组成部分。通过我们慷慨提供的可下载移动应用程序，您的移动设备可以成为连接到OmAgent的首个基础节点。设备用于接收环境刺激，如图像和声音，可能提供响应性反馈。我们已经发展了一个简化的后端流程来管理应用中心的业务逻辑，从而使开发人员能够集中精力构建智能智能体的逻辑框架。  

**Workflow**：在OmAgent框架中，智能智能体的架构结构通过图形进行表达。开发人员可以自由创新、配置和序列化节点功能。目前，我们选择了Conductor作为工作流编排引擎，支持诸如switch-case、fork-join和do-while等复杂操作。  

**Task and Worker**：在整个OmAgent工作流开发过程中，Task 和 Worker 是至关重要的概念。Worker 体现了工作流节点的实际操作逻辑，而 Task 负责编排工作流的逻辑。Task分为Operator，用于管理工作流逻辑（例如循环、分支）和 SimpleTask，代表由开发人员定制的节点。每个SimpleTask与一个Worker相关联；当工作流进展到特定的SimpleTask时，任务将被分派给相应的Worker进行执行。

### 构建智能体程序的基本原则
- **模块化**：将智能体程序的功能拆分为独立的工作者，每个工作者负责一个特定的任务。

- **可重用性**：设计工作者以便在不同的工作流程和智能体程序中可重用。

- **可扩展性**：通过添加更多工作者或调整工作流程顺序，利用工作流程来扩展智能体程序的功能。

- **互操作性**：工作者可以与各种后端进行交互，如LLMs、数据库或API，从而使智能体程序能够执行复杂操作。

- **异步执行**：工作流引擎和任务处理程序异步管理执行，实现资源的高效利用。

### 示例项目

我们提供了一些示例项目来展示如何使用OmAgent构建智能智能体程序。您可以在 [examples](./examples/) 目录中找到完整的示例列表。以下是参考顺序：
1. [step1_simpleVQA](./examples/step1_simpleVQA) 展示了如何使用OmAgent构建一个简单的多模态VQA智能体。[文档](docs/examples/simple_qa.md)  
2. [step2_outfit_with_switch](./examples/step2_outfit_with_switch) 展示了如何使用OmAgent构建一个带有switch-case分支的智能体。[文档](docs/examples/outfit_with_switch.md)  
3. [step3_outfit_with_loop](./examples/step3_outfit_with_loop) 展示了如何使用OmAgent构建一个带有循环的智能体。[文档](docs/examples/outfit_with_loop.md)  
4. [step4_outfit_with_ltm](./examples/step4_outfit_with_ltm) 展示了如何使用OmAgent构建一个带有长期记忆的智能体。[文档](docs/examples/outfit_with_ltm.md)  
5. [dnc_loop](./examples/dnc_loop) 展示了如何使用OmAgent构建一个使用DnC算法的智能体，用于解决通用性的复杂问题。[文档](docs/examples/dnc_loop.md)  
6. [video_understanding](./examples/video_understanding) 展示了如何使用OmAgent构建一个视频理解智能体，用于理解视频内容。[文档](docs/examples/video_understanding.md)  


## API 文档
完整的API文档请访问 [这里](https://om-ai-lab.github.io/OmAgentDocs/).

## 🔗 相关工作
如果您对多模态算法，大语言模型以及智能体技术感兴趣，欢迎进一步了解我们的研究工作：

🔆 [How to Evaluate the Generalization of Detection? A Benchmark for Comprehensive Open-Vocabulary Detection](https://arxiv.org/abs/2308.13177)(AAAI24)   
🏠 [Github Repository](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet: Large-scale vision-language multi-dataset pre-training with multimodal detection network](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268)(IET Computer Vision)  
🏠 [Github Repository](https://github.com/om-ai-lab/OmDet)

## ⭐️ 引用

如果您发现我们的仓库对您有帮助，请引用我们的论文：
```angular2
@article{zhang2024omagent,
  title={OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer},
  author={Zhang, Lu and Zhao, Tiancheng and Ying, Heting and Ma, Yibo and Lee, Kyusong},
  journal={arXiv preprint arXiv:2406.16620},
  year={2024}
}
```

## 第三方依赖

本项目包含以下第三方项目的代码：

- **conductor-python**  
  - 许可证: Apache License 2.0
  - [项目链接](https://github.com/conductor-sdk/conductor-python)
  - [许可证链接](http://www.apache.org/licenses/LICENSE-2.0)


## Star History
[![Star History Chart](https://api.star-history.com/svg?repos=om-ai-lab/OmAgent&type=Date)](https://star-history.com/#om-ai-lab/OmAgent&Date)