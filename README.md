# Research Library: Airflow Pipeline

INFO-H420, Assignment 3. A local Apache Airflow pipeline that turns research PDFs into a searchable library (Markdown conversion, local LLM metadata extraction, SQLite, static HTML page, Discord notification).

> Design, module internals and DAG structure are described in the project report. This README only covers **setup, configuration, execution and troubleshooting**.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Connecting Airflow to Ollama](#4-connecting-airflow-to-ollama)
5. [Running the pipeline](#5-running-the-pipeline)
6. [Verifying the results](#6-verifying-the-results)
7. [Testing without the scheduler](#7-testing-without-the-scheduler)
8. [Maintenance and reset](#8-maintenance-and-reset)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| OS | Linux, or Windows 10/11 with WSL 2 (Ubuntu recommended) |
| Python | 3.12 (`python3.12 -m venv` must work) |
| Ollama | Installed with the `llama3.2` model pulled (`ollama pull llama3.2`) |
| Google Drive | Desktop client syncing a `ResearchLibrary/` folder, reachable from the machine running Airflow |
| Discord webhook | Channel settings → Integrations → Webhooks → New Webhook → Copy URL |
| Tools | `git`, `curl`, `sqlite3` (optional, for checks), `dos2unix` (WSL/Windows) |

Google Drive layout expected by the pipeline:

```
Google Drive/ResearchLibrary/
├── papers/    # drop your PDFs here
└── output/    # index.html is generated here
```

On WSL, Google Drive for Desktop is usually exposed as `/mnt/g/My Drive/...`. If `/mnt/g` does not exist:

```bash
sudo mkdir -p /mnt/g
sudo mount -t drvfs G: /mnt/g
```

## 2. Installation

```bash
# 1. Clone
git clone <REPOSITORY_URL> research-library
cd research-library

# 2. Virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Airflow, installed with the official constraints file
AIRFLOW_VERSION=2.10.5
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# 4. Remaining dependencies
pip install pymupdf4llm openai requests

# 5. Configuration file
cp .env.example .env
```

> `requirements.txt` lists the direct dependencies for reference. Install Airflow with the constraints command above, not with `pip install -r requirements.txt` alone, otherwise pip may resolve incompatible versions.

### Windows line endings (WSL users, do this before the first run)

Files cloned or edited on Windows may have CRLF line endings. Bash then fails with `bad interpreter: /bin/bash^M` or `$'\r': command not found`, and `\r` ends up inside the values of `.env`.

```bash
sudo apt install -y dos2unix
dos2unix start_airflow.sh .env
chmod +x start_airflow.sh
```

Repeat after any edit from a Windows editor. To prevent it: use LF in your editor and run `git config core.autocrlf input`.

## 3. Configuration

Edit `.env` (it is git-ignored). All variables are required by `start_airflow.sh`.

```bash
export AIRFLOW_HOME="$PWD/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export PAPERS_DIR="/mnt/g/My Drive/ResearchLibrary/papers"
export OUTPUT_DIR="/mnt/g/My Drive/ResearchLibrary/output"
export DB_PATH="$PWD/data/papers.db"
export MARKDOWN_DIR="$PWD/data/markdown"
export OLLAMA_BASE_URL="http://localhost:11434/v1"
export OLLAMA_MODEL="llama3.2"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/<id>/<token>"
```

| Variable | Meaning | Must be |
|---|---|---|
| `AIRFLOW_HOME` | Airflow metadata, logs, config | Local path |
| `AIRFLOW__CORE__DAGS_FOLDER` | Where Airflow looks for DAGs | Absolute path to `dags/` |
| `AIRFLOW__CORE__LOAD_EXAMPLES` | Hides Airflow's example DAGs | `False` |
| `PAPERS_DIR` | Input PDFs | Inside the Google Drive folder |
| `OUTPUT_DIR` | Location of `index.html` | Inside the Google Drive folder |
| `DB_PATH` | SQLite file | **Outside** the Google Drive folder |
| `MARKDOWN_DIR` | Intermediate Markdown files | Local path |
| `OLLAMA_BASE_URL` | OpenAI-compatible endpoint, must end in `/v1` | See next section |
| `OLLAMA_MODEL` | Model name as shown by `ollama list` | e.g. `llama3.2` |
| `DISCORD_WEBHOOK_URL` | Webhook target (empty value disables notifications) | Valid Discord URL |

Optional, so you don't have to unpause the DAG manually: add `export AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False` to `.env` **before the first start**.

Test the webhook independently:

```bash
curl -H "Content-Type: application/json" \
     -d '{"content": "webhook test"}' "$DISCORD_WEBHOOK_URL"
```

## 4. Connecting Airflow to Ollama

Pick the case that matches your setup, then confirm with the check at the end.

**Case 1: Ollama runs in the same environment as Airflow** (native Linux, or `ollama serve` inside WSL). Keep `OLLAMA_BASE_URL="http://localhost:11434/v1"`.

**Case 2: Ollama runs on the Windows host, Airflow in WSL.** By default Ollama listens on `127.0.0.1` on the Windows side only.

*Option A: mirrored networking (recent WSL 2, recommended).* In `C:\Users\<user>\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Run `wsl --shutdown` in PowerShell, restart WSL. `localhost` now reaches the Windows host, so keep `http://localhost:11434/v1`.

*Option B: NAT mode (default).*

1. In PowerShell: `setx OLLAMA_HOST "0.0.0.0"`, then quit Ollama from the taskbar and relaunch it.
2. Allow inbound TCP port 11434 in Windows Firewall (private network).
3. In WSL, get the host IP: `ip route show default | awk '{print $3}'`
4. Set `OLLAMA_BASE_URL="http://<GATEWAY_IP>:11434/v1"` in `.env`. This IP can change at every WSL restart.

**Check from the Airflow environment** (should list `llama3.2`):

```bash
curl "${OLLAMA_BASE_URL%/v1}/api/tags"
```

## 5. Running the pipeline

```bash
./start_airflow.sh
```

The script can be run from any directory. It activates `.venv`, loads `.env`, creates the working folders, warns if Ollama is unreachable, then runs `airflow standalone` (webserver, scheduler and triggerer in one process).

On first start, Airflow creates an `admin` user. The password is printed in the terminal and stored in `$AIRFLOW_HOME/standalone_admin_password.txt`.

Then:

1. Open <http://localhost:8080> and log in.
2. Enable the `paper_pipeline` DAG with the toggle (skip if you set `DAGS_ARE_PAUSED_AT_CREATION=False`).
3. Copy one or more PDFs into `PAPERS_DIR`.
4. Click **Trigger** for an immediate run, or wait for the next scheduled run (every 10 minutes).
5. Follow the run in the **Grid** or **Graph** view; click a task, then **Logs**, for details.

Stop with `Ctrl+C` in the terminal running the script.

## 6. Verifying the results

| Output | How to check |
|---|---|
| Web page | Open `OUTPUT_DIR/index.html` in a browser; try the search box and the category filter |
| Database | `sqlite3 "$DB_PATH" "SELECT filename, title, category FROM papers;"` |
| Markdown | `ls "$MARKDOWN_DIR"` |
| Notification | One Discord message per newly processed paper |
| Idempotence | Trigger the DAG again with no new PDF: no paper is reprocessed and no message is sent |
