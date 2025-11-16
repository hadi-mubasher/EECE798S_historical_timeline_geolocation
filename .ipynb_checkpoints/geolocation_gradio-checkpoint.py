import gradio as gr
import asyncio
from agents import Agent, Runner
from geolocation_server.server import GeolocationServer

# =====================================================================
# Build agent for the UI
# =====================================================================

def build_geolocation_agent() -> Agent:
    """
    Construct agent for Gradio UI.

    Input
    -----
    None

    Returns
    -------
    Agent
        Configured agent instance

    Behavior
    --------
    Creates a GeolocationServer instance and registers its tools
    (geocode, reverse_geocode, nearby_search) with the Agent. The
    model is instructed to call tools when user prompts require
    retrieval or spatial reasoning.
    """
    server = GeolocationServer()

    # NOTE
    # ----
    # We pass the *bound* tool callables from the instance so the
    # function_tool decorator’s wrapping is preserved.
    tools = [
        server.geocode,
        server.reverse_geocode,
        server.nearby_search,
    ]

    return Agent(
        name="geolocation_agent",
        instructions=(
            "You are a geolocation assistant. Use the provided tools "
            "to geocode names, reverse geocode coordinates, and search "
            "for nearby points of interest."
        ),
        tools=tools,
        model="gpt-4o-mini",
    )


agent = build_geolocation_agent()
runner = Runner()

# =====================================================================
# Async / Sync bridge
# =====================================================================

async def run_agent_async(message: str) -> str:
    """
    Async wrapper around Runner.run.

    Input
    -----
    message
        User input prompt (free-form)

    Returns
    -------
    str
        Final LLM output text

    Behavior
    --------
    Awaits the model response and returns the final string output
    (Agent’s synthesized answer after any tool calls).
    """
    result = await runner.run(agent, message)
    return result.final_output  # Agents SDK: final text output


def run_agent(message: str) -> str:
    """
    Sync entrypoint for Gradio.

    Input
    -----
    message
        User input prompt

    Returns
    -------
    str
        Final LLM output text

    Behavior
    --------
    Bridges Gradio’s sync call with the async runner using asyncio.run.
    """
    return asyncio.run(run_agent_async(message))


# =====================================================================
# Gradio interface
# =====================================================================

ui = gr.Interface(
    fn=run_agent,
    inputs=gr.Textbox(
        label="Ask about locations, coordinates, or nearby places",
        placeholder=(
            "Examples:\n"
            "• Geocode AUB\n"
            "• Reverse geocode 33.90, 35.48\n"
            "• Find hospital near 33.89, 35.48 within 2km\n"
        ),
        lines=4,
    ),
    outputs=gr.Markdown(label="Answer"),
    title="Geolocation Agent",
    description=(
        "Free-form chat that routes to geocode / reverse geocode / nearby search tools.\n"
        "Tip: You can paste coordinates or ask for a POI type (e.g., hospital, museum, park)."
    ),
    allow_flagging="never",
)

if __name__ == "__main__":
    ui.launch()
