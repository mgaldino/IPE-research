# IPE Breakthrough Idea Swarm

Local web app to orchestrate a swarm of AI agents that generate, vet, and package breakthrough International Political Economy (IPE) research ideas. The system focuses on design-only plans (DiD/SCM/Shift-Share or ideal points) and produces structured idea dossiers plus council-style referee memos.

## Features
- Idea dossier generation (PITCH, DESIGN, DATA_PLAN, POSITIONING, NEXT_STEPS)
- Council review workflow with gates and memo scoring
- Literature pipeline (metadata fetch, PDF ingest, assessments)
- LLM-based literature assessment (optional) using provider credentials
- Resubmission workflow with dossier version snapshots and council rounds

## Requirements
- Python 3.11+
- A local virtualenv (recommended)

## Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run the server
```bash
. .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Or, using the built-in module runner:
```bash
. .venv/bin/activate
python -m app
```

Or a one-liner helper (opens the browser):
```bash
./run_app.sh
```

Open the UI:
- http://127.0.0.1:8001/

## Quick usage
1) Unlock session (passphrase)
2) Save provider credentials (OpenAI/Anthropic/Gemini)
3) (Optional) Run LLM assessment for a literature query
4) Start swarm and review dossiers

## Run form fields
- Idea count: how many idea dossiers to generate in a single swarm run.
- Topic focus: optional hint to steer generation toward a specific IPE topic or lane.
- Use assessment idea prompts: if enabled, seed each idea from the assessment’s “idea prompts” section.

## Council personas
- Referee A: theory + positioning
- Referee B: identification
- Referee C: measurement/construct validity
- Referee D: magnitude of contribution / agenda-setting
- Referee E: data feasibility

## Tests
```bash
. .venv/bin/activate
pytest
```

## Notes
- All analysis is design-only; no execution or estimation is performed.
- LLM assessments are optional and depend on provider quotas.
