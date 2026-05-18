from gemini_data_agent.agent import build_agent, _ADK_AVAILABLE


def test_adk_importable():
    assert _ADK_AVAILABLE


def test_agent_constructs():
    agent = build_agent(stub=True)
    assert agent is not None
    assert agent.name == "gemini_data_agent"


def test_agent_has_mongo_toolset():
    agent = build_agent(stub=True)
    tools = list(getattr(agent, "tools", []) or [])
    assert len(tools) >= 1
