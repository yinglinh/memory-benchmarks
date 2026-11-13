# Memory Benchmarks

Open-source evaluation suite to run benchmarks on memory-augmented LLM systems. Currently supports the [Mem0](https://github.com/mem0ai/mem0) Cloud and OSS versions to measure memory recall, extraction quality, and retrieval accuracy.

## FTEC5660 Reproducibility Study

This repository also contains a reproduction study and an experimental modification of Mem0 using the LOCOMO benchmark, conducted as part of FTEC5660.

The project consists of two stages:

1. **Reproduction:** Evaluate Mem0 OSS using LOCOMO Conversation 0, which contains 152 evaluation questions.
2. **Experimental Modification:** Investigate the effect of retrieval depth on steady-state retrieval latency by comparing Top-K = 200 and Top-K = 50.

The experimental environment uses:

- **Memory system:** Mem0 OSS
- **LLM provider:** DeepSeek
- **LLM model:** `deepseek-chat`
- **Embedding model:** `all-MiniLM-L6-v2`
- **Embedding provider:** Hugging Face
- **Vector database:** Qdrant
- **Deployment:** Docker Compose

The original Memory Benchmarks framework and its other benchmark implementations are retained. The additional instructions below describe how to reproduce the experiments conducted for this study.

Detailed methodology, analysis, and comparison with the original paper's reported results are provided in the accompanying project report.

## Benchmarks

| Benchmark | Dataset | Questions | What it tests |
|-----------|---------|-----------|---------------|
| **LOCOMO** | 10 multi-session dialogues | ~300 | Factual recall, temporal reasoning, multi-hop inference |
| **LongMemEval** | 500 diverse questions, 6 types | 500 | Long-term memory across information extraction, temporal, and multi-session reasoning |
| **BEAM** | 100 conversations per size bucket (100K–10M tokens) | 2,000+ | Real-world memory retrieval across 10 memory ability types |

## Quick Start

```bash
git clone https://github.com/mem0ai/memory-benchmarks.git
cd memory-benchmarks
pip install -r requirements.txt
```

### Option A: Mem0 Cloud

No Docker required. You need a [Mem0 API key](https://app.mem0.ai) and an OpenAI API key (for the answerer/judge LLM).

```bash
# Set your keys
export MEM0_API_KEY=m0-your-key
export OPENAI_API_KEY=sk-your-key

# Run a benchmark
python -m benchmarks.locomo.run \
  --project-name my-first-test \
  --backend cloud \
  --mem0-api-key $MEM0_API_KEY

# LongMemEval (500 questions)
python -m benchmarks.longmemeval.run \
  --project-name my-first-test \
  --backend cloud \
  --mem0-api-key $MEM0_API_KEY \
  --all-questions

# BEAM (configurable size)
python -m benchmarks.beam.run \
  --project-name my-first-test \
  --backend cloud \
  --mem0-api-key $MEM0_API_KEY \
  --chat-sizes 100K --conversations 0-9
```

### Option B: Mem0 OSS (Self-Hosted)

Requires Docker and Docker Compose. This starts a local Mem0 server backed by Qdrant.

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

docker compose up -d
# Mem0 server: http://localhost:8888
# Qdrant:      http://localhost:6333
```

Then run benchmarks against your local server:

```bash
# LOCOMO (fastest — ~300 questions, 10 conversations)
python -m benchmarks.locomo.run --project-name my-first-test

# LongMemEval (500 questions)
python -m benchmarks.longmemeval.run --project-name my-first-test --all-questions

# BEAM (configurable size)
python -m benchmarks.beam.run --project-name my-first-test --chat-sizes 100K --conversations 0-9
```

By default, the OSS server uses OpenAI for fact extraction (`gpt-4o-mini`) and embeddings (`text-embedding-3-small`). See [Custom Models](#custom-models) for using Azure, Ollama, or other providers.

### View results in the UI

```bash
npm install
npm run dev -- -p 3001
# Open http://localhost:3001
```

The web UI lets you browse results, inspect per-question evaluations with retrieval details, view logs, and compare runs.

## FTEC5660 Installation and Reproduction Guide

For the FTEC5660 reproduction study, use the personal repository URL and the dedicated setup instructions provided in this section. The original Quick Start section above describes the general usage of the upstream Memory Benchmarks project.

This section provides the environment setup, configuration, and execution instructions for reproducing the FTEC5660 experiments.

All commands below should be executed from the root directory of the cloned repository, unless otherwise specified.

### 1. Prerequisites

The following software and resources are required:

- Python 3.10 or a compatible version
- Git
- Docker Desktop with Docker Compose V2
- A valid DeepSeek API key
- Internet access for downloading dependencies and the embedding model

The original experimental environment used Python 3.10.9 on macOS.

### 2. Clone the Repository

Clone the complete Mem0 project, including the customized Memory Benchmarks evaluation submodule:

```bash
git clone --recurse-submodules https://github.com/yinglinh/mem0.git
cd mem0
```

The `--recurse-submodules` option automatically downloads the Memory Benchmarks repository into the `evaluation/` directory.

Navigate to the evaluation directory:

```bash
cd evaluation
```

All subsequent Python environment setup, configuration, and experiment commands should be executed from this directory.

**Note:** The evaluation repository is also available separately at https://github.com/yinglinh/memory-benchmarks.

### 3. Set Up the Python Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Install the required dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify the LOCOMO benchmark command:

```bash
python -m benchmarks.locomo.run --help
```

The command should display the available benchmark options.

### 4. Configure Environment Variables

Create a local `.env` file:

```bash
cp .env.example .env
```

Open `.env` and configure the credentials required for the DeepSeek API.

For the OpenAI-compatible benchmark client, use:

```env
OPENAI_API_KEY=YOUR_DEEPSEEK_API_KEY
OPENAI_BASE_URL=https://api.deepseek.com
```

Replace `YOUR_DEEPSEEK_API_KEY` with your own valid API key.

**Important configuration notes:**

- `OPENAI_API_KEY` contains the DeepSeek API key, not an OpenAI API key.
- `OPENAI_BASE_URL` directs the benchmark's OpenAI-compatible client to the DeepSeek API.
- The Mem0 server uses the DeepSeek provider directly through `docker/mem0/config.yaml`.
- The Mem0 configuration references `${OPENAI_API_KEY}` for authentication and specifies `https://api.deepseek.com` as its DeepSeek base URL.

The API key must remain private. Do not commit the `.env` file to GitHub.

### 5. Configure the Mem0 OSS Server

The project uses a self-hosted Mem0 OSS server with Qdrant as its vector database.

The custom server configuration is located at:

```text
docker/mem0/config.yaml
```

The configuration includes:

| Component | Setting |
|---|---|
| LLM provider | DeepSeek |
| LLM model | `deepseek-chat` |
| Embedding provider | Hugging Face |
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding dimensions | 384 |
| Vector database | Qdrant |
| Qdrant collection | `locomo_memories` |

The configuration file is mounted into the Mem0 container through:

```text
docker-compose.override.yml
```

This override file is included in the repository, so no additional manual volume configuration is required.

### 6. Start the Mem0 and Qdrant Services

Ensure that Docker Desktop is running.

All commands below should be executed from the root directory of the Memory Benchmarks repository. When this repository is included as a submodule in the full Mem0 project, this corresponds to the `evaluation/` directory.

```bash
docker compose up -d --build
```

This starts the following services:

| Service | Local endpoint |
|---|---|
| Mem0 OSS Server | `http://localhost:8888` |
| Qdrant | `http://localhost:6333` |

Docker Compose manages two services named `mem0` and `qdrant`. The `mem0` container runs the Mem0 FastAPI server, while the `qdrant` container provides vector storage for the memory system.

Check the container status:

```bash
docker compose ps
```

Verify that the Mem0 server is healthy:

```bash
curl http://localhost:8888/health
```

A successful response should contain:

```json
{
  "status": "ok",
  "llm": "deepseek",
  "embedder": "huggingface"
}
```

The response formatting may vary.

If the server fails to start, inspect its logs:

```bash
docker compose logs --tail=100 mem0
```

Do not proceed until the Mem0 server is healthy.

---

### 7. Run the LOCOMO Reproduction Experiment

The reproduction experiment uses LOCOMO Conversation 0, containing 152 evaluation questions.

Ensure that the Python virtual environment is activated and the Mem0 server is running.

Execute:

```bash
python -m benchmarks.locomo.run \
  --project-name mem0-locomo-reproduction \
  --backend oss \
  --answerer-model deepseek-chat \
  --judge-model deepseek-chat \
  --provider openai \
  --conversations 0 \
  --top-k 200 \
  --top-k-cutoffs 10,20,50,200 \
  --max-workers 1 \
  --rpm 20
```

This configuration:

- Uses the self-hosted Mem0 OSS backend.
- Processes LOCOMO Conversation 0.
- Uses DeepSeek Chat for answer generation and evaluation.
- Retrieves up to 200 memories.
- Evaluates retrieval at cutoffs of 10, 20, 50, and 200.
- Limits execution to one worker and 20 requests per minute.

Allow the benchmark to complete before starting the steady-state experiment.

#### Expected Output

The question-level prediction and retrieval records are saved under:

```text
results/locomo/predicted_mem0-locomo-reproduction/
```

The benchmark also generates evaluation result files under:

```text
results/locomo/
```

The committed preliminary accuracy result is:

```text
results/locomo/locomo_results_20261111_153209.json
```

New runs may generate files with different timestamps.

**Important:** The LOCOMO run also performs memory ingestion. This step is necessary when setting up a fresh environment because the Qdrant database is not included in the GitHub repository. The committed JSON question records do not contain the persistent vector database itself.

---

### 8. Run the Steady-State Retrieval Efficiency Experiment

The modified experiment is implemented in:

```text
retrieval_efficiency_steady_state.py
```

It compares retrieval latency between Top-K = 200 and Top-K = 50.

#### Prerequisites

Before running the script, ensure that:

1. The Mem0 OSS server is running.
2. The LOCOMO Conversation 0 memories have been ingested into Mem0.
3. The 152 question records are available in:

```text
results/locomo/predicted_mem0-locomo-reproduction/
```

The script verifies that exactly 152 question records are available and that they share the same user ID.

#### Execute the Experiment

From the repository root directory, run:

```bash
python retrieval_efficiency_steady_state.py
```

No additional command-line arguments are required.

#### Experimental Procedure

The script automatically performs the following steps:

1. **Warm-up:** Executes searches using all 152 questions for both Top-K configurations. Warm-up measurements are excluded from the formal results.
2. **Formal trials:** Conducts five trials for Top-K = 200 and five trials for Top-K = 50.
3. **Counterbalanced schedule:** Alternates the execution order to reduce potential time-order bias.
4. **Latency measurement:** Records individual retrieval latency for every question.

The total number of formal measurements is:

| Configuration | Trials | Questions per trial | Total measurements |
|---|---:|---:|---:|
| Top-K = 200 | 5 | 152 | 760 |
| Top-K = 50 | 5 | 152 | 760 |

The experiment calculates:

- Mean latency
- Latency variance
- P50 latency
- P95 latency

Exact numerical results may vary between runs due to differences in LLM API behavior, service conditions, and execution environments. The reproduction focuses on maintaining consistent experimental configurations and procedures rather than guaranteeing identical numerical outputs across all runs.

#### Generated Output Files

The experiment produces two JSON files:

**Raw measurements:**

```text
results/locomo/retrieval_efficiency_steady_state_raw.json
```

Contains individual latency measurements, trial information, and the execution schedule.

**Aggregated summary:**

```text
results/locomo/retrieval_efficiency_steady_state_summary.json
```

Contains the aggregated statistical results for both Top-K configurations.

**Important:** The script refuses to overwrite existing output files. If conducting a new run, move the existing files outside `results/locomo/` first:

```bash
mkdir -p ../previous-steady-state-results

mv results/locomo/retrieval_efficiency_steady_state_raw.json \
   ../previous-steady-state-results/

mv results/locomo/retrieval_efficiency_steady_state_summary.json \
   ../previous-steady-state-results/
```

Then execute the experiment again.

---

### 9. Reproducing the Experiments from a Fresh Environment

For a complete reproduction from a fresh clone, follow this sequence:

1. Clone the repository.
2. Install Python dependencies and activate the virtual environment.
3. Configure the DeepSeek API credentials.
4. Start Docker and the Mem0/Qdrant services.
5. Run the LOCOMO benchmark to ingest the conversation memories and generate the question-level evaluation records.
6. Run `retrieval_efficiency_steady_state.py`.
7. Inspect the generated raw and summary JSON files.

The LOCOMO benchmark and steady-state experiment must use the same Mem0 environment and populated memory collection.

The committed question records and previous experimental results are provided for reference. They do not replace the memory ingestion required for a fresh Qdrant database.

### 10. Stop the Services

After completing the experiments, stop the containers:

```bash
docker compose down
```

This preserves the persistent Docker volumes.

Avoid using:

```bash
docker compose down -v
```

unless you intentionally want to delete the stored Qdrant and Mem0 history data.

## How It Works

Each benchmark script runs a three-stage pipeline:

```
Ingest → Search → Evaluate
```

1. **Ingest**: Conversations are chunked and added to Mem0. The system extracts facts, embeds them, and builds entity links.
2. **Search**: For each question, the system queries Mem0. Results are scored using semantic similarity + BM25 + entity boost.
3. **Evaluate**: An LLM generates an answer from retrieved memories, then a judge LLM scores correctness against ground truth.

## Configuration

### Benchmark options

All benchmarks accept these common flags:

```
--project-name NAME        Run identifier (required)
--answerer-model MODEL     LLM for answer generation (default: gpt-4o)
--judge-model MODEL        LLM for judging (default: gpt-4o)
--provider PROVIDER        LLM provider: openai, anthropic, azure (default: openai)
--top-k N                  Retrieved memories count (default: 200)
--top-k-cutoffs LIST       Evaluate at multiple cutoffs (default: 10,20,50,200)
--predict-only             Stop after search, skip answer+judge
--evaluate-only            Skip ingest+search, evaluate existing results
--resume                   Resume from checkpoint
--backend oss|cloud        Mem0 backend (default: oss)
--mem0-host URL            Mem0 server URL (default: http://localhost:8888)
```

### Custom Models

By default, the Mem0 server uses OpenAI for fact extraction (`gpt-4o-mini`) and embeddings (`text-embedding-3-small`). You can change this by mounting a custom config file.

**Step 1**: Copy an example config:

```bash
cp configs/azure-openai.yaml mem0-config.yaml
# or: cp configs/ollama.yaml mem0-config.yaml
```

**Step 2**: Edit `mem0-config.yaml` with your model details.

**Step 3**: Uncomment the volume mount in `docker-compose.yml`:

```yaml
volumes:
  - mem0_history:/app/history
  - ./mem0-config.yaml:/app/config.yaml:ro   # <-- uncomment this line
```

**Step 4**: Restart:

```bash
docker compose down && docker compose up -d
```

See `configs/` for examples:
- `configs/openai.yaml` — OpenAI (default)
- `configs/azure-openai.yaml` — Azure OpenAI
- `configs/ollama.yaml` — Fully local with Ollama (no API keys)

## Results

### Mem0 Platform

Results using the Mem0 managed platform with the v3 memory pipeline.

#### LongMemEval

| Metric | Top 200 | Top 50 |
|--------|---------|--------|
| **Overall** | **94.4%** (472/500) | **94.8%** (474/500) |

<details>
<summary>LongMemEval breakdown by question type</summary>

| Question Type | Top 200 | Top 50 |
|---------------|---------|--------|
| knowledge-update | 93.6% (73/78) | 93.6% (73/78) |
| multi-session | 88.0% (117/133) | 93.2% (124/133) |
| single-session-assistant | 98.2% (55/56) | 98.2% (55/56) |
| single-session-preference | 96.7% (29/30) | 93.3% (28/30) |
| single-session-user | 98.6% (69/70) | 98.6% (69/70) |
| temporal-reasoning | 97.0% (129/133) | 94.0% (125/133) |

</details>

#### LoCoMo

| Metric | Top 200 | Top 50 |
|--------|---------|--------|
| **Overall** | **92.5%** (1425/1540) | **91.8%** (1414/1540) |

<details>
<summary>LoCoMo breakdown by question type (avg across top_10/20/50/200)</summary>

| Question Type | Avg (Top 10–200) |
|---------------|------------------|
| single-hop | 91.2% |
| multi-hop | 91.3% |
| open-domain | 72.7% |
| temporal | 92.0% |

</details>

#### BEAM

| Dataset | Top 200 | | Top 50 | |
|---------|---------|---|--------|---|
| | **Pass Rate** | **Avg Score** | **Pass Rate** | **Avg Score** |
| **BEAM 1M** (700 questions) | **70.1%** (491/700) | 0.641 | **67.1%** (470/700) | 0.604 |
| **BEAM 10M** (200 questions) | **50.5%** (101/200) | 0.486 | **45.5%** (91/200) | 0.413 |

<details>
<summary>BEAM breakdown by memory ability type</summary>

**BEAM 1M (Top 200)**

| Ability | Avg Score | Pass Rate |
|---------|-----------|-----------|
| preference_following | 0.883 | 68/70 |
| instruction_following | 0.852 | 62/70 |
| information_extraction | 0.700 | 53/70 |
| multi_session_reasoning | 0.652 | 52/70 |
| knowledge_update | 0.650 | 46/70 |
| summarization | 0.635 | 48/70 |
| temporal_reasoning | 0.618 | 47/70 |
| event_ordering | 0.536 | 42/70 |
| abstention | 0.525 | 39/70 |
| contradiction_resolution | 0.357 | 34/70 |

**BEAM 10M (Top 200)**

| Ability | Avg Score | Pass Rate |
|---------|-----------|-----------|
| preference_following | 0.904 | 19/20 |
| instruction_following | 0.825 | 18/20 |
| knowledge_update | 0.750 | 16/20 |
| information_extraction | 0.562 | 11/20 |
| summarization | 0.469 | 11/20 |
| abstention | 0.400 | 8/20 |
| contradiction_resolution | 0.325 | 5/20 |
| multi_session_reasoning | 0.261 | 6/20 |
| event_ordering | 0.202 | 3/20 |
| temporal_reasoning | 0.163 | 4/20 |

</details>

### OSS with Different Extraction Models

LongMemEval results using the self-hosted Mem0 OSS pipeline with different LLMs for memory extraction. All runs use the same embedder (Qwen 600M via SageMaker), the same Qdrant vector store, and GPT-5 as the answerer and judge.

| Extraction Model | Overall | SS-User | SS-Asst | SS-Pref | Knowledge Update | Temporal Reasoning | Multi-Session |
|-----------------|---------|---------|---------|---------|------------------|-------------------|---------------|
| **GPT-5** | **91.0%** | 95.7% | 92.9% | 93.3% | 91.0% | 94.7% | 83.5% |
| **GPT-OSS-120B** | **89.8%** | 95.7% | 96.4% | 93.3% | 89.5% | 80.5% | 79.7% |
| **Llama 4 Maverick** | **88.6%** | 97.1% | 75.0% | 93.3% | 93.6% | 90.2% | 84.2% |
| **Gemma 4 31B** | **88.6%** | 95.7% | 83.9% | 93.3% | 94.9% | 91.7% | 78.9% |

Full per-question evaluation results are available in [`results/platform/`](results/platform/) and [`results/oss/`](results/oss/).

## A Note on Benchmark Scores

**Benchmark scores are not absolute numbers.** They depend heavily on:

- **Embedding model quality** — A larger, more capable embedding model will produce better retrieval, directly improving scores. The default `text-embedding-3-small` (1536 dims) is cost-efficient but not state-of-the-art.
- **LLM capability** — Both the fact extraction model (used during ingestion) and the judge model (used during evaluation) affect results. A stronger extraction model captures more nuanced facts; a stronger judge is more accurate in its verdicts.
- **Retrieval depth** — Higher `top-k` values give the system more chances to find relevant memories, but may also introduce noise.

When comparing configurations, keep all other variables constant and change only what you're testing. The default OpenAI setup provides a reproducible baseline — your scores will likely improve with stronger models.

## Project Structure

```
memory-benchmarks/
├── benchmarks/              Python evaluation scripts
│   ├── common/              Shared: Mem0 client, LLM client, metrics, utils
│   ├── locomo/               LOCOMO benchmark
│   ├── longmemeval/          LongMemEval benchmark
│   └── beam/                 BEAM benchmark
│
├── configs/                  Example Mem0 server configurations
│
├── docker/
│   └── mem0/                 Mem0 server (Dockerfile, FastAPI app,
│                             and config.yaml)
│
├── docker-compose.yml        Main Docker Compose configuration
├── docker-compose.override.yml
│                             Custom Mem0 OSS configuration for this study
│
├── retrieval_efficiency_steady_state.py
│                             Steady-state retrieval efficiency experiment
│
├── .env.example              Example environment variables
├── requirements.txt          Python dependencies
│
├── src/                      Next.js frontend
│   ├── app/                  Pages and API routes
│   ├── components/            UI components
│   └── lib/                  Database, adapters, executor
│
├── results/                  Benchmark outputs
│                             (most runtime files are gitignored;
│                             selected reproduction data and results
│                             are included in the repository)
│
└── datasets/                 Auto-downloaded datasets (gitignored)
```

For this FTEC5660 study, selected LOCOMO input records and experimental result files are included in the repository for reference and reproducibility. These include the question-level JSON records, preliminary accuracy benchmark results, and steady-state retrieval efficiency measurements.

## License

Apache 2.0
