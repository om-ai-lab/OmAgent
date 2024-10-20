<div align="center">
    <h1> <img src="docs/images/logo.png" height=33 align="texttop"> OmAgent</h1>
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
    <a href="README.md">English</a> | <a href="README_ZH.md">中文</a> | <a href="README_JP.md">日本語</a> | <a>Français</a>
</p>

---

## 🗓️ Mises à jour récentes
* **20/10/2024** : Nous nous engageons activement à développer la v0.2.0 🚧 De nouvelles fonctionnalités passionnantes sont en cours ! Vous êtes invités à nous rejoindre sur X et Discord~
* **20/09/2024** : Notre article a été accepté par EMNLP 2024 ! Rejoignez-nous à Miami ! 🏝
* **04/07/2024** : Le projet open-source OmAgent est officiellement lancé ! 🎉
* **24/06/2024** : [Publication de l'article de recherche OmAgent](https://arxiv.org/abs/2406.16620).

---

## 📖 Introduction

OmAgent est un système intelligent et multimodal avancé, conçu pour exploiter la puissance des grands modèles de langage multimodal et d'algorithmes innovants afin d'accomplir des tâches complexes. Le projet OmAgent comprend un cadre léger, **omagent_core**, développé pour relever les défis liés au multimodal. Il est adaptable à vos propres idées et cas d'usage !

Les trois principaux composants d'OmAgent sont :  
- **Video2RAG** : Transforme la compréhension de longues vidéos en une tâche RAG multimodale, avec l'avantage de dépasser les limitations liées à la longueur des vidéos. Attention toutefois à la perte potentielle de détails durant le prétraitement.
- **DnCLoop** : Inspiré par la méthode algorithmique « Diviser pour Régner », ce module permet une approche itérative de résolution de problèmes complexes, en décomposant chaque tâche jusqu'à ce qu'elle soit facile à résoudre.
- **Rewinder** : Conçu pour pallier la perte de détails induite par le prétraitement dans Video2RAG, Rewinder permet aux agents de revisiter des moments clés des vidéos pour recueillir des informations supplémentaires.

<p align="center">
  <img src="docs/images/OmAgent.png" width="700"/>
</p>

Pour plus d'informations, consultez notre article : **[OmAgent : Un cadre d'agent multimodal pour la compréhension vidéo complexe avec Diviser pour Régner](https://arxiv.org/abs/2406.16620)**.

---

## 🛠️ Installation

### Prérequis

- Python ≥ 3.10
- Installation de `omagent_core` :
  ```bash
  cd omagent-core
  pip install -e .
  ```

- Installation des autres dépendances :
  ```bash
  cd ..
  pip install -r requirements.txt
  ```

### 🚀 Démarrage rapide

#### Traitement des tâches générales

1. Créez un fichier de configuration `config.yaml` et définissez les variables requises :
   ```bash
   cd workflows/general
   vim config.yaml
   ```

   | Nom de la configuration   | Utilisation                                                                                       |
   |---------------------------|---------------------------------------------------------------------------------------------------|
   | custom_openai_endpoint     | API pour OpenAI GPT ou un autre modèle, format : `{custom_openai_endpoint}/chat/completions`       |
   | custom_openai_key          | Clé API fournie par le fournisseur du modèle de langage                                            |
   | bing_api_key               | Clé API de Bing pour la recherche Web                                                              |

2. Configurez `run.py` pour exécuter l'agent :
   ```python
   def run_agent(task):
       logging.init_logger("omagent", "omagent", level="INFO")
       registry.import_module(project_root=Path(__file__).parent, custom=["./engine"])
       bot_builder = Builder.from_file("workflows/general")
       input = DnCInterface(bot_id="1", task=AgentTask(id=0, task=task))
   
       bot_builder.run_bot(input)
       return input.last_output
   
   if __name__ == "__main__":
       run_agent("Votre requête ici")
   ```

3. Démarrez OmAgent en exécutant :
   ```bash
   python run.py
   ```

---

## 🧠 Tâche de compréhension vidéo

### Préparation de l'environnement

- **Optionnel** : Par défaut, OmAgent utilise Milvus Lite comme base de données vectorielle pour stocker les données. Vous pouvez déployer la version complète via Docker si nécessaire :
  ```bash
  curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
  bash standalone_embed.sh start
  ```

- **Optionnel** : Algorithme de reconnaissance faciale. Vous pouvez désactiver cette fonctionnalité dans `video_tools.json` si elle n'est pas nécessaire.
  
  Si vous activez cette option, la base de données des visages est située dans `data/face_db`.

- **Optionnel** : Intégration d'OmDet pour la détection d'objets dans les vidéos.
  
  1. Installez OmDet depuis son [dépôt](https://github.com/om-ai-lab/OmDet).
  2. Exposez l'inférence en tant qu'API via FastAPI :
     ```python
     pip install pydantic fastapi uvicorn
     ```

---

## 🔗 Travaux associés
- [Évaluation de la détection de vocabulaire ouvert](https://arxiv.org/abs/2308.13177)  
- [OmDet: Pré-entraînement multimodal pour la vision](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cvi2.12268)

## ⭐️ Citation

Si ce projet vous est utile, veuillez citer notre article :
```bibtex
@article{zhang2024omagent,
  title={OmAgent: A Multi-modal Agent Framework for Complex Video Understanding with Task Divide-and-Conquer},
  author={Zhang, Lu et al.},
  journal={arXiv preprint arXiv:2406.16620},
  year={2024}
}
```
