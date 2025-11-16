# historical_map_gradio.py

import gradio as gr
import asyncio
from agents import Agent, Runner
from historical_map_server.server import (
    events_near_location,
    region_timeline,
    route_history_summary,
)

# =====================================================================
# Build agent for the UI
# =====================================================================

def build_historical_agent():
    """
    Construct agent for Gradio UI.

    Input
    -----
    None

    Returns
    -------
    Agent object

    Behavior
    --------
    Creates an Agent wired to the exposed tools. The model is
    instructed to call tools when user prompts require retrieval.
    """
    return Agent(
        name="historical_agent",
        instructions="You are a historical assistant. Use the provided tools.",
        tools=[events_near_location, region_timeline, route_history_summary],
        model="gpt-4o-mini",
    )

agent = build_historical_agent()
runner = Runner()


async def run_agent_async(message: str) -> str:
    """
    Async wrapper around Runner.run.

    Input
    -----
    message
        User input prompt

    Returns
    -------
    Final LLM output text

    Behavior
    --------
    Awaits model response and returns the final string output.
    """
    result = await runner.run(agent, message)
    return result.final_output  # correct attribute for the Agents SDK


def run_agent(message: str) -> str:
    """
    Sync entrypoint for Gradio.

    Input
    -----
    message
        User input prompt

    Returns
    -------
    Final LLM output text

    Behavior
    --------
    Bridges Gradio's sync call with the async runner using asyncio.run.
    """
    return asyncio.run(run_agent_async(message))


# =====================================================================
# Gradio interface
# =====================================================================

ui = gr.Interface(
    fn=run_agent,
    inputs=gr.Textbox(label="Ask about history"),
    outputs=gr.Markdown(label="Answer"),
    title="Historical Timeline Agent",
    description="Ask about Beirut, Baalbek, or routes.",
    allow_flagging="never",
)

if __name__ == "__main__":
    ui.launch()
