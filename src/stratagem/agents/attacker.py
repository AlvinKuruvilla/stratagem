"""Attacker agent node for the LangGraph game loop."""

from __future__ import annotations

from typing import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from stratagem.agents.context import GameContext
from stratagem.agents.llm import create_llm
from stratagem.agents.tools.attacker_tools import create_attacker_tools
from stratagem.game.state import GameState

ATTACKER_SYSTEM_PROMPT_TEMPLATE = """\
You are the ATTACKER in a network security game.

Your objective: navigate the network to reach high-value targets, compromise
them, and exfiltrate as much value as possible without being detected.

Current state:
- Position: {position}
- Round: {current_round}/{max_rounds}
- Compromised nodes: {compromised}
- Total exfiltrated: {exfiltrated:.1f}
- Known access: {access}

Strategy guidance:
1. Use scan_network to discover adjacent nodes from your current position.
2. Use probe_node to learn what techniques work against a target.
3. Use execute_technique to compromise nodes — pick techniques with high
   success rate and low noise to avoid detection.
4. Use move_lateral to move through compromised nodes toward high-value targets.
5. Use exfiltrate to extract value from compromised nodes.
6. Prioritize high-value targets (databases, application servers).
7. Minimize noise — the defender has deployed deception assets that can detect you.

When you have completed your actions for this round, stop calling tools.
"""


def create_attacker_node(
    llm: BaseChatModel | None = None,
    **llm_kwargs,
) -> Callable[[GameState], dict]:
    """Create an attacker node function for the game graph."""

    def attacker_node(state: GameState) -> dict:
        model = llm or create_llm(**llm_kwargs)
        ctx = GameContext.from_game_state(state)

        # Build round-specific prompt with current attacker state.
        access_str = ", ".join(
            f"{k}={v.value}" for k, v in ctx.attacker.access_levels.items()
        ) or "none"
        compromised_str = ", ".join(ctx.attacker.compromised_nodes) or "none"

        prompt = ATTACKER_SYSTEM_PROMPT_TEMPLATE.format(
            position=ctx.attacker.position,
            current_round=ctx.current_round,
            max_rounds=ctx.max_rounds,
            compromised=compromised_str,
            exfiltrated=ctx.attacker.exfiltrated_value,
            access=access_str,
        )

        tools = create_attacker_tools(ctx)
        agent = create_react_agent(model, tools)
        result = agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
        )

        update = ctx.to_state_update()
        update["messages"] = result["messages"]
        return update

    return attacker_node
