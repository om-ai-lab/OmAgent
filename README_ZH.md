<div>
    <h1> <img src="docs/images/logo.png" height=30 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/icon.png" width="300"/>
</p>

<p align="center">
    <a href="README.md">English</a> | <a>中文</a>
</p>


## 🗓️ 更新
* 09/20/2024: 我们的论文已经被 EMNLP 2024 收录。 迈阿密见！🏝
* 07/04/2024: OmAgent开源项目发布 🎉
* 06/24/2024: [OmAgent论文发布](https://arxiv.org/abs/2406.16620)




## 📖 介绍
OmAgent是一个多模态智能体系统，专注于利用多模态大语言模型能力以及其他多模态算法来做一些有趣的事。OmAgent项目包含一个专为解决多模态任务而设计的轻量级智能体框架omagent_core。我们利用这个框架搭建了超长复杂视频理解系统——OmAgent，当然你可以利用它实现你的任何想法。  
OmAgent包括三个核心组成部分:
- **Video2RAG**: 这部分的思想是将长视频理解转换为多模态RAG任务，好处是可以不受视频长度限制，但问题是这样的预处理会损失大量视频细节信息。
- **DnCLoop**: 受到经典算法思想Divide and Conquer启发，我们设计了一个递归的通用任务处理逻辑，它将复杂的问题不断细化形成任务树，并最终使复杂任务变成一组可解得简单任务。
- **Rewinder Tool**: 为了解决Video2RAG过程中信息损失的问题，我们设计了一个可以由智能体自主使用的“进度条”工具。智能体可以决定重看视频的任何细节，寻找他所需要的信息。

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

## 🛠️ 安装
- python >= 3.10
- 安装omagent_core
  ```bash
  cd omagent-core
  pip install -e .
  ```
- 安装requirements
  ```bash
  cd ..
  pip install -r requirements.txt
  ```
## 🚀 快速开始

### 通用任务处理
1. 创建配置文件并配置一些必要的变量
   ```shell
   cd workflows/general && vim config.yaml
   ```

   | 配置名                    | 用处                                                                              |
   |------------------------|---------------------------------------------------------------------------------|
   | custom_openai_endpoint | 调用OpenAI GPT或其他MLLM的API地址，地址格式遵循```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key      | MLLM提供方的api_key                                                                 |
   | bing_api_key           | Bing的api key，用于websearch                                                        |

   

2. 设置```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/general") # 通用任务处理workflow配置目录
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("Your Query") # 输入你想问的问题
    ```
3. ```python run.py```启动OmAgent。

### 视频理解任务
#### 相关环境准备
- **```可选```** OmAgent默认使用Milvus Lite作为向量数据库存储向量数据。如果你希望使用完整的Milvus服务，可以使用docker部署[milvus向量数据库](https://milvus.io/docs/install_standalone-docker.md)。向量数据库用于储存视频特征向量，以根据问题检索相关向量，减少MLLM的计算量。未安装docker？请参考[docker安装指南](https://docs.docker.com/get-docker/)。
    ```shell
       # 下载milvus启动脚本
       curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
       # 以standalone模式启动milvus
       bash standalone_embed.sh start
    ```
    部署完成后填写相关配置信息```workflows/video_understanding/config.yml```  
    
- **```可选```** 配置人脸识别算法。人脸识别算法可以作为智能体的工具进行调用，当然这是可选的。你可以通过修改```workflows/video_understanding/tools/video_tools.json```配置文件，删除其中关于FaceRecognition的部分对该功能进行禁用。默认的人脸识别底库存储在```data/face_db```目录下，不同文件夹对应不同人物。
- **```可选```** Open Vocabulary Detection(ovd)服务，开放词表检测，用于增强OmAgent对于各种目标物体的识别能力，ovd tools依赖于此，当然这是可选的。你可以按如下步骤对ovd tools进行禁用。 删除```workflows/video_understanding/tools/video_tools.json```中的
    ```json 
       {
            "name": "ObjectDetection",
            "ovd_endpoint": "$<ovd_endpoint::http://host_ip:8000/inf_predict>",
            "model_id": "$<ovd_model_id::OmDet-Turbo_tiny_SWIN_T>"
       }
    ```
  
  如果使用ovd tools，我们使用[OmDet](https://github.com/om-ai-lab/OmDet/tree/main)作为演示。
  1. 根据[OmDet Installation Guide](https://github.com/om-ai-lab/OmDet/blob/main/install.md)安装OmDet及环境。
  2. 安装将OmDet Inference转为API调用的requirements
     ```text
      pip install pydantic fastapi uvicorn
     ```
  3. 新建```wsgi.py```文件，暴露OmDet Inference为API
     ```shell
      cd OmDet && vim wsgi.py
     ```
     拷贝[OmDet Inference API代码](docs/ovd_api_doc.md)到wsgi.py
  4. 启动OmDet Inference API，默认端口为8000
     ```shell
     python wsgi.py
     ```
- 下载一些有趣的视频

#### 运行准备
1. 创建配置文件并配置一些必要的变量
   ```shell
   cd workflows/video_understanding && vim config.yaml
   ```
2. 配置MLLM, tools调用的API地址和API key。

   | 配置名                     | 用处                                                                        |
   |--------------------------|---------------------------------------------------------------------------|
   | custom_openai_endpoint   | 调用OpenAI GPT或其他MLLM的API地址，地址格式遵循```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key        | 对应调用地址提供方的api_key                                                         |
   | bing_api_key             | Bing的api key，用于websearch                                                  |
   | ovd_endpoint             | ovd tool的调用地址。如果你使用OmDet，调用地址应该为```http://host:8000/inf_predict```        |
   | ovd_model_id             | ovd tool调用使用的模型id。如果你使用OmDet，调用的模型id应该为```OmDet-Turbo_tiny_SWIN_T```      |

   

2. 设置```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/video_understanding") # 视频理解任务workflow配置目录
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("") # 问题会在console中提示你输入
    ```
3. ```python run.py```启动OmAgent。输入你想要处理的视频路径，稍等片刻，输入你想问的问题，OmAgent会根据问题回答你。

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