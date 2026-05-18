"""gemini-data-agent dashboard."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_data_agent.runner import ask  # noqa: E402


st.set_page_config(page_title="gemini-data-agent", layout="wide", page_icon=":bar_chart:")
st.title("gemini-data-agent")
st.caption(
    "Natural-language data-query agent on Google Cloud Agent Builder (ADK) "
    "+ Gemini 2.5, wired to the MongoDB MCP server. Apache 2.0."
)

with st.sidebar:
    st.header("Ask MongoDB")
    question = st.text_area(
        "Your question",
        value="How many users have logged in within the last 7 days, grouped by plan?",
        height=120,
    )
    model = st.selectbox(
        "Gemini model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
        index=0,
    )
    stub = st.toggle(
        "Use stub MongoDB MCP",
        value=True,
        help="On = local stub with canned acme_prod / acme_analytics databases. Off = real cluster (set MONGODB_CONNECTION_STRING).",
    )
    run = st.button("Run query", type="primary", use_container_width=True)
    st.divider()
    st.caption(
        f"Project: `{os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set')}`  "
        f"Vertex AI: `{os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'true')}`"
    )

st.markdown(
    """
The agent walks these MongoDB MCP tools to answer data questions:
- **list_databases** / **list_collections** to discover the schema
- **collection_schema** to read field types before querying
- **find** / **count** for direct retrieval
- **aggregate** for grouped / pipeline questions ($match + $group)
"""
)

if run:
    with st.status("Running Vertex AI Gemini...", expanded=True) as status:
        t0 = time.perf_counter()
        try:
            resp = ask(question, stub=stub, model=model)
        except Exception as e:  # pragma: no cover
            status.update(label=f"Error: {e}", state="error")
            st.exception(e)
            st.stop()
        elapsed = (time.perf_counter() - t0) * 1000
        status.update(label=f"Done in {elapsed:.0f} ms", state="complete")

    st.subheader("Answer")
    st.markdown(resp.final_text or "_(no final response)_")

    with st.expander(f"Agent event trace ({len(resp.events)} events)"):
        for i, ev in enumerate(resp.events):
            st.markdown(f"**{i}.** author=`{ev.get('author')}` final=`{ev.get('is_final')}`")
            text = ev.get("text") or ""
            if text:
                st.code(text[:1500], language=None)
else:
    st.info("Use the sidebar to fire a query against the stub MongoDB cluster.")
