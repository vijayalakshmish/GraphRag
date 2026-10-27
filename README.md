# 🕸️ GraphRAG Research Intelligence

A small, learning-focused prototype of **GraphRAG** (graph-based retrieval-augmented generation) built with Microsoft's open-source [GraphRAG](https://github.com/microsoft/graphrag) framework and the **Gemini API**. It turns a few technical documents into a knowledge graph, groups related entities into communities, and answers questions with citations back to the source text. An ontology file describes the kinds of things the graph should contain, and the extracted graph is checked against it.

> **Status:** prototype on a very small corpus. See [Limitations](#limitations) before drawing conclusions from the results.

---

## What it does

```
documents ──▶ text chunks ──▶ entities + relationships (LLM extraction)
                                      │
                                      ▼
                        knowledge graph ──▶ communities ──▶ community reports
                                      │
question ──▶ local search (entities, relationships, source passages) ──▶ answer with [Data: ...] citations
```

1. **Index:** GraphRAG splits the documents into chunks, asks the model to extract entities and relationships, builds a graph, finds communities, and writes a report for each.
2. **Query:** local search finds the entities related to a question, collects their relationships and source passages, and has the model answer from that context only.
3. **Inspect:** the output tables (entities, relationships, communities, reports, text units) can be read directly, so every answer can be traced to its evidence.
4. **Check against an ontology:** `ontology.yaml` declares classes, relationship types and validation rules. The extracted entity types are audited against it.

## Why a graph?

Plain RAG retrieves passages that look similar to the question. A knowledge graph also stores **how things connect**, so the system can follow relationships and summarize groups of related concepts. This project is a way to study that idea and its costs (extra indexing calls, latency). It does **not** yet include a plain-RAG baseline, so it does not show that the graph approach is better.

---

## Results so far

Index of the three-document experiment (`standard_experiment/`):

| Item | Count |
|---|---|
| Entities | 29 |
| Relationships | 26 |
| Communities | 5 |
| Community reports | 5 |
| Text units (chunks) | 5 |

Hand-graded benchmark (8 questions, 5 answerable and 3 unsupported):

| Result | Count |
|---|---|
| Pass | 6 |
| Partial | 2 |
| Fail | 0 |

Unsupported questions (for example, a cloud bill or a private phone number that the documents do not contain) were answered with "I do not know" instead of an invented answer. Average query time was about 13 seconds across 7 recorded queries. A second set of 5 evaluation cases is recorded in `EVALUATION_RESULTS.md`.

Entity types found: resilience pattern, system component, metric, engineering concept, observability signal, method, reliability target.

Grading was done by hand against key facts in the source text, so treat the scores as indicative.

---

## Project structure

| Path | Purpose |
|---|---|
| `Graphrag.ipynb` | The Colab notebook that built and tested everything |
| `input/` | The three source documents (`document_01.txt` to `document_03.txt`) |
| `settings.yaml` | GraphRAG configuration (models, chunking, storage). Reads the key from an environment variable. |
| `prompts/` | Extraction, community-report and search prompts |
| `ontology.yaml` | Ontology: 11 classes, 6 relationship types, 5 validation rules |
| `standard_experiment/` | Isolated run with its own input, output, logs, cache and vector store |
| `evaluation_questions.csv` | Benchmark questions with expected behaviour (answer or abstain) |
| `baseline_scorecard.csv`, `standard_index_scorecard.csv` | Scorecards for the two index builds |
| `EVALUATION_REPORT.md`, `EVALUATION_RESULTS.md` | Evaluation write-ups |
| `ONTOLOGY_VALIDATION_REPORT.md` | Ontology schema and conformance check |
| `app.py` | Streamlit demo with a password gate |
| `gradio_app.py` | Gradio demo |
| `requirements.txt` | Pinned dependencies |

Generated folders (`output/`, `logs/`, `cache/`, `lancedb/`, `*.parquet`) are listed in `.gitignore`, so the repository does **not** contain a ready-made index. You need to build it (see below).

---

## Getting started

### Requirements
- Python 3.10+ (developed in Google Colab)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- The models used in the experiment: `gemini-3.5-flash-lite` for completions and `gemini-embedding-001` for embeddings (3072-dimension vectors). Model names change over time, so edit them in `settings.yaml` if they are no longer available.

### Install
```bash
pip install -r requirements.txt
pip install streamlit        # only needed for app.py
```
In Colab, restart the runtime after installing so the pinned NumPy and pandas versions are the ones actually loaded.

### Set your key (never put it in a file)
In Colab, add a secret named `GEMINI_API_KEY` and turn on notebook access, then expose it as an environment variable. Elsewhere:
```bash
export GEMINI_API_KEY="your-key-here"
```
`settings.yaml` refers to the key as `${GEMINI_API_KEY}`, so the value never appears in the file.

### Build the index
This step makes many model calls and uses your API quota.
```bash
graphrag index --root ./standard_experiment --method standard
```
The free tier can return a rate-limit error (HTTP 429). If that happens, wait and try again.

### Ask questions
Use the query command with the local search method, and see its options with:
```bash
graphrag query --help
```
Local search suits specific questions about entities and how they relate.

### Run the demo apps
```bash
streamlit run app.py        # asks for a demo password; see the top of app.py for how it is set
python gradio_app.py
```
Both load the saved index and do not rebuild it. If you share a public link to a demo, remember that every question uses **your** API quota.

---

## Known issues

- **Duplicate entity:** the graph contains both `CIRCUIT BREAKER` and `CIRCUIT BREAKERS`. The singular form is one of 3 entities with no relationships (the others are `SERVICE A` and `SERVICE-LEVEL OBJECTIVES`, and `DISTRIBUTED SYSTEM` was reported disconnected in the same check). The duplicate check in the notebook did not catch plurals.
- **Tiny chunks:** the experiment used 100-token chunks with 10 tokens of overlap (the default is 1200), chosen to force several chunks from a very small corpus. Some chunks end in the middle of a sentence.
- **Ontology coverage:** the conformance audit compares entity **types**. The framework's extraction does not enforce relationship types or the other rules in `ontology.yaml`.
- **Version pins:** `requirements.txt` was generated in Colab. Check it in a fresh environment before relying on it.

## Limitations

- **Very small corpus:** three documents, about 323 tokens, five chunks. At this size a model could read everything at once, so the results say little about how GraphRAG behaves on real collections.
- **No baseline:** there is no plain-RAG comparison and no multi-hop question set yet, so this repository does not show whether the graph improves answers.
- **Hand-graded, 8 questions:** the pass rate is a rough indicator only.
- **Cost and latency:** indexing makes many model calls, and a query took about 13 seconds.
- **Prototype security:** the demo password gate is basic and not suitable for sensitive data.

## Ideas for next steps

- Add a plain-RAG baseline and a larger corpus with multi-hop questions, and compare both on the same questions.
- Merge near-duplicate entities and re-run the quality report.
- Enforce relationship types and rules from the ontology, not only entity types.
- Try global search for broad questions and compare it with local search.
- Add a larger evaluation set and a scripted evaluation run.

---

## Security

- Never commit API keys, `.env` files or notebook outputs that print them. If a key is ever shown or committed, **revoke it in AI Studio and create a new one**; removing it from the file is not enough because it stays in the Git history.
- Clear notebook outputs and remove temporary public share links before publishing.

## Notes

This is a learning project. The code and configuration were developed with AI assistance and then run, inspected and evaluated step by step in the notebook.

## Acknowledgements

Built on Microsoft's [GraphRAG](https://github.com/microsoft/graphrag) and the Gemini API. Check each project's license before reusing their code or prompts.
