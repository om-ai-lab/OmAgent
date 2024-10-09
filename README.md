<div>
    <h1> <img src="docs/images/logo.png" height=33 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/icon.png" width="300"/>
</p>

<p align="center">
    <a>English</a> | <a href="README_ZH.md">中文</a> | <a href="README_JP.md">日本語</a>
</p>


## 🗓️ Updates
* 09/20/2024: Our paper has been accepted by EMNLP 2024. See you in Miami!🏝
* 07/04/2024: The OmAgent open-source project has been unveiled. 🎉
* 06/24/2024: [The OmAgent research paper has been published.](https://arxiv.org/abs/2406.16620)




## 📖 Introduction
OmAgent is a sophisticated multimodal intelligent agent system, dedicated to harnessing the power of multimodal large language models and other multimodal algorithms to accomplish intriguing tasks. The OmAgent project encompasses a lightweight intelligent agent framework, omagent_core, meticulously designed to address multimodal challenges. With this framework, we have constructed an intricate long-form video comprehension system—OmAgent. Naturally, you have the liberty to employ it to realize any of your innovative ideas.  
OmAgent comprises three core components:  
- **Video2RAG**: The concept behind this component is to transform the comprehension of long videos into a multimodal RAG task. The advantage of this approach is that it transcends the limitations imposed by video length; however, the downside is that such preprocessing may lead to the loss of substantial video detail.  
- **DnCLoop**: Inspired by the classical algorithmic paradigm of Divide and Conquer, we devised a recursive general-task processing logic. This method iteratively refines complex problems into a task tree, ultimately transforming intricate tasks into a series of solvable, simpler tasks.  
- **Rewinder Tool**: To address the issue of information loss in the Video2RAG process, we have designed a "progress bar" tool named Rewinder that can be autonomously used by agents. This enables the agents to revisit any video details, allowing them to seek out the necessary information.  

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

For more details, check out our paper **[OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer](https://arxiv.org/abs/2406.16620)**

## 🛠️ How To Install
- python >= 3.10
- Install omagent_core
  ```bash
  cd omagent-core
  pip install -e .
  ```
- Other requirements
  ```bash
  cd ..
  pip install -r requirements.txt
  ```
## 🚀 Quick Start

### General Task Processing
1. Create a configuration file and set some necessary variables
   ```shell
   cd workflows/general && vim config.yaml
   ```

   | Configuration Name      | Usage                                                                                 |
   |-------------------------|---------------------------------------------------------------------------------------|
   | custom_openai_endpoint  | API address for calling OpenAI GPT or other MLLM, format: ```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key       | api_key provided by the MLLM provider                                                 |
   | bing_api_key            | Bing's api key, used for websearch                                                    |


2. Set up ```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/general") # General task processing workflow configuration directory
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("Your Query") # Enter your query
    ```
3. Start OmAgent by running ```python run.py```.

### Video Understanding Task
#### Environment Preparation
- **```Optional```** OmAgent uses Milvus Lite as a vector database to store vector data by default. If you wish to use the full Milvus service, you can deploy it [milvus vector database](https://milvus.io/docs/install_standalone-docker.md) using docker. The vector database is used to store video feature vectors and retrieve relevant vectors based on queries to reduce MLLM computation. Not installed docker? Refer to [docker installation guide](https://docs.docker.com/get-docker/).
    ```shell
       # Download milvus startup script
       curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
       # Start milvus in standalone mode
       bash standalone_embed.sh start
    ```
    Fill in the relevant configuration information after the deployment ```workflows/video_understanding/config.yml```  
    
- **```Optional```** Configure the face recognition algorithm. The face recognition algorithm can be called as a tool by the agent, but it is optional. You can disable this feature by modifying the ```workflows/video_understanding/tools/video_tools.json``` configuration file and removing the FaceRecognition section. The default face recognition database is stored in the ```data/face_db``` directory, with different folders corresponding to different individuals.
- **```Optional```** Open Vocabulary Detection (ovd) service, used to enhance OmAgent's ability to recognize various objects. The ovd tools depend on this service, but it is optional. You can disable ovd tools by following these steps. Remove the following from ```workflows/video_understanding/tools/video_tools.json```
    ```json 
       {
            "name": "ObjectDetection",
            "ovd_endpoint": "$<ovd_endpoint::http://host_ip:8000/inf_predict>",
            "model_id": "$<ovd_model_id::OmDet-Turbo_tiny_SWIN_T>"
       }
    ```
  
  If using ovd tools, we use [OmDet](https://github.com/om-ai-lab/OmDet/tree/main) for demonstration.
  1. Install OmDet and its environment according to the [OmDet Installation Guide](https://github.com/om-ai-lab/OmDet/blob/main/install.md).
  2. Install requirements to turn OmDet Inference into API calls
     ```text
      pip install pydantic fastapi uvicorn
     ```
  3. Create a ```wsgi.py``` file to expose OmDet Inference as an API
     ```shell
      cd OmDet && vim wsgi.py
     ```
     Copy the [OmDet Inference API code](docs/ovd_api_doc.md) to wsgi.py
  4. Start OmDet Inference API, the default port is 8000
     ```shell
     python wsgi.py
     ```
- Download some interesting videos

#### Running Preparation
1. Create a configuration file and set some necessary environment variables
   ```shell
   cd workflows/video_understanding && vim config.yaml
   ```
2. Configure the API addresses and API keys for MLLM and tools.

   | Configuration Name       | Usage                                                                                   |
   |--------------------------|-----------------------------------------------------------------------------------------|
   | custom_openai_endpoint   | API address for calling OpenAI GPT or other MLLM, format: ```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key        | api_key provided by the respective API provider                                          |
   | bing_api_key             | Bing's api key, used for web search                                                      |
   | ovd_endpoint             | ovd tool API address. If using OmDet, the address should be ```http://host:8000/inf_predict``` |
   | ovd_model_id             | Model ID used by the ovd tool. If using OmDet, the model ID should be ```OmDet-Turbo_tiny_SWIN_T``` |

   
2. Set up ```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/video_understanding") # Video understanding task workflow configuration directory
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("") # You will be prompted to enter the query in the console
    ```
3. Start OmAgent by running ```python run.py```. Enter the path of the video you want to process, wait a moment, then enter your query, and OmAgent will answer based on the query.

## 🔗 Related works
If you are intrigued by multimodal algorithms, large language models, and agent technologies, we invite you to delve deeper into our research endeavors:  
🔆 [How to Evaluate the Generalization of Detection? A Benchmark for Comprehensive Open-Vocabulary Detection](https://arxiv.org/abs/2308.13177)(AAAI24)   
🏠 [Github Repository](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet: Large-scale vision-language multi-dataset pre-training with multimodal detection network](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268)(IET Computer Vision)  
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
