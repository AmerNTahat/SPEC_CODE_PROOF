
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async def main() -> None:
    async with MCPServerStdio(
        name="Codex CLI",
        params={ "command": "npx", "args": ["-y", "codex", "mcp"] },
        client_session_timeout_seconds=360000,
    ) as codex_mcp_server:
        print("Codex MCP server started.")
        # This script only demonstrates launching Codex MCP.
        # See orchestrate.py for a full multi-agent workflow.
        return

if __name__ == "__main__":
    asyncio.run(main())
