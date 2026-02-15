"""Defender agent node for the LangGraph game loop."""

from __future__ import annotations

from typing import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from stratagem.agents.context import GameContext
from stratagem.agents.llm import create_llm
from stratagem.agents.tools.defender_tools import create_defender_tools
from stratagem.game.state import GameState

DEFENDER_SYSTEM_PROMPT = """\
You are the DEFENDER in a Stackelberg network security game.

Your objective: deploy deception assets (honeypots, decoy credentials, honeytokens)
on network nodes to maximize the probability of detecting an attacker.

You deploy assets ONCE during a setup phase. The attacker then takes multiple
turns trying to reach high-value targets. Your deployed assets persist and can
detect the attacker throughout the game.

Asset types and trade-offs:
- Honeypot (cost 3.0, detection 85%): Fake service. Expensive but very reliable.
- Decoy Credential (cost 1.5, detection 70%): Fake credential. Medium cost/detection.
- Honeytoken (cost 1.0, detection 50%): Fake data artifact. Cheap but less reliable.

Strategy guidance:
1. Use inspect_topology to understand the network layout.
2. Use get_solver_recommendation to see the game-theoretic optimal strategy.
3. Focus on high-value targets and chokepoints the attacker must traverse.
4. Use get_budget to track remaining resources.
5. Deploy assets until your budget is spent or you are satisfied with coverage.

When you are done deploying, stop calling tools.
"""


def create_defender_node(
    llm: BaseChatModel | None = None,
    **llm_kwargs,
) -> Callable[[GameState], dict]:
    """Create a defender node function for the game graph.

    The returned function deserializes GameState into a GameContext, runs a
    ReAct agent with defender tools until it stops calling tools, then
    serializes the context back into a state update.
    """

    def defender_node(state: GameState) -> dict:
        model = llm or create_llm(**llm_kwargs)
        ctx = GameContext.from_game_state(state)
        tools = create_defender_tools(ctx)

        agent = create_react_agent(model, tools)
        result = agent.invoke(
            {"messages": [HumanMessage(content=DEFENDER_SYSTEM_PROMPT)]},
        )

        update = ctx.to_state_update()
        update["messages"] = result["messages"]
        return update

    return defender_node
