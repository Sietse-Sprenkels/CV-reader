from pydantic_ai import Agent
from pydantic import BaseModel
from pydantic_ai.models.anthropic import AnthropicModelSettings


class Candidate(BaseModel):
    name: str
    birth_data: str
    gender: str
    email: str
    phone_number: str
    linkedin: str
    university: str
    study: str
    msc_start_date: str
    msc_graduation_date: str
    current_employer: str


class ReadFailure(BaseModel):
    """An unrecoverable failure. Use this when you can't recover from the error."""

    explanation: str


agent = Agent[None, list[Candidate] | ReadFailure](
    "anthropic:claude-sonnet-4-0",
    output_type=[list[Candidate], ReadFailure],
    instructions=(
        "You are given set of CV data. Extract the relevant fields and return a Candidate object."
        "If you cannot extract the data, return a ReadFailure object explaining why."
        "The CV is in dutch, and the fields may not be explicitly labeled."
        "CV's are separated by [BEGIN CV] and [END CV] markers."
        "Duplicate applicants should be merged into a single Candidate."
        "Make your best guess for missing fields based on the CV content."
        "Add an asterisk (*) to fields you are unsure about."
        "Leave fields empty if you cannot find any information about them."
    ),
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,
    ),
)
