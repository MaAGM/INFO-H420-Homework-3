# Research Library — Airflow Pipeline (INFO-H420, Assignment 3)

Apache Airflow pipeline (TaskFlow API) that turns research PDFs into a searchable library, running on WSL 2 / Linux.

## 1. Pipeline overview

```
PDF (papers/) → Markdown (PyMuPDF4LLM) → JSON metadata (Ollama / llama3.2, OpenAI API)
              → SQLite (data/papers.db) → static index.html → Discord notification (webhook)
```

The `paper_pipeline` DAG runs every 10 minutes (`catchup=False`, `max_active_runs=1`):

| Task | Role |
|---|---|
| `find_new_pdfs` | Lists the PDFs in `papers/` that are not yet in the database |
| `convert_pdf` | PDF → Markdown (one instance per PDF, *dynamic task mapping*) |
| `generate_metadata` | LLM call: `title`, `summary`, `keywords`, `category` (JSON, 1 retry max, field validation) |
| `store_paper` | SQLite upsert (`filename` is unique) |
| `regenerate_html` | Regenerates `index.html` (search + category filter) |
| `send_notification` | One Discord message per processed paper, after the page has been updated |

The SQLite database stays local, outside the Google Drive synced folder. Only `papers/` and `output/` are synced.

## 2. Project structure

```
.
├── dags/
│   └── paper_pipeline.py      # Single DAG (@dag / @task), orchestration only
├── src/
│   ├── config.py              # Paths and settings (environment variables)
│   ├── pdf_to_md.py           # PDF → Markdown (PyMuPDF4LLM)
│   ├── llm.py                 # OpenAI client → Ollama, JSON, retry, validation
│   ├── db_manager.py          # SQLite: papers table
│   ├── html_generator.py      # index.html generation
│   └── discord_notifier.py    # Discord webhook
├── data/                      # papers.db and markdown/ (ignored by git)
├── .env.example               # Configuration template
├── requirements.txt
└── start_airflow.sh           # Global startup script
```

Layout on the Google Drive side:

```
Google Drive/ResearchLibrary/
├── papers/    # Input PDFs
└── output/    # Generated index.html
```

## 3. Prerequisites

- Windows 10/11 with WSL 2 (Ubuntu recommended), or native Linux
- Python 3.12
- [Ollama](https://ollama.com) installed on the host with the `llama3.2` model
- Google Drive synced and accessible from WSL (e.g. `/mnt/g/My Drive/...`)
- A Discord webhook (Channel settings → Integrations → Webhooks)

## 4. Installation

```bash
# 1. Clone the repository
git clone <REPOSITORY_URL> research-library
cd research-library

# 2. Virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Airflow, using the official constraints file
AIRFLOW_VERSION=2.10.5
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# 4. Other dependencies
pip install pymupdf4llm openai requests

# 5. Configuration
cp .env.example .env
```

Edit `.env`:

```bash
export AIRFLOW_HOME="$PWD/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export PAPERS_DIR="/mnt/g/My Drive/ResearchLibrary/papers"   # to adapt
export OUTPUT_DIR="/mnt/g/My Drive/ResearchLibrary/output"   # to adapt
export DB_PATH="$PWD/data/papers.db"
export MARKDOWN_DIR="$PWD/data/markdown"
export OLLAMA_BASE_URL="http://localhost:11434/v1"           # see section 6
export OLLAMA_MODEL="llama3.2"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

`.env` is loaded by `start_airflow.sh`. For manual use: `set -a; source .env; set +a`.

## 5. ⚠️ Windows line endings (CRLF) — handle before any launch

A repository cloned or edited on Windows may contain `CRLF` line endings. Bash then reads a stray `\r`, which causes errors such as:

```
/bin/bash^M: bad interpreter: No such file or directory
$'\r': command not found
```

In `.env`, the `\r` ends up inside the variable values (invalid paths and URLs).

Convert **the startup script and `.env`**:

```bash
sudo apt install -y dos2unix
dos2unix start_airflow.sh .env
chmod +x start_airflow.sh
```

Repeat this after every modification of these files from a Windows editor. Prevention: set the editor to `LF` line endings and use `git config core.autocrlf input`.

## 6. Ollama configuration (Windows host ↔ WSL)

Ollama runs on the Windows host; Airflow runs inside WSL. By default, Ollama only listens on `127.0.0.1` on the Windows side.

**Option A — "mirrored" networking mode (recent WSL 2, recommended).** In `C:\Users\<user>\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Then run `wsl --shutdown` in PowerShell and restart WSL. `localhost` then points to the Windows host: `OLLAMA_BASE_URL="http://localhost:11434/v1"` works.

**Option B — NAT mode (default).**

1. Expose Ollama on all interfaces. In PowerShell, then restart Ollama (quit the app from the taskbar and relaunch it):
   ```powershell
   setx OLLAMA_HOST "0.0.0.0"
   ```
2. Allow port 11434 in the Windows firewall (private network).
3. In WSL, get the gateway IP (the Windows host):
   ```bash
   ip route show default | awk '{print $3}'
   ```
4. Put it in `.env`:
   ```bash
   export OLLAMA_BASE_URL="http://<GATEWAY_IP>:11434/v1"
   ```
   This IP may change every time WSL restarts.

**Check from WSL:**

```bash
curl http://<host>:11434/api/tags          # should list llama3.2
```

If Ollama is launched directly inside WSL (`ollama serve`), keep `http://localhost:11434/v1`.

Model to download: `ollama pull llama3.2`.

## 7. Launch and usage

```bash
./start_airflow.sh
```

The script:
1. activates `.venv`;
2. loads `.env`;
3. creates the required folders (`papers/`, `output/`, `data/`, `data/markdown/`, `AIRFLOW_HOME`);
4. checks that Ollama responds (warning otherwise);
5. runs `airflow standalone`.

On first startup, the generated `admin` user and its password are displayed in the terminal.

**Usage:**

1. Open http://localhost:8080 and log in.
2. Enable the `paper_pipeline` DAG (toggle).
3. Drop one or more PDFs into `papers/`.
4. Click **Trigger** to run immediately, or wait for the next scheduled run (10 min).
5. Follow the tasks in the **Graph** view; logs are available per task.
6. Result: `output/index.html` (open it in the browser) and a Discord notification.

**CLI test** (terminal with `.env` loaded and `.venv` activated):

```bash
airflow dags list-import-errors                    # check that the DAG imports
airflow dags test paper_pipeline                   # full run without the scheduler
```

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `bad interpreter` / `$'\r'` | CRLF line endings → section 5 |
| `Connection refused` to Ollama | `OLLAMA_HOST` / gateway IP / firewall → section 6 |
| DAG missing from the UI | Import error: `airflow dags list-import-errors` |
| No PDF processed | Wrong `PAPERS_DIR`, or PDF already in the database |
| No Discord message | `DISCORD_WEBHOOK_URL` empty or invalid |