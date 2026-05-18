# Google Cloud Rapid Agent Hackathon — MongoDB partner track submission

Devpost: https://rapid-agent.devpost.com
Deadline: 2026-06-11 14:00 PDT
Track: **MongoDB**

This is the fourth substantively-different submission from Mukunda Katta
to this hackathon (rule 7B explicitly allows multiple unique submissions):

- `ragvitals` — RAG drift agent
- `gemini-ops-agent` — production-incident investigator (Dynatrace MCP)
- `gemini-eval-agent` — LLM-evaluation auditor (Arize Phoenix MCP)
- `gemini-data-agent` (this entry) — NL-to-MongoDB query agent

Different partner, different MCP, different agent goal.

## Rule compliance

| Rule | How we meet it |
|---|---|
| Powered by Gemini | gemini-2.5-flash via Vertex AI |
| Powered by Google Cloud Agent Builder | `google.adk.agents.LlmAgent` (ADK) |
| Integrates a Partner's MCP server | Tool surface matches `mongodb-mcp-server` (npm); stub for demos, real cluster via env var |
| Newly created during Contest Period | Repo init 2026-05-18, within May 5 – Jun 11 window |
| Original creation, not extension | Standalone repo |
| OSI license at repo root | Apache 2.0 |
| Runs on web | Streamlit dashboard, Cloud Run deployable |

## Elevator pitch
A Gemini agent that turns plain-English questions into MongoDB queries
via the MongoDB MCP server, and answers with the counts copied verbatim
from the database.

## Description
gemini-data-agent treats every data question as a discover-then-query
loop. You ask "how many users are on each plan?" and the agent walks
the MongoDB MCP tools:

1. `list_databases` to see what's available.
2. `list_collections` for the candidate database.
3. `collection_schema` to read the field types of the target collection.
4. The right query tool — `count` for "how many", `find` for "show me",
   `aggregate` for "group by" / "broken down by".

The answer is structured: a one-line direct answer, the exact tool +
arguments used, 2-4 evidence bullets citing numbers copied verbatim from
the database, and a suggested follow-up.

A live agent run on Vertex AI returned `269 free + 127 starter + 73 pro
+ 31 enterprise = 500 users` — matching the canned dataset exactly.

## Built with
python, gemini, gemini-2-5, vertex-ai, google-cloud-agent-builder,
agent-development-kit, mcp, model-context-protocol, mongodb, mongodb-mcp,
streamlit, google-cloud-run, apache-2

## Try it out
- Code repo: https://github.com/MukundaKatta/gemini-data-agent
- Live demo (Cloud Run): <PASTE_AFTER_DEPLOY>
- Demo video (YouTube unlisted): <PASTE_AFTER_REC>
