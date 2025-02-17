# EchoPageAI
A (html) page generator with ai model(s) which respond to a request.

**EchoPageAI** est une application intelligente qui génère dynamiquement des pages HTML en fonction des besoins de l'utilisateur. Il utilise des agents IA spécialisés (recherche, conseil, organisation, etc.) pour analyser et répondre à la demande.  

Le programme est en français.
---

## ✨ Fonctionnalités  
✅ Détection automatique des besoins de l'utilisateur  
✅ Génération dynamique de contenu en HTML  
✅ Agents spécialisés pour des réponses ciblées  
✅ Intégration avec **Ollama** (modèles locaux) et **Together AI** (API externe)  
✅ Interface utilisateur avec **Tkinter**  

---

## 🛠️ Prérequis  

Avant d'utiliser **EchoPageAI**, assure-toi d'avoir :  

- **Python 3.9+** installé  
- **Git** installé  
- **pip** à jour :  
  ```bash
  python -m pip install --upgrade pip


Ollama doit être installé.

Un fichier .env avec ta clé API Together AI (si tu veux utiliser le mode externe), voir changer le code de "base_role.py" (fonction _generate_external) si tu veux que ça soit une autre api externe.
TOGETHER_API_KEY=ta_cle_api


**Installation**

1️⃣ Clone le repo

git clone https://github.com/Aurekin/EchoPageAI.git
cd EchoPageAI

2️⃣ Installe les dépendances

pip install -r requirements.txt

3️⃣ Lance l’application

python main.py

--------------------------------------------------

🔧 Configuration
🏗️ Modes de fonctionnement

L'application supporte deux modes pour les modèles IA :

    Mode local 🏠 (via Ollama)
    Mode externe 🌍 (via Together AI)

Par défaut, les agents IA utilisent Ollama en local. Si tu veux utiliser Together AI, ajoute mode='external' dans base_role.py.
📁 Gestion des rôles

Les rôles des agents sont définis dans roles.json. Tu peux en ajouter/modifier en changeant ce fichier.


📂 EchoPageAI/

├── 📜 main.py → Interface utilisateur avec Tkinter

├── 📜 agent_manager.py → Gestion des agents IA

├── 📂 roles/ → Définition des rôles des agents

│ ├── 📜 base_role.py → Classe de base des rôles

│ ├── 📜 detecteur_besoins.py → Détection des besoins

│ ├── 📜 connecteur.py → Synthèse des réponses

│ ├── 📜 recherche.py → Agent de recherche

│ ├── 📜 role_class.py → Création dynamique de rôles

│ ├── 📜 roles.json → Fichier de configuration des rôles

└── 📜 .env → Clé API (optionnel pour Together AI)

---------------------------------------------------------
📧 Contact
Si tu as des questions, ouvre une Issue ou contacte-moi sur GitHub ! 😃


🤝 **Contribution**

Si tu veux améliorer EchoPageAI :
1️⃣ Fork le repo
2️⃣ Crée une branche : git checkout -b feature-ma-feature
3️⃣ Ajoute tes modifications et commit
4️⃣ Fais un PR sur GitHub 🚀
