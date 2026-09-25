"""JSON the model is allowed to return. Extra keys are ignored."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import RiskFlagType, Severity


class SourceCitation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: str
    chunk_id: str
    title: str = ""
    excerpt: str = ""


class DraftFlag(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: RiskFlagType
    severity: Severity
    description: str = Field(min_length=1, max_length=500)


class AnalysisDraft(BaseModel):
    """There is no approval field. A model that adds one is ignored."""

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(min_length=1, max_length=4000)
    extracted_data: dict
    risk_flags: list[DraftFlag] = Field(default_factory=list, max_length=20)
    missing_information: list[str] = Field(default_factory=list, max_length=20)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=20)
    confidence: float = Field(ge=0, le=1)
    sources: list[SourceCitation] = Field(default_factory=list, max_length=10)
