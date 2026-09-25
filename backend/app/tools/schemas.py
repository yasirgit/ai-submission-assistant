"""Arguments the model is allowed to pass. The caller is not one of them."""

from pydantic import BaseModel, ConfigDict, Field

TOOL_NAMES = (
    "get_submission",
    "get_company",
    "get_company_claims",
    "search_underwriting_guidelines",
)


class GetSubmissionArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submission_id: str = Field(min_length=1, max_length=64)


class GetCompanyArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str = Field(min_length=1, max_length=64)


class GetClaimsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str = Field(min_length=1, max_length=64)


class SearchGuidelinesArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=500)


ARG_MODELS = {
    "get_submission": GetSubmissionArgs,
    "get_company": GetCompanyArgs,
    "get_company_claims": GetClaimsArgs,
    "search_underwriting_guidelines": SearchGuidelinesArgs,
}


def openai_tool_specs() -> list[dict]:
    specs = []
    for name, model in ARG_MODELS.items():
        properties = {}
        required = []
        for field_name in model.model_fields:
            properties[field_name] = {"type": "string"}
            required.append(field_name)
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": _DESCRIPTION[name],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": False,
                    },
                },
            }
        )
    return specs


_DESCRIPTION = {
    "get_submission": "Read one submission the caller is allowed to see.",
    "get_company": "Read a company linked to a submission the caller is allowed to see.",
    "get_company_claims": "Read claims for a company the caller is allowed to see.",
    "search_underwriting_guidelines": "Search published guideline chunks. Returns a short list.",
}
