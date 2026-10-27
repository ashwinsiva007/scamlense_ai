from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


BandType = Literal["low_risk", "suspicious", "likely_scam", "insufficient_info"]
ConfidenceType = Literal["high", "medium", "low"]
LanguageType = Literal["en", "ta", "hi"]
ModeType = Literal["cloud", "local", "mock"]
SignalSourceType = Literal["rule", "tool", "model"]
ToolStatusType = Literal["ok", "warn", "error", "skipped"]


class ExtractedData(BaseModel):
    document_type: str = Field(..., description="Detected document classification (e.g. offer_letter, sms, alert)")
    sender: Optional[str] = Field(None, description="Sender address, phone, or handle if visible")
    message_text: str = Field(..., description="Verbatim raw text extracted from input")
    urls: List[str] = Field(default_factory=list, description="Extracted web links and URLs")
    phone_numbers: List[str] = Field(default_factory=list, description="Extracted contact phone numbers")
    upi_ids: List[str] = Field(default_factory=list, description="Extracted UPI VPAs or payment handles")
    amounts: List[str] = Field(default_factory=list, description="Monetary amounts mentioned")
    claimed_brand: Optional[str] = Field(None, description="Brand or organization claimed by sender")
    detected_language: str = Field(default="en", description="Primary natural language detected in text")
    image_quality: str = Field(default="sharp", description="Quality assessment (high, medium, low, sharp, blurry, glitched, text_only)")
    visual_notes: List[str] = Field(default_factory=list, description="Visual observations from image layout (mismatched fonts, odd alignment, cropped status bar, etc.)")


class Signal(BaseModel):
    id: str = Field(..., description="Unique rule/signal identifier")
    label: str = Field(..., description="Human-readable signal title")
    category: str = Field(..., description="One of the 10 signal categories")
    weight: float = Field(..., description="Score weight contribution (positive increases risk, negative reduces)")
    evidence: str = Field(..., description="Exact quoted verbatim text or observable fact from input")
    source: SignalSourceType = Field(..., description="Origin of detection: rule, tool, or model")


class ToolResult(BaseModel):
    tool: str = Field(..., description="Name of external verifier tool")
    target: str = Field(..., description="Artifact checked (domain, URL, UPI handle)")
    status: ToolStatusType = Field(..., description="Check status: ok, warn, error, skipped")
    detail: str = Field(..., description="Human-readable verification outcome")


class FamilyAlert(BaseModel):
    title: str = Field(..., description="Shareable alert header with warning emoji")
    body: str = Field(..., description="Simple conversational warning suited for family WhatsApp groups")
    tips: List[str] = Field(default_factory=list, description="Actionable bullet points for non-technical relatives")


class AnalyzeResponse(BaseModel):
    request_id: str = Field(..., description="Unique UUID for this analysis session")
    band: BandType = Field(..., description="Calibrated risk tier")
    score: int = Field(..., ge=0, le=100, description="Deterministic risk score 0 to 100")
    confidence: ConfidenceType = Field(..., description="Confidence level of assessment")
    scam_type: Optional[str] = Field(None, description="Identified scam archetype or pattern")
    language: LanguageType = Field(..., description="Language used for explanations")
    extracted: ExtractedData = Field(..., description="Entities and verbatim content parsed from input")
    signals: List[Signal] = Field(default_factory=list, description="Red flags and mitigating signals with evidence")
    tool_results: List[ToolResult] = Field(default_factory=list, description="Results from URL, domain, or UPI verifiers")
    explanation: str = Field(..., description="Comprehensive natural language explanation of findings")
    next_steps: List[str] = Field(default_factory=list, description="Recommended immediate actions")
    family_alert: FamilyAlert = Field(..., description="Formatted card ready to forward to relatives")
    limitations: str = Field(..., description="Explicit disclaimer of informational nature and boundaries")
    mode: ModeType = Field(..., description="Mode under which this request was executed")
    timings_ms: Dict[str, Union[int, float]] = Field(default_factory=dict, description="Execution latencies per stage")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service status")
    mode: str = Field(..., description="Current configured MODE")
    model: str = Field(..., description="Configured model identifier")
    model_name: Optional[str] = Field(None, description="Configured model name identifier")
    env_file_loaded: str = Field(default="", description="Path of the environment file loaded")
    env_file_path_loaded: str = Field(default="", description="Path of the environment file loaded")
    key_configured: bool = Field(default=False, description="Whether Gemini API key is configured (true or false only)")
    key_length: int = Field(default=0, description="Length of configured Gemini API key (never exposes key)")
    sdk_version: str = Field(default="unknown", description="Version of google-genai SDK installed")
    process_id: int = Field(default=0, description="Process ID of the answering server")
    started_at: str = Field(default="", description="ISO timestamp of server startup")
    ollama_reachable: bool = Field(default=False, description="Whether local Ollama endpoint responded")
    cloud_key_set: bool = Field(default=False, description="Whether cloud API key is configured")
    live_ok: bool = Field(default=False, description="Result of a tiny real request to the model, cached for 60 seconds")


class BenchmarksResponse(BaseModel):
    dataset_version: str
    total_eval_samples: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float = 0.0
    average_latency_ms: int
    rule_packs_loaded: int
    last_updated: str
    confusion_matrix: Optional[Dict[str, int]] = None
    comparison: Optional[Dict[str, Any]] = None
    per_language: Optional[Dict[str, Any]] = None
