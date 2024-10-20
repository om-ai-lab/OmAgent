<div>
    <h1> <img src="docs/images/logo.png" height=33 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/icon.png" width="300"/>
</p>

<p align="center">
  <a href="https://twitter.com/intent/follow?screen_name=OmAI_lab" target="_blank">
    <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/OmAI_lab">
  </a>
  <a href="https://discord.gg/9JfTJ7bk" target="_blank">
    <img alt="Discord" src="https://img.shields.io/discord/1296666215548321822?style=flat&logo=discord">
  </a>
</p>

<p align="center">
    <a href="README.md">English</a> | <a>中文</a> | <a href="README_JP.md">日本語</a> | <a href="README_FR.md">Français</a>
</p>

## 🗓️ 更新日志
* 2024/10/20：我们正在积极开发2.0.0版本 🚧 令人兴奋的新功能正在开发中！欢迎在X和Discord上加入我们~
* 2024/09/20：我们的论文已被EMNLP 2024接收。迈阿密见！🏝
* 2024/07/04：OmAgent开源项目正式发布 🎉
* 2024/06/24：[OmAgent研究论文已发表](https://arxiv.org/abs/2406.16620)

## 📖 简介
OmAgent是一个先进的多模态智能代理系统，致力于利用多模态大语言模型和其他多模态算法来完成有趣的任务。OmAgent项目包含一个轻量级智能代理框架omagent_core，专门设计用于解决多模态挑战。基于此框架，我们构建了一个复杂的长视频理解系统——OmAgent。当然，您也可以使用它来实现任何您的创新想法。

OmAgent包含三个核心组件：
- **Video2RAG**：该组件的核心理念是将长视频的理解转化为多模态RAG任务。这种方法的优点是突破了视频长度的限制；但缺点是这种预处理可能会导致大量视频细节的丢失。
- **DnCLoop**：受经典分治算法范式的启发，我们设计了一个递归的通用任务处理逻辑。该方法通过迭代将复杂问题细化为任务树，最终将复杂任务转化为一系列可解决的简单任务。
- **Rewinder工具**：为了解决Video2RAG过程中的信息损失问题，我们设计了一个名为Rewinder的"进度条"工具，可以被代理自主使用。这使得代理能够重新访问任何视频细节，从而获取必要的信息。

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

更多详细信息，请查看我们的论文：**[OmAgent: 基于任务分治的复杂视频理解多模态代理框架](https://arxiv.org/abs/2406.16620)**

## 🛠️ 安装方法
- python >= 3.10
- 安装omagent_core
  ```bash
  cd omagent-core
  pip install -e .
  ```
- 其他依赖
  ```bash
  cd ..
  pip install -r requirements.txt
  ```

## 🚀 快速开始

### 通用任务处理
1. 创建配置文件并设置必要的环境变量
   ```shell
   cd workflows/general && vim config.yaml
   ```

   | 配置名称                | 用途                                                                                   |
   |------------------------|----------------------------------------------------------------------------------------|
   | custom_openai_endpoint | 调用OpenAI GPT或其他MLLM的API地址，格式：```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key      | MLLM提供商提供的api_key                                                                |
   | bing_api_key          | Bing的api key，用于网络搜索                                                            |

2. 设置```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/general") # 通用任务处理工作流配置目录
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("您的查询") # 输入您的查询
    ```
3. 运行```python run.py```启动OmAgent。

### 视频理解任务
#### 环境准备
- **```可选```** OmAgent默认使用Milvus Lite作为向量数据库来存储向量数据。如果您希望使用完整的Milvus服务，可以使用docker部署[milvus向量数据库](https://milvus.io/docs/install_standalone-docker.md)。向量数据库用于存储视频特征向量，并根据查询检索相关向量以减少MLLM计算。未安装docker？请参考[docker安装指南](https://docs.docker.com/get-docker/)。
    ```shell
    # 下载milvus启动脚本
    curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
    # 以独立模式启动milvus
    bash standalone_embed.sh start
    ```
    部署后填写相关配置信息```workflows/video_understanding/config.yml```

- **```可选```** 配置人脸识别算法。人脸识别算法可以作为工具被代理调用，但这是可选的。您可以通过修改```workflows/video_understanding/tools/video_tools.json```配置文件并删除FaceRecognition部分来禁用此功能。默认的人脸识别数据库存储在```data/face_db```目录中，不同的文件夹对应不同的个人。

- **```可选```** 开放词汇检测（OVD）服务，用于增强OmAgent识别各种物体的能力。OVD工具依赖于此服务，但这是可选的。您可以按以下步骤禁用OVD工具。从```workflows/video_understanding/tools/video_tools.json```中删除以下内容：
    ```json 
    {
         "name": "ObjectDetection",
         "ovd_endpoint": "$<ovd_endpoint::http://host_ip:8000/inf_predict>",
         "model_id": "$<ovd_model_id::OmDet-Turbo_tiny_SWIN_T>"
    }
    ```

  如果使用ovd工具，我们使用[OmDet](https://github.com/om-ai-lab/OmDet/tree/main)进行演示。
  1. 根据[OmDet安装指南](https://github.com/om-ai-lab/OmDet/blob/main/install.md)安装OmDet及其环境。
  2. 安装将OmDet推理转换为API调用的依赖
     ```text
     pip install pydantic fastapi uvicorn
     ```
  3. 创建```wsgi.py```文件以将OmDet推理暴露为API
     ```shell
     cd OmDet && vim wsgi.py
     ```
     将[OmDet推理API代码](docs/ovd_api_doc.md)复制到wsgi.py
  4. 启动OmDet推理API，默认端口为8000
     ```shell
     python wsgi.py
     ```
- 下载一些有趣的视频

#### 运行准备
1. 创建配置文件并设置必要的环境变量
   ```shell
   cd workflows/video_understanding && vim config.yaml
   ```
2. 配置MLLM和工具的API地址和API密钥。

   | 配置名称                | 用途                                                                                    |
   |------------------------|-----------------------------------------------------------------------------------------|
   | custom_openai_endpoint | 调用OpenAI GPT或其他MLLM的API地址，格式：```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key      | 相应API提供商提供的api_key                                                              |
   | bing_api_key          | Bing的api key，用于网络搜索                                                             |
   | ovd_endpoint          | ovd工具API地址。如果使用OmDet，地址应为```http://host:8000/inf_predict```              |
   | ovd_model_id          | ovd工具使用的模型ID。如果使用OmDet，模型ID应为```OmDet-Turbo_tiny_SWIN_T```            |

2. 设置```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/video_understanding") # 视频理解任务工作流配置目录
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("") # 您将在控制台中被提示输入查询
    ```
3. 运行```python run.py```启动OmAgent。输入您想要处理的视频路径，稍等片刻，然后输入您的查询，OmAgent将根据查询作出回答。

## 🔗 相关工作
如果您对多模态算法、大语言模型和代理技术感兴趣，我们邀请您深入了解我们的研究工作：  
🔆 [如何评估检测的泛化能力？全面开放词汇检测基准](https://arxiv.org/abs/2308.13177) (AAAI24)   
🏠 [GitHub仓库](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet：具有多模态检测网络的大规模视觉-语言多数据集预训练](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268) (IET Computer Vision)  
🏠 [Github仓库](https://github.com/om-ai-lab/OmDet)

## ⭐️ 引用

如果您觉得我们的仓库有帮助，请引用我们的论文：
```angular2
@article{zhang2024omagent,
  title={OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer},
  author={Zhang, Lu and Zhao, Tiancheng and Ying, Heting and Ma, Yibo and Lee, Kyusong},
  journal={arXiv preprint arXiv:2406.16620},
  year={2024}
}
```
