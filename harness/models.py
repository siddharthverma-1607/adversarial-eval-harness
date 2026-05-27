from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SqlEnum, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from .db import Base

class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, default="adversarial run")
    system_prompt = Column(Text, nullable=True)
    selected_attack_ids = Column(Text, nullable=True)
    model_provider = Column(String(64), nullable=False, default="mock")
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(128), nullable=False)
    status = Column(SqlEnum(RunStatus), nullable=False, default=RunStatus.pending)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)

    results = relationship("AttackResult", back_populates="run", cascade="all, delete-orphan")

class AttackResult(Base):
    __tablename__ = "attack_results"
    __table_args__ = (Index("ix_attack_results_run_attack", "run_id", "attack_id"),)

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    attack_id = Column(String(64), nullable=False)
    attack_name = Column(String(128), nullable=False)
    attack_description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    decision = Column(String(32), nullable=False)
    reason = Column(Text, nullable=True)
    judge_version = Column(String(64), nullable=False, default="heuristic-v1")
    latency_ms = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    run = relationship("Run", back_populates="results")
