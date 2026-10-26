# GraphRAG Prototype Evaluation Report

**Evaluation date:** 2026-10-26
**Index:** `standard_experiment`
**Search mode:** GraphRAG Local Search

## 1. Objective

Check whether the indexed prototype can answer a technical reliability question
and whether selected claims have supporting wording in the source documents.

## 2. Index and graph checks

The latest inspected index contained:

- Entities: 25
- Relationships: 25
- Communities: 4
- Community reports: 4
- Text units: 5
- Source documents: 3

Earlier inspection cells showed different counts; the values above refer to the
latest inspected output. Recheck the files if the index is regenerated.

Previously performed integrity checks found no missing relationship endpoints
and no empty entity descriptions. The graph-quality report also identified
potential disconnected concepts and a singular/plural naming variation for
circuit breaker entities.

## 3. Query tested

> How do retries, exponential backoff, jitter, and circuit breakers help
> improve service reliability?

Local Search returned a multi-paragraph answer that discussed transient
failures, retry amplification, exponential backoff, jitter, and circuit breakers.
The response included GraphRAG data references to reports, entities,
relationships, and source material.

## 4. Phrase-level evidence checks

| Selected claim | Result |
|---|---|
| Retries improve reliability during transient failures | PASS |
| Uncontrolled retries can amplify outages | PASS |
| Exponential backoff reduces synchronized retries | PASS |
| Circuit breakers prevent repeated calls to failing dependencies | PASS |
| Circuit breaker threshold allows temporary blocking | PASS |

**Result: 5/5 selected phrase checks passed.**

These checks searched the original text files for specified phrases. They are
a lightweight lexical check, not a full semantic entailment or citation audit.

## 5. What this evaluation establishes

- The indexing pipeline produced graph and community artifacts.
- A Local Search query returned a coherent technical answer.
- The five selected claims had matching wording in the source corpus.

## 6. What it does not establish

- General answer accuracy across different questions.
- That each individual citation supports the exact sentence beside it.
- Reliable performance on ambiguous, unanswerable, or conflicting questions.
- Production-scale latency, cost, or scalability.
- Superiority over vector-only RAG or another baseline.

## 7. Next evaluation stage

Create a manually reviewed test set with answerable, multi-hop, and
unanswerable questions. For each question, record expected evidence passages.
Score answer correctness, citation support, retrieval relevance, and abstention
when evidence is insufficient. Run further model queries only after confirming
that the budget and provider quota allow them.
