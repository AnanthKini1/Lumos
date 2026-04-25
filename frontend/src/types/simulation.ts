/**
 * SHARED / LOCKED — Do not change without team sync.
 *
 * TypeScript interfaces mirroring every Pydantic model in backend/models.py.
 * WS-C imports exclusively from this file when working with simulation data.
 * No ad-hoc type definitions for simulation shapes anywhere else in the frontend.
 *
 * Any change here requires the same team sync as changes to backend/models.py
 * because it breaks frontend rendering and/or backend serialization simultaneously.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type PrimaryEmotion =
  | 'defensive'
  | 'curious'
  | 'dismissed'
  | 'engaged'
  | 'bored'
  | 'threatened'
  | 'warm'
  | 'frustrated'
  | 'intrigued'

export type ResponseInclination = 'defend' | 'withdraw' | 'attack' | 'accept'

export type VerdictCategory =
  | 'GENUINE_BELIEF_SHIFT'
  | 'PARTIAL_SHIFT'
  | 'SURFACE_COMPLIANCE'
  | 'BACKFIRE'
  | 'NO_MOVEMENT'

export type PersistenceResult = 'held' | 'partially_reverted' | 'fully_reverted'

// ---------------------------------------------------------------------------
// Input data schemas (personas, strategies, topics)
// ---------------------------------------------------------------------------

export interface CommunicationPreferences {
  directness: string
  evidence_preference: string
  tone: string
}

export interface EmotionalTriggers {
  defensive_when: string[]
  open_when: string[]
}

export interface SourceCitation {
  primary_source: string
  url?: string
  supplementary: string[]
}

export interface PersonaProfile {
  id: string
  display_name: string
  demographic_shorthand: string
  first_person_description: string
  core_values: string[]
  communication_preferences: CommunicationPreferences
  trust_orientation: string[]
  identity_groups: string[]
  emotional_triggers: EmotionalTriggers
  trusted_sources: string[]
  source_citation: SourceCitation
  predicted_behavior_under_strategies: Record<string, string>
}

export interface AcademicCitation {
  framework: string
  primary_source: string
  url?: string
}

export interface StrategyDefinition {
  id: string
  display_name: string
  one_line_description: string
  academic_citation: AcademicCitation
  persuader_system_prompt: string
  predicted_effective_on: string[]
  predicted_ineffective_on: string[]
}

export interface TopicProfile {
  id: string
  display_name: string
  stance_scale_definition: Record<string, string>
  context_briefing: string
  predicted_starting_stances: Record<string, number>
}

// ---------------------------------------------------------------------------
// Per-turn agent output schemas
// ---------------------------------------------------------------------------

export interface EmotionalReaction {
  primary_emotion: PrimaryEmotion
  intensity: number
  trigger: string
}

export interface IdentityThreat {
  threatened: boolean
  what_was_threatened?: string
  response_inclination: ResponseInclination
}

export interface PersonaTurnOutput {
  internal_monologue: string
  emotional_reaction: EmotionalReaction
  identity_threat: IdentityThreat
  private_stance: number
  public_stance: number
  private_stance_change_reason: string
  memory_to_carry_forward: string
  public_response: string
}

export interface PersuaderOutput {
  message: string
  internal_strategy_note: string
}

export interface MechanismClassification {
  primary_mechanism_id: string
  secondary_mechanism_id?: string
  explanation: string
  evidence_quotes: string[]
  color_category: 'backfire' | 'genuine_persuasion' | 'surface_mechanism'
  intensity: number
}

export interface ConversationTurn {
  turn_number: number
  persuader_message: string
  persuader_strategy_note: string
  persona_output: PersonaTurnOutput
  // Pivotal-moment annotation fields
  stance_delta?: number
  is_pivotal?: boolean
  is_inflection_point?: boolean
  mechanism_classification?: MechanismClassification
  per_turn_cognitive_scores?: Record<string, number>
  color_category?: string
  intensity?: number
}

// ---------------------------------------------------------------------------
// Post-conversation schemas
// ---------------------------------------------------------------------------

export interface CoolingOff {
  post_conversation_reflection: string
  post_reflection_stance: number
}

export interface Trajectory {
  public_stance_per_turn: number[]
  private_stance_per_turn: number[]
  gap_per_turn: number[]
}

export interface CognitiveScores {
  identity_threats_triggered: number
  average_engagement_depth: number
  motivated_reasoning_intensity: number
  ambivalence_presence: number
  memory_residue_count: number
  public_private_gap_score: number
  persistence: PersistenceResult
}

export interface StandoutQuote {
  turn: number
  type: 'monologue' | 'public'
  text: string
  annotation: string
}

// ---------------------------------------------------------------------------
// Aggregated outcome
// ---------------------------------------------------------------------------

export interface StrategyOutcome {
  strategy_id: string
  persona_id: string
  topic_id: string
  turns: ConversationTurn[]
  cooling_off: CoolingOff
  trajectory: Trajectory
  cognitive_scores: CognitiveScores
  verdict: VerdictCategory
  verdict_reasoning: string
  standout_quotes: StandoutQuote[]
  synthesis_paragraph: string
}

// ---------------------------------------------------------------------------
// Top-level simulation output file
// ---------------------------------------------------------------------------

export interface SimulationMetadata {
  scenario_id: string
  persona: PersonaProfile
  topic: TopicProfile
  strategies_compared: string[]
  generated_at: string
}

export interface SimulationOutput {
  metadata: SimulationMetadata
  outcomes: StrategyOutcome[]
  overall_synthesis: string
  validation_note?: string
}
