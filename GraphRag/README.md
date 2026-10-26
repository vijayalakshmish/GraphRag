# GraphRAG Research Intelligence

A GraphRAG prototype for answering technical engineering questions using
relationships between concepts and information retrieved from source documents.

## Problem

Traditional retrieval can find relevant passages, but technical questions
often involve relationships between several concepts. This prototype explores
how a knowledge graph and community reports can support multi-hop,
evidence-oriented answers.

## Architecture

1. Three technical text documents provide the source knowledge.
2. GraphRAG Standard indexing extracts entities and relationships.
3. Community detection and reports organize related concepts.
4. GraphRAG Local Search combines graph context and source text to answer
   a natural-language question.
5. Local phrase checks provide an initial grounding sanity check.

## Demonstrated question

"How do retries, exponential backoff, jitter, and circuit breakers help
improve service reliability?"

The prototype returned an answer connecting retries, exponential backoff,
jitter, circuit breakers, transient failures, and reliability, with GraphRAG
data references.

## Current validation

- Five selected answer claims checked against the original text documents.
- Five of five selected phrases were found.
- Relationship endpoint integrity and entity descriptions were checked.
- Graph quality findings are documented in `GRAPH_QUALITY_REPORT.md`.

These checks are preliminary. Phrase matching does not establish full semantic
correctness, citation precision, or completeness.

## Reproduce

Run in Google Colab with a compatible Python environment and GraphRAG
dependencies. Configure a supported model provider and credentials privately
in the runtime; never commit API keys.

The experiment's configuration and indexed files are in `standard_experiment/`.
Review the installed GraphRAG version's CLI and configuration before rerunning
indexing. Indexing and model calls may consume provider quota or incur charges.

## Limitations

- The prototype uses only three small technical documents.
- Evaluation currently covers one Local Search question and five phrase checks.
- No broad benchmark, independent human evaluation, latency benchmark, or
  reliable cost benchmark has been completed.
- Results may vary with model, configuration, and source documents.

## Next improvements

1. Build a diverse, manually reviewed question-and-evidence test set.
2. Measure answer correctness, citation support, and retrieval relevance.
3. Test difficult questions, unanswerable questions, and conflicting evidence.
4. Benchmark latency and actual provider usage under a controlled budget.
5. Expand the corpus only after the evaluation procedure is established.
