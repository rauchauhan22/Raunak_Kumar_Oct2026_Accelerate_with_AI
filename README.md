# Retail Medallion Pipeline

An agentic data engineering pipeline that ingests raw retail CSV files and processes them through a **Bronze → Silver → Gold** Medallion Architecture, using an LLM (via Groq) to dynamically generate source-to-target mappings (STTM) at each layer. Includes a Streamlit UI with human-in-the-loop (HITL) STTM approval and an HTML report generator for business-question answers.

## Project Structure

```
.
├── app.py                     # Streamlit UI — upload data, run pipeline with HITL STTM approval, ask business questions
├── orchestrator.py            # Orchestrates the 4 pipeline phases, fail-fast error handling, audit logging
├── requirements.txt           # Python dependencies
├── agents/
│   ├── profiler.py            # Phase 1: profiles raw CSV (nulls, uniques, stats) -> profile JSON
│   ├── sttm_generator.py      # Generates Bronze/Silver/Gold STTM mappings via LLM
│   ├── bronze_agent.py        # Executes Bronze layer transformations (parse_date, trim, cast, currency cleanup)
│   ├── silver_agent.py        # Executes Silver layer cleansing (drop_null, fill_unknown, fill_mean, drop_duplicates)
│   ├── gold_agent.py          # Executes Gold layer aggregations (dynamic group-by based on STTM)
│   └── reporter.py            # Loads Gold parquet into DuckDB, runs LLM-generated SQL, builds HTML report
├── core/
│   ├── connection_req.py      # Groq/OpenAI-compatible client connection (reads GROQ_API_KEY from env)
│   └── audit.py                # Simple audit logger -> traces/pipeline.log
├── data/
│   ├── raw/                   # Uploaded/raw input CSVs
│   ├── bronze/                # Bronze parquet + generated bronze STTM CSVs
│   ├── silver/                # Silver parquet + generated silver STTM CSVs
│   └── gold/                  # Gold parquet tables (aggregated, queryable via DuckDB)
├── reports/                    # Generated HTML reports (question + answer)
└── traces/                     # Pipeline audit log (traces/pipeline.log)
```

## Pipeline Phases

1. **Phase 1 — Profile & Bronze STTM**: Profiles the raw CSV and asks the LLM to generate a Bronze-layer source-to-target mapping (parse dates, strip currency symbols, trim whitespace, cast types).
2. **Phase 2 — Bronze Ingestion & Silver STTM**: Applies the approved Bronze STTM to produce a Bronze parquet file, then generates a Silver-layer STTM (null handling, deduplication).
3. **Phase 3 — Silver Ingestion & Gold STTM**: Applies the approved Silver STTM to cleanse the data, then generates a Gold-layer STTM (aggregations/group-bys).
4. **Phase 4 — Gold Materialization**: Applies the approved Gold STTM to produce queryable Gold parquet tables.

Each STTM (Bronze/Silver/Gold) is reviewed and approved by a human in the Streamlit UI before the next phase executes.

## Setup

```powershell
pip install -r requirements.txt
$env:GROQ_API_KEY = "your-groq-api-key"
```

## Running the App

```powershell
py -m streamlit run app.py
```

Then in the browser:
1. Upload a raw CSV (e.g., `sales.csv`, `products.csv`).
2. Click **Start Pipeline** and approve each generated STTM as it's produced.
3. Once Gold tables are ready, ask a business question (e.g., "Which product has the highest sales?").
4. Download the generated HTML report of the question + answer.

## Running via CLI (no HITL approval)

```powershell
py orchestrator.py
```

Runs all 4 phases end-to-end for the hardcoded object in `orchestrator.py`'s `main()`.

## Security Notes

- `GROQ_API_KEY` is read from the environment — never hardcoded in source.
- `.gitignore` excludes `.env`, virtual environments, and Streamlit secrets from version control.

## Observability

- `core/audit.py` logs phase start/complete/fail events to `traces/pipeline.log` for every pipeline run.
