import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase

from tavily.client import TavilyClient

async def get_mcp_tools():
    client = MultiServerMCPClient(
        {
            "travel_server": {
                "transport": "streamable_http",
                "url": "https://mcp.kiwi.com"
            }
        },
    )

    tools = await client.get_tools()
    return tools

tavily_key = os.environ.get("TAVILY_CLIENT")

tavily = TavilyClient(api_key=tavily_key)

@tool
def web_search(query: str, search_number:int, max_search_number: int):
    """
        Search the web for information. only string is allowed in query.
        You must tract your search count by providing search_number(starting at 1) and max_seatch_number on every call.
        Queries must use only plain text characters. Do not use accented or special characters(egL use 'capacite' instead of 'capacité')
    """
    print(f"searching the web for {query}. search_number={search_number}. max_search_number={max_search_number}")
    if search_number > max_search_number:
        return {"message": "search limit exceeded. Please summarize your findings and provide your final answer."}
    try:
        return tavily.search(query)
    except Exception as e:
        return {"error": str(e)}
    

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "resourses", "Chinook.db")

db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

@tool
def query_playlist_db(query: str) -> str:
    """query the database for playlist information"""
    print(f"quering the db with {query}")
    try:
        return db.run(query)
    except Exception as e:
        return f"error querying database {e}"
    