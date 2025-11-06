
import os, asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, set_default_openai_api
from agents.mcp import MCPServerStdio
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai.types.shared import Reasoning

# Tools
from tools.pdf_tools import extract_faa_tables
from tools.gumbo_tools import generate_gumbo
from tools.sireum_tools import run_sireum

load_dotenv(override=True)
set_default_openai_api(os.getenv("OPENAI_API_KEY"))

async def main():
    async with MCPServerStdio(
        name="Codex CLI",
        params={ "command": "npx", "args": ["-y", "codex", "mcp"] },
        client_session_timeout_seconds=360000,
    ) as codex_mcp_server:

        extractor_agent = Agent(
            name="Extractor",
            instructions=(f"""{RECOMMENDED_PROMPT_PREFIX}
You extract FAA tables from PDF into JSON via the tool `extract_faa_tables`.
If additional scripting is needed, call Codex MCP tools.
"""),
            tools=[extract_faa_tables],
            mcp_servers=[codex_mcp_server],
        )

        spec_agent = Agent(
            name="GUMBO Spec Generator",
            instructions=(f"""{RECOMMENDED_PROMPT_PREFIX}
You generate a classic GUMBO annex (Lark grammar) using the tool `generate_gumbo`.
Include sections: state/functions (if provided), integration, initialize, compute, compute_cases.
"""),
            tools=[generate_gumbo],
            mcp_servers=[codex_mcp_server],
        )

        verify_agent = Agent(
            name="Verifier",
            instructions=(f"""{RECOMMENDED_PROMPT_PREFIX}
Run Sireum/Logika GUMBO verification via `run_sireum`. Summarize results.
"""),
            tools=[run_sireum],
            mcp_servers=[codex_mcp_server],
        )

        repair_agent = Agent(
            name="Repair",
            instructions=(f"""{RECOMMENDED_PROMPT_PREFIX}
Given verification failures, propose minimal GUMBO fixes and a unified diff. 
If you need to edit files, use Codex to create patches.
"""),
            mcp_servers=[codex_mcp_server],
        )

        correction_manager = Agent(
            name="Correction Manager",
            instructions=(f"""{RECOMMENDED_PROMPT_PREFIX}
If extraction/spec generation repeatedly fail, propose code patches for the offending agent 
(e.g., improve table parsing, fix grammar mapping). Output a patch as a unified diff and rationale.
"""),
            mcp_servers=[codex_mcp_server],
        )

        project_manager = Agent(
            name="Project Manager",
            instructions=(f"""{RECOMMENDED_PROMPT_PREFIX}
You orchestrate: Extract → Spec → Verify → (Repair/Correction loop) until checks pass.
Gate each handoff: require files/artifacts to exist before proceeding.
"""),
            model="gpt-5",
            model_settings=dict(reasoning=Reasoning(effort="medium")),
            handoffs=[extractor_agent, spec_agent, verify_agent, repair_agent, correction_manager],
            tools=[WebSearchTool()],
            mcp_servers=[codex_mcp_server],
        )

        task_list = f"""
Goal: Build GUMBO annexes from FAA PDF and verify with Sireum.

Inputs:
- PDF: ./docs/Steve_Meller_FAA_docAR-08-32.pdf
- Model: ./models/Monitor_no_gumbo.sysml

Steps:
- Extract tables from the PDF to JSON using Extractor (`extract_faa_tables`).
- Generate GUMBO annex from JSON (`generate_gumbo`) and insert into the model.
- Run Sireum verification (`run_sireum`).
- If failures: Repair proposes fixes; if systemic: Correction Manager proposes code patches.
- Stop when verification passes, or limits are reached.
"""

        result = await Runner.run(project_manager, task_list, max_turns=30)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
