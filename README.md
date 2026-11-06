# Research Library — Pipeline Airflow (INFO-H420, Assignment 3)

Pipeline Apache Airflow (TaskFlow API) qui transforme des PDF de recherche en bibliothèque consultable, exécuté sous WSL 2 / Linux.

## 1. Présentation du pipeline

```
PDF (papers/) → Markdown (PyMuPDF4LLM) → métadonnées JSON (Ollama / llama3.2, API OpenAI)
              → SQLite (data/papers.db) → index.html statique → notification Discord (webhook)
```

Le DAG `paper_pipeline` s'exécute toutes les 10 minutes (`catchup=False`, `max_active_runs=1`) :

| Tâche | Rôle |
|---|---|
| `find_new_pdfs` | Liste les PDF de `papers/` absents de la base |
| `convert_pdf` | PDF → Markdown (une instance par PDF, *dynamic task mapping*) |
| `generate_metadata` | Appel LLM : `title`, `summary`, `keywords`, `category` (JSON, 1 retry max, validation des champs) |
| `store_paper` | Upsert SQLite (`filename` unique) |
| `regenerate_html` | Régénère `index.html` (recherche + filtre par catégorie) |
| `send_notification` | Message Discord par article traité, après la mise à jour de la page |

La base SQLite reste en local, hors du dossier synchronisé Google Drive. Seuls `papers/` et `output/` sont synchronisés.

## 2. Structure du projet

```
.
├── dags/
│   └── paper_pipeline.py      # DAG unique (@dag / @task), orchestration uniquement
├── src/
│   ├── config.py              # Chemins et paramètres (variables d'environnement)
│   ├── pdf_to_md.py           # PDF → Markdown (PyMuPDF4LLM)
│   ├── llm.py                 # Client OpenAI → Ollama, JSON, retry, validation
│   ├── db_manager.py          # SQLite : table papers
│   ├── html_generator.py      # Génération de index.html
│   └── discord_notifier.py    # Webhook Discord
├── data/                      # papers.db et markdown/ (ignoré par git)
├── .env.example               # Modèle de configuration
├── requirements.txt
└── start_airflow.sh           # Script de démarrage global
```

Disposition côté Google Drive :

```
Google Drive/ResearchLibrary/
├── papers/    # PDF d'entrée
└── output/    # index.html généré
```

## 3. Prérequis

