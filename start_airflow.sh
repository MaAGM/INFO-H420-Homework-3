#!/bin/bash
# Lance le pipeline Research Library : à exécuter depuis n'importe où, avec ./start_airflow.sh
set -euo pipefail

# Se placer à la racine du projet (dossier de ce script)
cd "$(dirname "$(readlink -f "$0")")"

# 1. Environnement virtuel
if [ ! -f .venv/bin/activate ]; then
  echo "Erreur : .venv introuvable. Crée-le d'abord (voir README)." >&2
  exit 1
fi
source .venv/bin/activate

# 2. Variables d'environnement (chemins, Ollama, Discord, Airflow)
if [ ! -f .env ]; then
  echo "Erreur : .env introuvable. Fais : cp .env.example .env puis adapte les chemins." >&2
  exit 1
fi
set -a
source .env
set +a

# 3. Dossiers nécessaires
mkdir -p "$PAPERS_DIR" "$OUTPUT_DIR" "$(dirname "$DB_PATH")" "$MARKDOWN_DIR" "$AIRFLOW_HOME"

# 4. Vérifier qu'Ollama répond (avertissement seulement)
OLLAMA_ROOT="${OLLAMA_BASE_URL%/v1}"
if ! curl -sf "$OLLAMA_ROOT/api/tags" > /dev/null; then
  echo "Attention : Ollama ne répond pas sur $OLLAMA_ROOT (lance 'ollama serve')." >&2
fi

echo "PAPERS_DIR = $PAPERS_DIR"
echo "OUTPUT_DIR = $OUTPUT_DIR"
echo "DB_PATH    = $DB_PATH"
echo "Modèle     = $OLLAMA_MODEL"
echo "UI Airflow : http://localhost:8080"

# 5. Lancer Airflow
exec airflow standalone