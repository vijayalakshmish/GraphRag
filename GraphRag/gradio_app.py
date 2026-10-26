import asyncio
import os
from pathlib import Path

import gradio as gr
import numpy as np
import pandas as pd

from graphrag.config.load_config import load_config
from graphrag.query.factory import get_local_search_engine
from graphrag.query.input.loaders.dfs import (
    read_entities,
    read_relationships,
    read_communities,
    read_community_reports,
    read_text_units,
)
from graphrag_vectors import create_vector_store


ROOT = Path(__file__).resolve().parent
EXPERIMENT = ROOT / "standard_experiment"
OUTPUT = EXPERIMENT / "output"


def normalize_covariates(value):
    if value is None:
        return {}
    if isinstance(value, np.ndarray) and value.size == 0:
        return {}
    if isinstance(value, float) and pd.isna(value):
        return {}
    return value


def load_project():
    required = [
        "entities.parquet",
        "relationships.parquet",
        "communities.parquet",
        "community_reports.parquet",
        "text_units.parquet",
    ]
    missing = [name for name in required if not (OUTPUT / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Required GraphRAG index files are missing: " + ", ".join(missing)
        )

    config = load_config(root_dir=EXPERIMENT)

    entities_df = pd.read_parquet(OUTPUT / "entities.parquet")
    relationships_df = pd.read_parquet(OUTPUT / "relationships.parquet")
    communities_df = pd.read_parquet(OUTPUT / "communities.parquet")
    reports_df = pd.read_parquet(OUTPUT / "community_reports.parquet")
    text_units_df = pd.read_parquet(OUTPUT / "text_units.parquet")

    text_units_df = text_units_df.copy()
    if "covariate_ids" in text_units_df.columns:
        text_units_df["covariate_ids"] = (
            text_units_df["covariate_ids"].apply(normalize_covariates)
        )

    entities = read_entities(entities_df)
    relationships = read_relationships(relationships_df)
    communities = read_communities(communities_df)
    reports = read_community_reports(reports_df)
    text_units = read_text_units(text_units_df)

    vector_config = config.vector_store
    entity_schema = vector_config.index_schema["entity_description"]
    vector_store = create_vector_store(vector_config, entity_schema)
    vector_store.connect()

    engine = get_local_search_engine(
        config=config,
        reports=reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        covariates={},
        response_type="multiple paragraphs",
        description_embedding_store=vector_store,
    )

    return engine, vector_store, {
        "entities": len(entities),
        "relationships": len(relationships),
        "communities": len(communities),
        "community_reports": len(reports),
        "text_units": len(text_units),
    }


ENGINE, VECTOR_STORE, INDEX_COUNTS = load_project()


SOURCE_TITLES = {
    "0": "Distributed Systems: Service Reliability",
    "1": "Circuit Breaker Recovery (continuation)",
    "2": "Distributed Systems: Observability",
    "3": "Distributed Systems: Resilience and Scaling",
    "4": "Scaling Limitations (continuation)",
}


def format_sources(context_data):
    sources = context_data.get("sources") if isinstance(context_data, dict) else None
    if isinstance(sources, pd.DataFrame):
        records = sources.to_dict(orient="records")
    elif isinstance(sources, list):
        records = sources
    else:
        return "No source records were returned."

    sections = []
    for number, item in enumerate(records, start=1):
        item = item if isinstance(item, dict) else {"text": str(item)}
        source_id = str(item.get("id", number))
        content = " ".join(str(item.get("text") or "").split())
        preview = content[:347].rstrip() + "..." if len(content) > 350 else content
        title = SOURCE_TITLES.get(source_id, f"Retrieved source {source_id}")
        sections.append(
            f"**{number}. {title}**\n\n"
            f"*Source ID: {source_id}*\n\n{preview}"
        )
    return "\n\n---\n\n".join(sections) or "No source records were returned."


def value_or_unknown(result, name):
    value = getattr(result, name, None)
    return "Not reported" if value is None else str(value)


def answer_question(question):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", "No query was run."

    try:
        # Gradio runs this handler in a worker thread. asyncio.run keeps
        # the query loop isolated from the UI's event loop.
        result = asyncio.run(_run_search(question))
        answer = str(getattr(result, "response", "") or "").strip()
        if not answer:
            answer = "The search completed but returned no answer text."

        context_data = getattr(result, "context_data", {})
        sources_text = format_sources(context_data)

        diagnostics = "\n".join([
            "Query completed successfully.",
            f"Entities retrieved: {value_or_unknown(result, 'entities')}",
            f"Relationships retrieved: {value_or_unknown(result, 'relationships')}",
            f"LLM calls: {value_or_unknown(result, 'llm_calls')}",
            f"Prompt tokens: {value_or_unknown(result, 'prompt_tokens')}",
            f"Output tokens: {value_or_unknown(result, 'output_tokens')}",
            f"Completion time: {value_or_unknown(result, 'completion_time')}",
        ])
        return answer, sources_text, diagnostics

    except Exception as exc:
        # Avoid printing exception details that could contain sensitive data.
        message = (
            f"Query failed ({type(exc).__name__}). "
            "Check API quota, environment configuration, and application logs."
        )
        return "The query could not be completed.", "", message


async def _run_search(question):
    result = ENGINE.search(question)
    if hasattr(result, "__await__"):
        result = await result
    return result


def clear_outputs():
    return "", "", "", "Enter a question about the indexed technical documents."


with gr.Blocks(title="GraphRAG Research Intelligence") as demo:
    gr.Markdown(
        "# GraphRAG Research Intelligence\n"
        "Ask questions about the indexed technical research documents. "
        "Answers are grounded in the existing GraphRAG index."
    )
    gr.Markdown(
        "This app uses the existing index and vector table. "
        "It does not rebuild the index."
    )

    question_box = gr.Textbox(
        label="Your question",
        placeholder="How do retries and circuit breakers improve service reliability?",
        lines=3,
    )
    with gr.Row():
        ask_button = gr.Button("Ask", variant="primary")
        clear_button = gr.Button("Clear")

    answer_box = gr.Markdown(label="Answer")
    with gr.Accordion("Retrieved source context", open=False):
        sources_box = gr.Markdown()
    with gr.Accordion("Query diagnostics", open=False):
        diagnostics_box = gr.Textbox(
            label="Diagnostics",
            lines=8,
            interactive=False,
        )

    ask_button.click(
        fn=answer_question,
        inputs=[question_box],
        outputs=[answer_box, sources_box, diagnostics_box],
    )
    question_box.submit(
        fn=answer_question,
        inputs=[question_box],
        outputs=[answer_box, sources_box, diagnostics_box],
    )
    clear_button.click(
        fn=clear_outputs,
        inputs=[],
        outputs=[question_box, answer_box, sources_box, diagnostics_box],
    )

    gr.Markdown("### Indexed corpus")
    gr.JSON(value=INDEX_COUNTS, label="Loaded index counts")


if __name__ == "__main__":
    share_enabled = os.environ.get("GRADIO_SHARE", "false").lower() == "true"
    demo.launch(share=share_enabled)
