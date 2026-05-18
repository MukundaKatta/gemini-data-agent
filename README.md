# gemini-data-agent

A natural-language data-query agent built on **Google Cloud Agent Builder (ADK)**,
**Gemini 2.5**, and the **MongoDB MCP server**.

Open source under Apache 2.0.

## What it does

You ask "how many pro-plan users churned last month?" or "what's the
average order value for shipped orders?" in plain English. The agent
discovers the schema via the MongoDB MCP tools, picks the right query
shape (find / count / aggregate), runs it, and returns a four-section
answer: a direct one-line answer, the exact MongoDB query it used,
2-4 evidence bullets with counts copied verbatim from the database
response, and one suggested follow-up.

The agent uses the standard MongoDB MCP tool surface
(`list_databases`, `list_collections`, `collection_schema`, `find`,
`count`, `aggregate`) — same as the official
[`mongodb-mcp-server`](https://www.npmjs.com/package/mongodb-mcp-server) npm
package. A stub MCP server ships in the repo with a small canned
e-commerce dataset (500 users, 1200 orders) so demos run without a
MongoDB cluster.

## Architecture

```
┌─────────────┐  user question         ┌──────────────────────────────┐
│  Streamlit  │ ────────────────────▶  │  ADK LlmAgent (Gemini 2.5)   │
│  dashboard  │                         │  on Vertex AI                │
└─────────────┘ ◀── answer + query ──── └────┬─────────────────────────┘
                                              │ MCPToolset / stdio
                                              ▼
                                   ┌───────────────────────────┐
                                   │  MongoDB MCP server        │
                                   │  (stub by default,         │
                                   │  real cluster via flag)    │
                                   └───────────────────────────┘
```

## Try it locally

```bash
git clone https://github.com/MukundaKatta/gemini-data-agent
cd gemini-data-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_LOCATION=us-central1

PYTHONPATH=src streamlit run app/dashboard.py
```

## Try it against a real MongoDB cluster

```bash
export MONGODB_CONNECTION_STRING="mongodb+srv://user:pass@host/?retryWrites=true"
```

Untick "Use stub MongoDB MCP" in the sidebar. The agent now spawns the
official `mongodb-mcp-server` via `npx`.

## Tests

```bash
PYTHONPATH=src pytest -q
```

11 tests cover the stub server's responses and the agent wiring.

## License

Apache 2.0. Mukunda Katta, independent developer.
