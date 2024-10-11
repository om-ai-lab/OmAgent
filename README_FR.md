<div>
    <h1> <img src="docs/images/logo.png" height=33 align="texttop">OmAgent</h1>
</div>

<p align="center">
  <img src="docs/images/icon.png" width="300"/>
</p>

<p align="center">
    <a>Anglais</a> | <a href="README_ZH.md">中文</a> | <a href="README_JP.md">日本語</a>
</p>


## 🗓️ Mises à jour
* 20/09/2024 : Notre article a été accepté par l'EMNLP 2024. Rendez-vous à Miami !🏝
* 04/07/2024 : Le projet open-source OmAgent a été dévoilé. 🎉
* 24/06/2024 : [Le document de recherche OmAgent a été publié.](https://arxiv.org/abs/2406.16620)




## 📖Présentation
OmAgent est un système d'agent intelligent multimodal sophistiqué, dédié à l'exploitation de la puissance des grands modèles de langage multimodaux et d'autres algorithmes multimodaux pour accomplir des tâches intrigantes. Le projet OmAgent englobe un framework d'agent intelligent léger, omagent_core, méticuleusement conçu pour relever les défis multimodaux. Avec ce cadre, nous avons construit un système complexe de compréhension vidéo longue durée : OmAgent. Naturellement, vous avez la liberté de l’utiliser pour réaliser n’importe laquelle de vos idées innovantes.  
OmAgent comprend trois composants principaux :  
- **Video2RAG** ​​: Le concept derrière ce composant est de transformer la compréhension de longues vidéos en une tâche RAG multimodale. L’avantage de cette approche est qu’elle transcende les limitations imposées par la durée de la vidéo ; cependant, l'inconvénient est qu'un tel prétraitement peut entraîner une perte de détails vidéo substantiels.  
- **DnCLoop** : Inspirés par le paradigme algorithmique classique de Divide and Conquer, nous avons conçu une logique de traitement récursive de tâches générales. Cette méthode affine de manière itérative des problèmes complexes dans un arbre de tâches, transformant finalement les tâches complexes en une série de tâches plus simples et résolubles.  
- **Rewinder Tool** : Pour résoudre le problème de perte d'informations dans le processus Video2RAG, nous avons conçu un outil de « barre de progression » nommé Rewinder qui peut être utilisé de manière autonome par les agents. Cela permet aux agents de revoir tous les détails de la vidéo, leur permettant ainsi de rechercher les informations nécessaires.  

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

Pour plus de détails, consultez notre article **[OmAgent : A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer](https://arxiv.org/abs/2406.16620)**

## 🛠️ Comment installer
-python >= 3.10
- Installer omagent_core
  ```bash
  cd omagent-core
  pip install -e .
  ```
- Autres exigences
  ```bash
  cd..
  pip install -r exigences.txt
  ```
## 🚀 Démarrage rapide

### Traitement général des tâches
1. Créez un fichier de configuration et définissez certaines variables nécessaires
   ```coquille
   cd workflows/général && vim config.yaml
   ```

| Nom de la configuration | Utilisation |
   |------------------------------|----------------------- -------------------------------------------------- ---------------|
   | custom_openai_endpoint | Adresse API pour appeler OpenAI GPT ou autre MLLM, format : ```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key | api_key fourni par le fournisseur MLLM |
   | bing_api_key | Clé API de Bing, utilisée pour la recherche sur le Web |


2. Configurez ```run.py```
    ```python
    def run_agent (tâche) :
        logging.init_logger("omagent", "omagent", level="INFO")
        registre.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/general") # Répertoire de configuration du workflow de traitement des tâches générales
        entrée = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(entrée)
        retourner input.last_output
    
    
    si __name__ == "__main__":
        run_agent("Votre requête") # Entrez votre requête
    ```
3. Démarrez OmAgent en exécutant ```python run.py```.

### Tâche de compréhension de la vidéo
#### Préparation de l'environnement
- **```Facultatif```** OmAgent utilise Milvus Lite comme base de données vectorielle pour stocker les données vectorielles par défaut. Si vous souhaitez utiliser le service Milvus complet, vous pouvez le déployer [base de données vectorielles milvus](https://milvus.io/docs/install_standalone-docker.md) à l'aide de Docker. La base de données de vecteurs est utilisée pour stocker des vecteurs de caractéristiques vidéo et récupérer des vecteurs pertinents sur la base de requêtes afin de réduire le calcul MLLM. Docker non installé ? Reportez-vous au [guide d'installation de Docker](https://docs.docker.com/get-docker/).
    ```coquille
       # Télécharger le script de démarrage de Milvus
       curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
       # Démarrez Milvus en mode autonome
       bash standalone_embed.sh démarrer
    ```
    Remplissez les informations de configuration pertinentes après le déploiement ```workflows/video_understanding/config.yml```  
    
- **```Facultatif```** Configurez l'algorithme de reconnaissance faciale. L’algorithme de reconnaissance faciale peut être appelé comme outil par l’agent, mais il est facultatif. Vous pouvez désactiver cette fonctionnalité en modifiant le fichier de configuration ```workflows/video_understanding/tools/video_tools.json``` et en supprimant la section FaceRecognition. La base de données de reconnaissance faciale par défaut est stockée dans le répertoire ```data/face_db```, avec différents dossiers correspondant à différents individus.
- **```Facultatif```** Service de détection de vocabulaire ouvert (ovd), utilisé pour améliorer la capacité d'OmAgent à reconnaître divers objets. Les outils ovd dépendent de ce service, mais il est facultatif. Vous pouvez désactiver les outils ovd en suivant ces étapes. Supprimez les éléments suivants de ```workflows/video_understanding/tools/video_tools.json```
```json 
       {
            "name": "Détection d'Objet",
            "ovd_endpoint": "$<ovd_endpoint::http://host_ip:8000/inf_predict>",
            "model_id": "$<ovd_model_id::OmDet-Turbo_tiny_SWIN_T>"
       }
    ```
  
  Si vous utilisez des outils ovd, nous utilisons [OmDet](https://github.com/om-ai-lab/OmDet/tree/main) pour la démonstration.
  1. Installez OmDet et son environnement conformément au [Guide d'installation d'OmDet](https://github.com/om-ai-lab/OmDet/blob/main/install.md).
  2. Installez les exigences pour transformer l'inférence OmDet en appels API
     ```texte
      pip installer pydantic fastapi uvicorn
     ```
  3. Créez un fichier ```wsgi.py``` pour exposer l'inférence OmDet en tant qu'API
     ```coquille
      cd OmDet && vim wsgi.py
     ```
     Copiez le [code API d'inférence OmDet] (docs/ovd_api_doc.md) dans wsgi.py
  4. Démarrez l'API d'inférence OmDet, le port par défaut est 8000
     ```coquille
     python wsgi.py
     ```
- Téléchargez des vidéos intéressantes

#### Préparation en cours d'exécution
1. Créez un fichier de configuration et définissez certaines variables d'environnement nécessaires
   ```coquille
   cd workflows/video_understanding && vim config.yaml
   ```
2. Configurez les adresses API et les clés API pour MLLM et les outils.

   | Nom de la configuration | Utilisation |
   |-------------------------------|---------------------- -------------------------------------------------- -----------------|
   | custom_openai_endpoint | Adresse API pour appeler OpenAI GPT ou autre MLLM, format : ```{custom_openai_endpoint}/chat/completions``` |
   | custom_openai_key | api_key fourni par le fournisseur d'API respectif |
   | bing_api_key | Clé API de Bing, utilisée pour la recherche sur le Web |
   | ovd_endpoint | Adresse API de l'outil ovd. Si vous utilisez OmDet, l'adresse doit être ```http://host:8000/inf_predict``` |
   | ovd_model_id | ID de modèle utilisé par l'outil ovd. Si vous utilisez OmDet, l'ID du modèle doit être ```OmDet-Turbo_tiny_SWIN_T``` |

2. Configurez ```run.py```
    ```python
    def run_agent (tâche) :
        logging.init_logger("omagent", "omagent", level="INFO")
        registre.import_module(project_root=Path(__file__).parent, custom=["./engine"])
        bot_builder = Builder.from_file("workflows/video_understanding") # Répertoire de configuration du workflow des tâches de compréhension vidéo
        entrée = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
    
        bot_builder.run_bot(entrée)
        retourner input.last_output
    
    
    si __name__ == "__main__":
        run_agent("") # Vous serez invité à saisir la requête dans la console
    ```
3. Démarrez OmAgent en exécutant ```python run.py```. Entrez le chemin de la vidéo que vous souhaitez traiter, attendez un moment, puis entrez votre requête et OmAgent répondra en fonction de la requête.


## 🔗 Œuvres liées
Si vous êtes intrigué par les algorithmes multimodaux, les grands modèles de langage et les technologies d'agents, nous vous invitons à approfondir nos recherches :  
🔆 [Comment évaluer la généralisation de la détection ? Une référence pour une détection complète du vocabulaire ouvert](https://arxiv.org/abs/2308.13177)(AAAI24)   
🏠 [Dépôt Github](https://github.com/om-ai-lab/OVDEval/tree/main)

🔆 [OmDet : pré-formation multi-ensembles de données en langage de vision à grande échelle avec réseau de détection multimodal](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268)(IET Computer Vision)  
🏠 [Dépôt Github](https://github.com/om-ai-lab/OmDet)

## ⭐️Citation

Si vous trouvez notre référentiel utile, veuillez citer notre article :  
```angulaire2
@article{zhang2024omagent,
  title={OmAgent : un cadre d'agent multimodal pour la compréhension de vidéos complexes avec la division des tâches pour régner},
  author={Zhang, Lu et Zhao, Tiancheng et Ying, Heting et Ma, Yibo et Lee, Kyusong},
  journal={préimpression arXiv arXiv:2406.16620},
  année={2024}
}
```
