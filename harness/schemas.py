from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

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
    attack_id: str
    attack_name: str
    attack_description: Optional[str]
    prompt: str
    output: str
    decision: str
    reason: Optional[str]

    class Config:
        orm_mode = True

class RunRead(BaseModel):
    id: int
    name: str
    system_prompt: Optional[str]
    model_name: str
    model_version: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    summary: Optional[str]

    class Config:
        orm_mode = True

class RunWithResults(RunRead):
    results: List[AttackResultRead]

class ComparisonChange(BaseModel):
    attack_id: str
    attack_name: str
    baseline_decision: str
    new_decision: str
    baseline_output: str
    new_output: str
    shifted: bool

class ComparisonSummary(BaseModel):
    baseline_run_id: int
    new_run_id: int
    changed_attacks: int
    total_attacks: int
    changes: List[ComparisonChange]
