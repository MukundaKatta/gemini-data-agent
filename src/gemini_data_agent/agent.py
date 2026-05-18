"""ADK Gemini agent wired to the MongoDB MCP server (stub by default,
real cluster via env vars). Takes a natural-language data question and
walks the MongoDB tools to answer it."""

from __future__ import annotations

import os
import sys
from typing import Any


try:
    from google.adk.agents import LlmAgent
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    _ADK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ADK_AVAILABLE = False


SYSTEM_PROMPT = """\
You are a MongoDB data analyst. The user asks data questions in plain English
and you use the available MongoDB tools to answer them.

Always start by calling `list_databases` and `list_collections` to discover
what's available, then call `collection_schema` for the collection you plan
to query. After that, pick the right tool:
- "how many X" or "count X" -> call `count`
- "show me the top N" or "list X" -> call `find` with a limit
- "group by" / "broken down by" / "per plan" / "per status" -> call
  `aggregate` with `$group`.

Always assume the user wants you to execute tool calls and answer using the
results. Don't ask for clarification on schema or collection names; discover
them with the tools.

Format your final answer with EXACTLY these four labeled sections:

ANSWER: <one-sentence direct answer>
QUERY: <the exact tool name(s) and arguments you actually called>
EVIDENCE: <2-4 bullets, each citing a number copied verbatim from the tool output>
NEXT STEP: <one concrete follow-up the analyst could try>

The numbers in your answer must come from the tool output, not from your
own estimates. If the tool returned `count: 75`, write 75; do not say
"about 75" or extrapolate.
"""


def _mongo_toolset(stub: bool = True) -> Any:
    if not _ADK_AVAILABLE:
        raise ImportError("Install google-adk and mcp: pip install google-adk mcp")
    if stub:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gemini_data_agent.mcp_stub"],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    else:
        params = StdioServerParameters(
            command="npx",
            args=["-y", "mongodb-mcp-server@latest",
                  "--connectionString", os.environ["MONGODB_CONNECTION_STRING"]],
            env={**os.environ},
        )
    return McpToolset(connection_params=StdioConnectionParams(server_params=params))


def build_agent(model: str = "gemini-2.5-flash", stub: bool = True) -> Any:
    if not _ADK_AVAILABLE:
        return None
    return LlmAgent(
        model=model,
        name="gemini_data_agent",
        instruction=SYSTEM_PROMPT,
        tools=[_mongo_toolset(stub=stub)],
    )
