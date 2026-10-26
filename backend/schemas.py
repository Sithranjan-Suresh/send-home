"""Pydantic models for the analysis, requests and responses (nothing is stored)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Span(BaseModel):
    start: int
    end: int


class Verified(BaseModel):
    """Fields added by the deterministic verify pass."""

    span: Optional[Span] = None
    flags: list[str] = Field(default_factory=list)


class SummaryItem(Verified):
    text: str
    source_quote: str = ""


class MedicationItem(Verified):
    name: str
    dose: Optional[str] = None
    schedule: Optional[str] = None
    purpose: Optional[str] = None
    source_quote: str = ""


class RedFlagItem(Verified):
    text: str
    urgency: Literal["call", "er"] = "call"
    source_quote: str = ""


class FollowUpItem(Verified):
    what: str
    when: Optional[str] = None
    source_quote: str = ""


class Analysis(BaseModel):
    is_discharge_doc: bool = True
    summary: list[SummaryItem] = Field(default_factory=list)
    medications: list[MedicationItem] = Field(default_factory=list)
    red_flags: list[RedFlagItem] = Field(default_factory=list)
    follow_ups: list[FollowUpItem] = Field(default_factory=list)


class Grades(BaseModel):
    original: Optional[float] = None
    plain: Optional[float] = None


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    analysis: Analysis
    grades: Grades
    message: Optional[str] = None


class AskRequest(BaseModel):
    text: str
    question: str


class AskResponse(BaseModel):
    in_document: bool
    answer: Optional[str] = None
    source_quotes: list[str] = Field(default_factory=list)
    spans: list[Span] = Field(default_factory=list)


class TranslateRequest(BaseModel):
    analysis: Analysis
    language: str = "es"


class TranslateResponse(BaseModel):
    translated: dict
    back_translation: dict
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str


class ErrorResponse(BaseModel):
    error: str
    message: str
