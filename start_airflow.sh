#!/bin/bash
# Run the Research Library pipeline: can be executed from anywhere, with ./start_airflow.sh
set -euo pipefail

# Place yourself at the root of the project (folder of this script)
cd "$(dirname "$(readlink -f "$0")")"

# 1. Virtual environment
if [ ! -f .venv/bin/activate ]; then
  echo "Erreur : .venv is missing. Create it first (see README)." >&2
  exit 1
fi
source .venv/bin/activate

# 2. Environment variables (paths, Ollama, Discord, Airflow)
if [ ! -f .env ]; then
  echo "Erreur : .env is missing. Do: cp .env.example .env then adapt the paths." >&2
  exit 1
fi
set -a
source .env
set +a

# 3. Create necessary directories
mkdir -p "$PAPERS_DIR" "$OUTPUT_DIR" "$(dirname "$DB_PATH")" "$MARKDOWN_DIR" "$AIRFLOW_HOME"

# 4. Verify that Ollama responds (warning only)
OLLAMA_ROOT="${OLLAMA_BASE_URL%/v1}"
if ! curl -sf "$OLLAMA_ROOT/api/tags" > /dev/null; then
  echo "Warning : Ollama is not responding on $OLLAMA_ROOT (run 'ollama serve')." >&2
fi

echo "PAPERS_DIR = $PAPERS_DIR"
echo "OUTPUT_DIR = $OUTPUT_DIR"
echo "DB_PATH    = $DB_PATH"
echo "Modèle     = $OLLAMA_MODEL"
echo "UI Airflow : http://localhost:8080"

# 5. Run Airflow
exec airflow standalone