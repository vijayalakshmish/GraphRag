import os
from pathlib import Path

import pandas as pd
import streamlit as st
from graphrag.api import local_search
from graphrag.config.load_config import load_config

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

st.set_page_config(
    page_title="GraphRAG Research Intelligence",
    page_icon="🔎",
    layout="wide",
)

st.title("GraphRAG Research Intelligence")
st.caption("Evidence-grounded question answering for distributed-systems research")

# Require a password before loading the index or accepting questions.
import hmac

APP_PASSWORD = os.environ.get("APP_PASSWORD")

if not APP_PASSWORD:
    st.error("Demo password is not configured. Set APP_PASSWORD in the environment.")
    st.stop()

if not st.session_state.get("authenticated", False):
    with st.form("demo_login"):
        entered_password = st.text_input("Demo password", type="password")
        submitted = st.form_submit_button("Unlock demo")

    if submitted:
        if hmac.compare_digest(entered_password, APP_PASSWORD):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

@st.cache_resource
def load_project():
    config = load_config(ROOT)
    tables = {
        name: pd.read_parquet(OUTPUT / f"{name}.parquet")
        for name in [
            "entities",
            "communities",
            "community_reports",
            "text_units",
            "relationships",
        ]
    }
    return config, tables

try:
    config, tables = load_project()
except Exception as exc:
    st.error(f"Could not load the GraphRAG index: {exc}")
    st.stop()

with st.sidebar:
    st.header("Index overview")
    st.metric("Entities", len(tables["entities"]))
    st.metric("Relationships", len(tables["relationships"]))
    st.metric("Source passages", len(tables["text_units"]))
    st.divider()
    st.caption("Uses the saved Standard index. It does not rebuild the index.")

question = st.text_area(
    "Ask an engineering question",
    placeholder="How do circuit breakers and rate limiting help during overload?",
    height=100,
)

st.warning(
    "Submitting a question may send a request to Gemini and consume API quota. "
    "Check your provider's current pricing and quota before continuing."
)

if st.button("Search knowledge graph", type="primary"):
    if not question.strip():
        st.warning("Enter a question first.")
    elif not os.environ.get("GEMINI_API_KEY"):
        st.error(
            "GEMINI_API_KEY is not set in this app's environment. "
            "Set it securely before querying; do not paste the key into this app."
        )
    else:
        try:
            with st.spinner("Searching the knowledge graph..."):
                answer, context = local_search(
                    config=config,
                    entities=tables["entities"],
                    communities=tables["communities"],
                    community_reports=tables["community_reports"],
                    text_units=tables["text_units"],
                    relationships=tables["relationships"],
                    covariates=None,
                    community_level=0,
                    response_type="Multiple Paragraphs",
                    query=question.strip(),
                    verbose=False,
                )

            st.subheader("Answer")
            if isinstance(answer, str):
                st.markdown(answer)
            else:
                st.write(answer)

            with st.expander("Retrieved context (debug view)"):
                if isinstance(context, dict):
                    for name, value in context.items():
                        st.markdown(f"**{name}**")
                        if isinstance(value, pd.DataFrame):
                            st.dataframe(value, use_container_width=True)
                        else:
                            st.write(value)
                elif isinstance(context, list):
                    for item in context:
                        if isinstance(item, pd.DataFrame):
                            st.dataframe(item, use_container_width=True)
                        else:
                            st.write(item)
                else:
                    st.write(context)

        except Exception as exc:
            st.error(f"Query failed: {exc}")
            st.caption(
                "Check the runtime, API quota, and GraphRAG configuration. "
                "The saved index was not rebuilt by this app."
            )

st.divider()
st.caption("Prototype for research and evaluation. Verify important claims against cited source passages.")

