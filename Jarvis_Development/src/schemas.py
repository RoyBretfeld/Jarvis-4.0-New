"""
AWP-048 – Pydantic Schemas
Validierte Datenmodelle für alle internen Datenströme:
Core ↔ RAG ↔ Agents ↔ UI
Python 3.12 | Pydantic v2
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class AgentRole(str, Enum):
    CODER    = "coder"
    TESTER   = "tester"
    SECURITY = "security"
    DEBATE   = "debate"


class AuraState(str, Enum):
    IDLE       = "idle"
    PROCESSING = "processing"
    ALERT      = "alert"
    SUCCESS    = "success"


class LogLevel(str, Enum):
    DEBUG   = "DEBUG"
    INFO    = "INFO"
    WARNING = "WARNING"
    ERROR   = "ERROR"


class AWPStatus(str, Enum):
    PENDING     = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED   = "COMPLETED"
    SKIPPED     = "SKIPPED"
    FAILED      = "FAILED"


# ─────────────────────────────────────────────
# Core ↔ RAG
# ─────────────────────────────────────────────

class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=32_000)
    model: str = Field(default="bge-small-en-v1.5")


class EmbedResponse(BaseModel):
    vector: list[float]
    dim: int
    model: str

    @field_validator("vector")
    @classmethod
    def check_dim(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("Empty vector")
        return v


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    source_file: str
    chunk_index: int = Field(ge=0)
    text: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    vector: list[float] | None = None


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=50)
    mode: str = Field(default="hybrid", pattern="^(hybrid|semantic|keyword)$")
    score_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    filter_source: str | None = None


class SearchHit(BaseModel):
    chunk_id: str
    text: str
    score: float = Field(ge=0.0, le=1.0)
    source: str                    # "qdrant" | "chroma"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int
    mode: str


# ─────────────────────────────────────────────
# Agent I/O
# ─────────────────────────────────────────────

class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent: AgentRole
    file: str | None = None
    content: str | None = None
    operation: str = "write"
    context_hits: list[SearchHit] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentOutput(BaseModel):
    task_id: str
    agent: AgentRole
    success: bool
    output: str = ""
    errors: list[str] = Field(default_factory=list)
    diff: str | None = None
    backup_path: str | None = None
    security_findings: int = 0
    duration_ms: int = 0


class PipelineState(BaseModel):
    pipeline_id: str = Field(default_factory=lambda: str(uuid4()))
    file: str
    steps: list[AgentOutput] = Field(default_factory=list)
    stopped_at: AgentRole | None = None
    success: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def duration_ms(self) -> int:
        if self.completed_at:
            return int((self.completed_at - self.created_at).total_seconds() * 1000)
        return 0


# ─────────────────────────────────────────────
# Core ↔ UI (WebSocket messages)
# ─────────────────────────────────────────────

class LogMessage(BaseModel):
    ts: str
    level: LogLevel
    service: str
    message: str


class AuraUpdate(BaseModel):
    state: AuraState
    reason: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ThreadMetrics(BaseModel):
    threads: list[float] = Field(..., min_length=1, max_length=64)
    avg_pct: float
    max_pct: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def compute_stats(self) -> "ThreadMetrics":
        if self.threads:
            object.__setattr__(self, "avg_pct",
                               round(sum(self.threads) / len(self.threads), 1))
            object.__setattr__(self, "max_pct", round(max(self.threads), 1))
        return self


class SystemStatus(BaseModel):
    cpu_pct: float = Field(ge=0.0, le=100.0)
    ram_pct: float = Field(ge=0.0, le=100.0)
    ssd1_pct: float = Field(ge=0.0, le=100.0, default=0.0)
    ssd2_pct: float = Field(ge=0.0, le=100.0, default=0.0)
    temp_celsius: float | None = None
    aura: AuraState = AuraState.IDLE
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# State management
# ─────────────────────────────────────────────

class AWPEntry(BaseModel):
    status: AWPStatus = AWPStatus.PENDING
    artifact: str | None = None
    note: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SecuritySummary(BaseModel):
    owasp_scan: str = "PENDING"
    critical_findings: int = Field(ge=0, default=0)
    warnings: int = Field(ge=0, default=0)
    scan_log: str | None = None


class ProjectState(BaseModel):
    project: str
    version: str
    current_phase: str
    last_updated: datetime
    workpackages: dict[str, AWPEntry] = Field(default_factory=dict)
    security: SecuritySummary = Field(default_factory=SecuritySummary)


# ─────────────────────────────────────────────
# Debate mode (AWP-050)
# ─────────────────────────────────────────────

class DebateMessage(BaseModel):
    round: int = Field(ge=1)
    speaker: AgentRole
    argument: str
    verdict: str | None = None        # only on final round


class DebateResult(BaseModel):
    topic: str
    rounds: list[DebateMessage]
    consensus: bool
    final_verdict: str
    requires_human_approval: bool
