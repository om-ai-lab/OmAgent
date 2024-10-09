<div>
    <h1> <img src="docs/images/logo.png" height=33 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/icon.png" width="300"/>
</p>

<p align="center">
    <a href="README.md">English</a> | <a href="README_ZH.md">中文</a> | <a>日本語</a>
</p>


## 🗓️ 更新
* 2024年9月20日: 私たちの論文がEMNLP 2024に採択されました。マイアミでお会いしましょう！🏝
* 2024年7月4日: OmAgentオープンソースプロジェクトが公開されました。🎉
* 2024年6月24日: [OmAgent研究論文が発表されました。](https://arxiv.org/abs/2406.16620)




## 📖 紹介
OmAgentは、高度なマルチモーダルインテリジェントエージェントシステムであり、マルチモーダル大規模言語モデルや他のマルチモーダルアルゴリズムの力を活用して興味深いタスクを達成することを目的としています。OmAgentプロジェクトには、マルチモーダル課題に対処するために設計された軽量なインテリジェントエージェントフレームワークであるomagent_coreが含まれています。このフレームワークを使用して、複雑な長編ビデオ理解システムであるOmAgentを構築しました。もちろん、あなたの革新的なアイデアを実現するために使用することもできます。  
OmAgentは3つの主要なコンポーネントで構成されています：  
- **Video2RAG**: このコンポーネントの背後にある概念は、長編ビデオの理解をマルチモーダルRAGタスクに変換することです。このアプローチの利点は、ビデオの長さによる制約を超えることができることですが、その欠点は、そのような前処理が大量のビデオ詳細情報の損失を引き起こす可能性があることです。  
- **DnCLoop**: 古典的なアルゴリズムパラダイムであるDivide and Conquerに触発されて、再帰的な一般タスク処理ロジックを考案しました。この方法は、複雑な問題をタスクツリーに反復的に精緻化し、最終的に複雑なタスクを一連の解決可能な単純なタスクに変換します。  
- **Rewinder Tool**: Video2RAGプロセスでの情報損失の問題に対処するために、エージェントが自律的に使用できる「進行状況バー」ツールであるRewinderを設計しました。これにより、エージェントは任意のビデオの詳細を再訪し、必要な情報を探し出すことができます。  

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

詳細については、私たちの論文 **[OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer](https://arxiv.org/abs/2406.16620)** をご覧ください。

## 🛠️ インストール方法
- python >= 3.10
- omagent_coreのインストール
  ```bash
  cd omagent-core
  pip install -e .
  ```
- その他の要件
  ```bash
  cd ..
  pip install -r requirements.txt
  ```
## 🚀 クイックスタート

### 一般タスク処理
1. 設定ファイルを作成し、いくつかの必要な変数を設定します
   ```shell
   cd workflows/general && vim config.yaml
   ```

   | 設定名                  | 用途                                                                                 |
   |-------------------------|---------------------------------------------------------------------------------------|
   | custom_openai_endpoint  | OpenAI GPTまたは他のMLLMを呼び出すためのAPIアドレス、形式: ```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key       | MLLMプロバイダーが提供するapi_key                                                 |
   | bing_api_key            | Bingのapiキー、web検索に使用                                                    |


2. ```run.py```を設定します
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/general") # 一般タスク処理ワークフロー設定ディレクトリ
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("Your Query") # クエリを入力
    ```
3. ```python run.py```を実行してOmAgentを起動します。

### ビデオ理解タスク
#### 環境準備
- **```オプション```** OmAgentはデフォルトでMilvus Liteをベクトルデータベースとして使用してベクトルデータを保存します。完全なMilvusサービスを使用したい場合は、dockerを使用して[milvusベクトルデータベース](https://milvus.io/docs/install_standalone-docker.md)をデプロイできます。ベクトルデータベースは、ビデオ特徴ベクトルを保存し、クエリに基づいて関連するベクトルを取得してMLLMの計算量を減らすために使用されます。dockerをインストールしていない？[dockerインストールガイド](https://docs.docker.com/get-docker/)を参照してください。
    ```shell
       # milvusスタートアップスクリプトをダウンロード
       curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
       # スタンドアロンモードでmilvusを起動
       bash standalone_embed.sh start
    ```
    デプロイ後、関連する設定情報を記入します ```workflows/video_understanding/config.yml```  
    
- **```オプション```** 顔認識アルゴリズムを設定します。顔認識アルゴリズムはエージェントのツールとして呼び出すことができますが、これはオプションです。```workflows/video_understanding/tools/video_tools.json```設定ファイルを変更し、FaceRecognitionセクションを削除することでこの機能を無効にすることができます。デフォルトの顔認識データベースは```data/face_db```ディレクトリに保存されており、異なるフォルダが異なる個人に対応しています。
- **```オプション```** Open Vocabulary Detection (ovd)サービスは、OmAgentのさまざまなオブジェクトを認識する能力を強化するために使用されます。ovdツールはこのサービスに依存していますが、これはオプションです。次の手順に従ってovdツールを無効にすることができます。```workflows/video_understanding/tools/video_tools.json```から次の部分を削除します
    ```json 
       {
            "name": "ObjectDetection",
            "ovd_endpoint": "$<ovd_endpoint::http://host_ip:8000/inf_predict>",
            "model_id": "$<ovd_model_id::OmDet-Turbo_tiny_SWIN_T>"
       }
    ```
  
  ovdツールを使用する場合、デモンストレーションには[OmDet](https://github.com/om-ai-lab/OmDet/tree/main)を使用します。
  1. [OmDetインストールガイド](https://github.com/om-ai-lab/OmDet/blob/main/install.md)に従ってOmDetとその環境をインストールします。
  2. OmDet InferenceをAPI呼び出しに変換するための要件をインストールします
     ```text
      pip install pydantic fastapi uvicorn
     ```
  3. OmDet InferenceをAPIとして公開するための```wsgi.py```ファイルを作成します
     ```shell
      cd OmDet && vim wsgi.py
     ```
     [OmDet Inference APIコード](docs/ovd_api_doc.md)をwsgi.pyにコピーします
  4. OmDet Inference APIを起動します。デフォルトのポートは8000です
     ```shell
     python wsgi.py
     ```
- 興味深いビデオをいくつかダウンロードします

#### 実行準備
1. 設定ファイルを作成し、いくつかの必要な環境変数を設定します
   ```shell
   cd workflows/video_understanding && vim config.yaml
   ```
2. MLLMおよびツールのAPIアドレスとAPIキーを設定します。

   | 設定名                   | 用途                                                                                   |
   |--------------------------|-----------------------------------------------------------------------------------------|
   | custom_openai_endpoint   | OpenAI GPTまたは他のMLLMを呼び出すためのAPIアドレス、形式: ```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key        | 各APIプロバイダーが提供するapi_key                                          |
   | bing_api_key             | Bingのapiキー、web検索に使用                                                      |
   | ovd_endpoint             | ovdツールAPIアドレス。OmDetを使用する場合、アドレスは```http://host:8000/inf_predict``` |
   | ovd_model_id             | ovdツールが使用するモデルID。OmDetを使用する場合、モデルIDは```OmDet-Turbo_tiny_SWIN_T``` |

   
2. ```run.py```を設定します
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/video_understanding") # Video understanding task workflow configuration directory
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("") # コンソールでクエリを入力するように促されます
    ```
3. ```python run.py```を実行してOmAgentを起動します。処理したいビデオのパスを入力し、しばらく待ってからクエリを入力すると、OmAgentがクエリに基づいて回答します。

## 🔗 関連作業
マルチモーダルアルゴリズム、大規模言語モデル、およびエージェント技術に興味がある場合は、私たちの研究活動をさらに詳しく調べてください：  
🔆 [How to Evaluate the Generalization of Detection? A Benchmark for Comprehensive Open-Vocabulary Detection](https://arxiv.org/abs/2308.13177)(AAAI24)   
🏠 [Github Repository](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet: Large-scale vision-language multi-dataset pre-training with multimodal detection network](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268)(IET Computer Vision)  
🏠 [Github Repository](https://github.com/om-ai-lab/OmDet)

## ⭐️ 引用

私たちのリポジトリが役立つと感じた場合は、私たちの論文を引用してください：  
```angular2
@article{zhang2024omagent,
  title={OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer},
  author={Zhang, Lu and Zhao, Tiancheng and Ying, Heting and Ma, Yibo and Lee, Kyusong},
  journal={arXiv preprint arXiv:2406.16620},
  year={2024}
}
```
