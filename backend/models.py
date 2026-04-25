"""
SHARED / LOCKED — Do not change without team sync.

Single source of truth for all data shapes that cross workstream boundaries.
Pydantic models for every schema defined in Shared Contracts.

- WS-A reads: PersonaProfile, StrategyDefinition, TopicProfile
- WS-A writes: CognitiveScores, StandoutQuote (via scorer.py)
- WS-B reads and writes: all models
- WS-C reads: all models (via TypeScript mirrors in frontend/src/types/simulation.ts)

No business logic lives here — only data shapes and field validation.
Any field addition or rename breaks two other workstreams.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PrimaryEmotion(str, Enum):
    DEFENSIVE = "defensive"
    CURIOUS = "curious"
    DISMISSED = "dismissed"
    ENGAGED = "engaged"
    BORED = "bored"
    THREATENED = "threatened"
    WARM = "warm"
    FRUSTRATED = "frustrated"
    INTRIGUED = "intrigued"


class ResponseInclination(str, Enum):
    DEFEND = "defend"
    WITHDRAW = "withdraw"
    ATTACK = "attack"
    ACCEPT = "accept"


class VerdictCategory(str, Enum):
    GENUINE_BELIEF_SHIFT = "GENUINE_BELIEF_SHIFT"
    PARTIAL_SHIFT = "PARTIAL_SHIFT"
    SURFACE_COMPLIANCE = "SURFACE_COMPLIANCE"
    BACKFIRE = "BACKFIRE"
    NO_MOVEMENT = "NO_MOVEMENT"


class PersistenceResult(str, Enum):
    HELD = "held"
    PARTIALLY_REVERTED = "partially_reverted"
    FULLY_REVERTED = "fully_reverted"


# ---------------------------------------------------------------------------
# Input data schemas (produced by WS-A, consumed by WS-B)
# ---------------------------------------------------------------------------

class CommunicationPreferences(BaseModel):
    directness: str
    evidence_preference: str
    tone: str


class EmotionalTriggers(BaseModel):
    defensive_when: list[str]
    open_when: list[str]


class SourceCitation(BaseModel):
    primary_source: str
    url: Optional[str] = None
    supplementary: list[str] = Field(default_factory=list)


class PersonaProfile(BaseModel):
    id: str
    display_name: str
    demographic_shorthand: str
    first_person_description: str
    core_values: list[str]
    communication_preferences: CommunicationPreferences
    trust_orientation: list[str]
    identity_groups: list[str]
    emotional_triggers: EmotionalTriggers
    trusted_sources: list[str]
    source_citation: SourceCitation
    predicted_behavior_under_strategies: dict[str, str] = Field(default_factory=dict)


class AcademicCitation(BaseModel):
    framework: str
    primary_source: str
    url: Optional[str] = None


class StrategyDefinition(BaseModel):
    id: str
    display_name: str
    one_line_description: str
    academic_citation: AcademicCitation
    persuader_system_prompt: str
    predicted_effective_on: list[str] = Field(default_factory=list)
    predicted_ineffective_on: list[str] = Field(default_factory=list)


class StanceScaleDefinition(BaseModel):
    model_config = {"populate_by_name": True}

    low: str = Field(alias="0")
    mid: str = Field(alias="5")
    high: str = Field(alias="10")


class KeyStatistic(BaseModel):
    claim: str
    source: str
    direction: str = ""  # "supports_stance_10" | "supports_stance_0" | "neutral"


class TopicProfile(BaseModel):
    id: str
    display_name: str
    stance_scale_definition: dict[str, str]
    context_briefing: str
    predicted_starting_stances: dict[str, float] = Field(default_factory=dict)
    key_statistics: list[KeyStatistic] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Per-turn agent output schemas (produced by WS-B, consumed by frontend)
# ---------------------------------------------------------------------------

class EmotionalReaction(BaseModel):
    primary_emotion: PrimaryEmotion
    intensity: int = Field(ge=0, le=10)
    trigger: str


class IdentityThreat(BaseModel):
    threatened: bool
    what_was_threatened: Optional[str] = None
    response_inclination: ResponseInclination


class PersonaTurnOutput(BaseModel):
    internal_monologue: str
    emotional_reaction: EmotionalReaction
    identity_threat: IdentityThreat
    private_stance: float = Field(ge=0.0, le=10.0)
    public_stance: float = Field(ge=0.0, le=10.0)
    private_stance_change_reason: str
    memory_to_carry_forward: str
    public_response: str


class PersuaderOutput(BaseModel):
    message: str
    internal_strategy_note: str


class MechanismClassification(BaseModel):
    primary_mechanism_id: str
    secondary_mechanism_id: Optional[str] = None
    explanation: str
    evidence_quotes: list[str] = Field(default_factory=list)
    color_category: Literal["backfire", "genuine_persuasion", "surface_mechanism"]
    intensity: float = Field(ge=0.0, le=1.0)


class ConversationTurn(BaseModel):
    turn_number: int
    persuader_message: str
    persuader_strategy_note: str
    persona_output: PersonaTurnOutput
    # Pivotal-moment annotation fields — added after conversation completes
    stance_delta: float = 0.0
    is_pivotal: bool = False
    is_inflection_point: bool = False
    mechanism_classification: Optional[MechanismClassification] = None
    per_turn_cognitive_scores: Optional[dict[str, float]] = None
    color_category: Optional[str] = None
    intensity: Optional[float] = None


# ---------------------------------------------------------------------------
# Post-conversation schemas
# ---------------------------------------------------------------------------

class CoolingOff(BaseModel):
    post_conversation_reflection: str
    post_reflection_stance: float = Field(ge=0.0, le=10.0)


class Trajectory(BaseModel):
    public_stance_per_turn: list[float]
    private_stance_per_turn: list[float]
    gap_per_turn: list[float]


class CognitiveScores(BaseModel):
    identity_threats_triggered: int
    average_engagement_depth: float = Field(ge=0.0, le=10.0)
    motivated_reasoning_intensity: float = Field(ge=0.0, le=10.0)
    ambivalence_presence: float = Field(ge=0.0, le=10.0)
    memory_residue_count: int
    public_private_gap_score: float = Field(ge=0.0, le=10.0)
    persistence: PersistenceResult


class StandoutQuote(BaseModel):
    turn: int
    type: Literal["monologue", "public"]
    text: str
    annotation: str


# ---------------------------------------------------------------------------
# Aggregated outcome schema (produced by WS-B pipeline + WS-A judge)
# ---------------------------------------------------------------------------

class StrategyOutcome(BaseModel):
    strategy_id: str
    persona_id: str
    topic_id: str
    turns: list[ConversationTurn]
    cooling_off: CoolingOff
    trajectory: Trajectory
    cognitive_scores: CognitiveScores
    verdict: VerdictCategory
    verdict_reasoning: str
    standout_quotes: list[StandoutQuote]
    synthesis_paragraph: str


# ---------------------------------------------------------------------------
# Top-level simulation output file schema
# ---------------------------------------------------------------------------

class SimulationMetadata(BaseModel):
    scenario_id: str
    persona: PersonaProfile
    topic: TopicProfile
    strategies_compared: list[str]
    generated_at: str


class SimulationOutput(BaseModel):
    metadata: SimulationMetadata
    outcomes: list[StrategyOutcome]
    overall_synthesis: str
    validation_note: Optional[str] = None
