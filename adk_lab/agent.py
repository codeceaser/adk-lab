"""The single root agent for Expedition E0.

The three Python functions are passed straight into `tools=`. ADK builds the
tool contract from them; nothing here wraps, registers or decorates them.
"""

from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from .tools import get_employee, validate_proposal_fields

from .wrapped_tools import wrapped_get_assessment_unit

root_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="ida_lab_agent",
    description=(
        "Helps users inspect Employee and Assessment Unit records and validate"
        " Activity Proposal fields."
    ),
    instruction=(
        "You help users inspect Employee and Assessment Unit information and"
        " check whether Activity Proposal fields are usable. Use the available"
        " tools when a request needs those capabilities. Never invent Employee"
        " or Assessment Unit information — report only what a tool returned."
    ),
    tools=[get_employee, wrapped_get_assessment_unit, validate_proposal_fields],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
        )
    ),
)
