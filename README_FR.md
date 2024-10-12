<div>
    <h1> <img src="docs/images/logo.png" height=33 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/icon.png" width="300"/>
</p>

<p align="center">
    <a>French</a> | <a href="README_ZH.md">中文</a> | <a href="README_JP.md">日本語</a> | Français
</p>


## 🗓️ Mises à jour
* 20/09/2024 : Notre article a été accepté par EMNLP 2024. Rendez-vous à Miami !🏝
* 04/07/2024 : Le projet open-source OmAgent a été dévoilé. 🎉
* 24/06/2024 : [L'article de recherche OmAgent a été publié.](https://arxiv.org/abs/2406.16620)




## 📖 Introduction
OmAgent est un système d'agent intelligent multimodal sophistiqué, dédié à exploiter la puissance des grands modèles de langage multimodaux et d'autres algorithmes multimodaux pour accomplir des tâches intéressantes. Le projet OmAgent comprend un cadre d'agent intelligent léger, omagent_core, conçu méticuleusement pour relever les défis multimodaux. Grâce à ce cadre, nous avons construit un système de compréhension vidéo de longue durée complexe—OmAgent. Naturellement, vous avez la liberté de l'utiliser pour réaliser vos idées innovantes.  
OmAgent se compose de trois composants principaux :  
- **Video2RAG** : L'idée derrière ce composant est de transformer la compréhension de longues vidéos en une tâche multimodale RAG. L'avantage de cette approche est qu'elle transcende les limitations imposées par la longueur des vidéos ; cependant, l'inconvénient est que ce prétraitement peut entraîner une perte substantielle de détails vidéo.  
- **DnCLoop** : Inspiré par le paradigme algorithmique classique de Diviser pour Régner, nous avons conçu une logique de traitement de tâches générale récursive. Cette méthode affine de manière itérative les problèmes complexes en un arbre de tâches, transformant finalement les tâches complexes en une série de tâches plus simples et solvables.  
- **Outil Rewinder** : Pour pallier la perte d'information dans le processus Video2RAG, nous avons conçu un outil appelé "barre de progression", Rewinder, que les agents peuvent utiliser de manière autonome. Cela permet aux agents de revisiter tous les détails d'une vidéo, leur permettant de rechercher les informations nécessaires.  

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

Pour plus de détails, consultez notre article **[OmAgent : Un cadre d'agent multimodal pour la compréhension vidéo complexe avec Diviser pour Régner](https://arxiv.org/abs/2406.16620)**

## 🛠️ Comment installer
- python >= 3.10
- Installer omagent_core
  ```bash
  cd omagent-core
  pip install -e .



Autres dépendances
```
cd ..
pip install -r requirements.txt
```
## 🚀 Démarrage rapide

### Traitement des tâches générales
1. Créez un fichier de configuration et définissez quelques variables nécessaires :
   ```shell
   cd workflows/general && vim config.yaml


| Nom de la configuration   | Utilisation                                                                                   |
|---------------------------|-----------------------------------------------------------------------------------------------|
| custom_openai_endpoint     | Adresse API pour appeler OpenAI GPT ou un autre MLLM, format : ```{custom_openai_endpoint}/chat/completions``` |
| custom_openai_key          | api_key fourni par le fournisseur MLLM                                                        |
| bing_api_key               | Clé API de Bing, utilisée pour la recherche web                                               |


2. Configurez ```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/general") # Répertoire de configuration du workflow de traitement des tâches générales
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("Votre requête") # Entrez votre requête
    ```
3. Démarrez OmAgent en exécutant ```python run.py```.

### Tâche de compréhension vidéo
#### Préparation de l'environnement
- **```Optionnel```** OmAgent utilise par défaut Milvus Lite comme base de données vectorielle pour stocker des données vectorielles. Si vous souhaitez utiliser le service complet de Milvus, vous pouvez le déployer via [base de données vectorielle milvus](https://milvus.io/docs/install_standalone-docker.md) en utilisant docker. La base de données vectorielle est utilisée pour stocker les vecteurs de fonctionnalités vidéo et récupérer des vecteurs pertinents en fonction des requêtes afin de réduire le calcul de MLLM. Vous n'avez pas installé docker ? Consultez le [guide d'installation de docker](https://docs.docker.com/get-docker/).
    ```shell
       # Téléchargez le script de démarrage de milvus
       curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
       # Démarrez milvus en mode autonome
       bash standalone_embed.sh start
    ```
    Remplissez les informations de configuration pertinentes après le déploiement ```workflows/video_understanding/config.yml```  
    
- **```Optionnel```** Configurez l'algorithme de reconnaissance faciale. L'algorithme de reconnaissance faciale peut être utilisé comme un outil par l'agent, mais il est facultatif. Vous pouvez désactiver cette fonctionnalité en modifiant le fichier de configuration ```workflows/video_understanding/tools/video_tools.json``` et en supprimant la section FaceRecognition. La base de données de reconnaissance faciale par défaut est stockée dans le répertoire ```data/face_db```, avec différents dossiers correspondant à différentes personnes.
- **```Optionnel```** Service de détection de vocabulaire ouvert (ovd), utilisé pour améliorer la capacité d'OmAgent à reconnaître divers objets. Les outils ovd dépendent de ce service, mais il est facultatif. Vous pouvez désactiver les outils ovd en suivant ces étapes. Supprimez ce qui suit dans ```workflows/video_understanding/tools/video_tools.json```
    ```json 
       {
            "name": "ObjectDetection",
            "ovd_endpoint": "$<ovd_endpoint::http://host_ip:8000/inf_predict>",
            "model_id": "$<ovd_model_id::OmDet-Turbo_tiny_SWIN_T>"
       }
    ```
  
  Si vous utilisez les outils ovd, nous utilisons [OmDet](https://github.com/om-ai-lab/OmDet/tree/main) à titre de démonstration.
  1. Installez OmDet et son environnement selon le [guide d'installation d'OmDet](https://github.com/om-ai-lab/OmDet/blob/main/install.md).
  2. Installez les exigences pour transformer l'inférence OmDet en appels API
     ```text
      pip install pydantic fastapi uvicorn
     ```
  3. Créez un fichier ```wsgi.py``` pour exposer l'inférence OmDet en tant qu'API
     ```shell
      cd OmDet && vim wsgi.py
     ```
     Copiez le [code API d'inférence OmDet](docs/ovd_api_doc.md) dans wsgi.py
  4. Démarrez l'API d'inférence OmDet, le port par défaut est 8000
     ```shell
     python wsgi.py
     ```
- Téléchargez des vidéos intéressantes

#### Préparation de l'exécution
1. Créez un fichier de configuration et définissez certaines variables d'environnement nécessaires
   ```shell
   cd workflows/video_understanding && vim config.yaml
   
2. Configurez les adresses API et les clés API pour MLLM et les outils.

| Nom de la configuration     | Utilisation                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| custom_openai_endpoint       | Adresse API pour appeler OpenAI GPT ou un autre MLLM, format : ```{custom_openai_endpoint}/chat/completions``` |
| custom_openai_key            | api_key fournie par le fournisseur API respectif                                                |
| bing_api_key                 | Clé API de Bing, utilisée pour la recherche web                                                 |
| ovd_endpoint                 | Adresse API de l'outil ovd. Si vous utilisez OmDet, l'adresse doit être ```http://host:8000/inf_predict``` |
| ovd_model_id                 | ID du modèle utilisé par l'outil ovd. Si vous utilisez OmDet, l'ID du modèle doit être ```OmDet-Turbo_tiny_SWIN_T``` |


2. Configurez ```run.py```
    ```python
    def run_agent(task):
        logging.init_logger("omagent", "omagent", level="INFO")
        registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/video_understanding") # Répertoire de configuration du workflow pour la tâche de compréhension vidéo
        input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(input)
        return input.last_output
    
    
    if __name__ == "__main__":
        run_agent("") # Vous serez invité à entrer la requête dans la console
    ```
3. Démarrez OmAgent en exécutant ```python run.py```. Entrez le chemin de la vidéo que vous souhaitez traiter, attendez un moment, puis entrez votre requête, et OmAgent répondra en fonction de la requête.

## 🔗 Travaux associés
Si vous êtes intéressé par les algorithmes multimodaux, les grands modèles de langage et les technologies d'agents, nous vous invitons à explorer davantage nos travaux de recherche :  
🔆 [Comment évaluer la généralisation de la détection ? Un benchmark pour une détection de vocabulaire ouvert complète](https://arxiv.org/abs/2308.13177)(AAAI24)   
🏠 [Dépôt Github](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet : Pré-entraînement multi-dataset vision-langage à grande échelle avec réseau de détection multimodal](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268)(IET Computer Vision)  
🏠 [Dépôt Github](https://github.com/om-ai-lab/OmDet)

## ⭐️ Citation

Si vous trouvez notre dépôt utile, veuillez citer notre article :  
```angular2
@article{zhang2024omagent,
  title={OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer},
  author={Zhang, Lu and Zhao, Tiancheng and Ying, Heting and Ma, Yibo and Lee, Kyusong},
  journal={arXiv preprint arXiv:2406.16620},
  year={2024}
}
```
