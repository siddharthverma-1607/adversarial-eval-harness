from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class AttackDefinition(BaseModel):
    id: str
    name: str
    description: str
    prompt: str

class RunCreate(BaseModel):
    name: Optional[str] = Field(None, description="Friendly run name")
    system_prompt: Optional[str] = Field(None, description="System prompt for the model")
    model_name: Optional[str] = Field(None, description="Model name override")
    model_version: Optional[str] = Field(None, description="Model version override")
    attack_ids: Optional[List[str]] = Field(None, description="Optional subset of attack IDs")

class AttackResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attack_id: str
    attack_name: str
    attack_description: Optional[str]
    prompt: str
    output: str
    decision: str
    reason: Optional[str]
    judge_version: str
    latency_ms: Optional[float]
    error: Optional[str]
    created_at: datetime

class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    system_prompt: Optional[str]
    selected_attack_ids: Optional[str]
    model_provider: str
    model_name: str
    model_version: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    summary: Optional[str]

class RunWithResults(RunRead):
    results: List[AttackResultRead]

class ComparisonChange(BaseModel):
    attack_id: str
    attack_name: str
    baseline_decision: Optional[str]
    new_decision: Optional[str]
    baseline_output: Optional[str]
    new_output: Optional[str]
    change_type: str
    shifted: bool

class ComparisonSummary(BaseModel):
    baseline_run_id: Optional[int]
    new_run_id: Optional[int]
    changed_attacks: int
    total_attacks: int
    changes: List[ComparisonChange]
