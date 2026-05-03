from multi_agent.wedding_planner.tools import get_mcp_tools
from langchain.agents import create_agent

from multi_agent.wedding_planner.model import ollama

from datetime import datetime

async def create_travel_agent():
    tools = await get_mcp_tools()
    travel_agent = create_agent(
        model=ollama,
        tools=tools,
        system_prompt=f"""
        You are a travel agent. Search for flights to the desired detination wedding location.
        You are not allowed to ask any more follow up questions, you must find the best flight options based on the following criteria:
        - Prices (lowest, economy class)
        - Duration (shortest)
        - Date (time of the year which you believe is best for a wedding at this location)
        to make thinks easy, only look for one ticket, one way.
        you may need to make multiple searches to iteratively find the best options.
        you will be given no extra information, only the origin and destination. It is your job to think critically about the best options.
        if the MCP tool fails, returns malformed output, or does give you usable flight results, try the tool again.
        once you have found the best options, let the user know yout shortlist of options.
        current date time - {datetime.now()}
        """
    )

    return travel_agent