- Windows 10/11 avec WSL 2 (Ubuntu recommandé), ou Linux natif
- Python 3.12
- [Ollama](https://ollama.com) installé sur l'hôte avec le modèle `llama3.2`
- Google Drive synchronisé et accessible depuis WSL (ex. `/mnt/g/My Drive/...`)
- Un webhook Discord (Paramètres du salon → Intégrations → Webhooks)

## 4. Installation

```bash
# 1. Cloner le dépôt
git clone <URL_DU_DEPOT> research-library
cd research-library

# 2. Environnement virtuel
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Airflow, avec le fichier de contraintes officiel
AIRFLOW_VERSION=2.10.5
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# 4. Autres dépendances
pip install pymupdf4llm openai requests

# 5. Configuration
cp .env.example .env
```

Éditer `.env` :

```bash
export AIRFLOW_HOME="$PWD/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export PAPERS_DIR="/mnt/g/My Drive/ResearchLibrary/papers"   # à adapter
export OUTPUT_DIR="/mnt/g/My Drive/ResearchLibrary/output"   # à adapter
export DB_PATH="$PWD/data/papers.db"
export MARKDOWN_DIR="$PWD/data/markdown"
export OLLAMA_BASE_URL="http://localhost:11434/v1"           # voir section 6
export OLLAMA_MODEL="llama3.2"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

`.env` est chargé par `start_airflow.sh`. Pour un usage manuel : `set -a; source .env; set +a`.

## 5. ⚠️ Fins de ligne Windows (CRLF) — à traiter avant tout lancement

Un dépôt cloné ou édité sous Windows peut contenir des fins de ligne `CRLF`. Bash lit alors un `\r` parasite, ce qui produit des erreurs comme :

```
/bin/bash^M: bad interpreter: No such file or directory
$'\r': command not found
```

Dans `.env`, le `\r` se retrouve dans les valeurs des variables (chemins et URL invalides).

Convertir **le script de lancement et le `.env`** :

```bash
sudo apt install -y dos2unix
dos2unix start_airflow.sh .env
chmod +x start_airflow.sh
```

À refaire après chaque modification de ces fichiers depuis un éditeur Windows. Prévention : configurer l'éditeur en fins de ligne `LF` et utiliser `git config core.autocrlf input`.

## 6. Configuration d'Ollama (hôte Windows ↔ WSL)

Ollama tourne sur l'hôte Windows ; Airflow tourne dans WSL. Par défaut, Ollama n'écoute que sur `127.0.0.1` côté Windows.

**Option A — Mode réseau « mirrored » (WSL 2 récent, recommandé).** Dans `C:\Users\<user>\.wslconfig` :

```ini
[wsl2]
networkingMode=mirrored
```

Puis `wsl --shutdown` dans PowerShell et relancer WSL. `localhost` pointe alors vers l'hôte Windows : `OLLAMA_BASE_URL="http://localhost:11434/v1"` fonctionne.

**Option B — Mode NAT (par défaut).**

1. Exposer Ollama sur toutes les interfaces, dans PowerShell, puis redémarrer Ollama (quitter l'application depuis la barre des tâches et la relancer) :
   ```powershell
   setx OLLAMA_HOST "0.0.0.0"
   ```
2. Autoriser le port 11434 dans le pare-feu Windows (réseau privé).
3. Dans WSL, récupérer l'IP de la passerelle (hôte Windows) :
   ```bash
   ip route show default | awk '{print $3}'
   ```
4. La reporter dans `.env` :
   ```bash
   export OLLAMA_BASE_URL="http://<IP_PASSERELLE>:11434/v1"
   ```
   Cette IP peut changer à chaque redémarrage de WSL.

**Vérification depuis WSL :**

```bash
curl http://<hôte>:11434/api/tags          # doit lister llama3.2
```

Si Ollama est lancé directement dans WSL (`ollama serve`), garder `http://localhost:11434/v1`.

Modèle à télécharger : `ollama pull llama3.2`.

## 7. Lancement et utilisation

```bash
./start_airflow.sh
```

Le script :
1. active `.venv` ;
2. charge `.env` ;
3. crée les dossiers nécessaires (`papers/`, `output/`, `data/`, `data/markdown/`, `AIRFLOW_HOME`) ;
4. vérifie qu'Ollama répond (avertissement sinon) ;
5. exécute `airflow standalone`.

Au premier démarrage, l'utilisateur `admin` et son mot de passe générés sont affichés dans le terminal.

**Utilisation :**

1. Ouvrir http://localhost:8080 et se connecter.
2. Activer le DAG `paper_pipeline` (toggle).
3. Déposer un ou plusieurs PDF dans `papers/`.
4. Cliquer sur **Trigger** pour exécuter immédiatement, ou attendre le prochain run planifié (10 min).
5. Suivre les tâches dans la vue **Graph** ; les logs sont accessibles par tâche.
6. Résultat : `output/index.html` (ouvrir dans le navigateur) et notification Discord.

**Test en CLI** (terminal avec le `.env` chargé et `.venv` activé) :

```bash
airflow dags list-import-errors                    # vérifier l'import du DAG
airflow dags test paper_pipeline                   # exécution complète sans scheduler
```

## Dépannage

| Symptôme | Cause probable |
|---|---|
| `bad interpreter` / `$'\r'` | Fins de ligne CRLF → section 5 |
| `Connection refused` vers Ollama | `OLLAMA_HOST` / IP de la passerelle / pare-feu → section 6 |
| DAG absent de l'interface | Erreur d'import : `airflow dags list-import-errors` |
| Aucun PDF traité | `PAPERS_DIR` incorrect ou PDF déjà présent en base |
| Pas de message Discord | `DISCORD_WEBHOOK_URL` vide ou invalide |