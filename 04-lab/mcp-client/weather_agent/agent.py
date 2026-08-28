"""
Weather Agent - connects to a Streamable HTTP MCP server.
"""
import os

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")
MODEL_NAME = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

logger.info(f"🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)

# McpToolset connects lazily when ADK needs to discover or invoke a tool.
weather_tools = McpToolset(connection_params=connection_params)

root_agent = Agent(
    name="weather_agent",
    model=MODEL_NAME,
    description="An assistant that provides current weather and short forecasts.",
    instruction=(
        "Use the MCP weather tools for weather questions. Ask for a city when it "
        "is missing. Forecasts must be between 1 and 3 days. Do not invent weather data."
    ),
    tools=[weather_tools],
)
logger.info("Weather agent initialized with MCP server %s", MCP_SERVER_URL)

