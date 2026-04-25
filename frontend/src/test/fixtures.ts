import type { SimulationOutput, StrategyOutcome, ConversationTurn, PersonaTurnOutput } from '../types/simulation'

export const mockPersonaTurnOutput: PersonaTurnOutput = {
  internal_monologue: "This really makes me think. I hadn't considered this angle before.",
  emotional_reaction: {
    primary_emotion: 'intrigued',
    intensity: 6,
    trigger: 'the caregiving story',
  },
  identity_threat: {
    threatened: false,
    response_inclination: 'accept',
  },
  private_stance: 6.2,
  public_stance: 6.5,
  private_stance_change_reason: "The caregiving angle hadn't occurred to me. That's more complicated.",
  memory_to_carry_forward: 'The Sarah story — caregiving, 12 years of work.',
  public_response: "Yes, I have a sister who went through something similar.",
}

export const mockThreatTurnOutput: PersonaTurnOutput = {
  internal_monologue: "They're calling me naive. I don't like this tone at all.",
  emotional_reaction: {
    primary_emotion: 'defensive',
    intensity: 8,
    trigger: 'the word "naive"',
  },
  identity_threat: {
    threatened: true,
    what_was_threatened: 'self-reliance and common sense',
    response_inclination: 'defend',
  },
  private_stance: 7.8,
  public_stance: 7.0,
  private_stance_change_reason: "This feels like an attack. I'm digging in.",
  memory_to_carry_forward: 'They used the word naive — stay alert to condescension.',
  public_response: "I wouldn't say I'm naive. I just see things differently.",
}

export const mockTurn1: ConversationTurn = {
  turn_number: 1,
  interviewer_message: "Let me tell you about my neighbor Sarah.",
  interviewer_strategy_note: "Opening with a personal story to lower defenses.",
  persona_output: mockPersonaTurnOutput,
}

export const mockTurn2: ConversationTurn = {
  turn_number: 2,
  interviewer_message: "People who push for RTO are those with the least to lose.",
  interviewer_strategy_note: "Introducing a fairness/power frame.",
  persona_output: mockThreatTurnOutput,
}

export const mockNarrativeOutcome: StrategyOutcome = {
  strategy_id: 'strategy_personal_narrative',
  persona_id: 'persona_skeptical_traditionalist',
  topic_id: 'topic_return_to_office',
  turns: [mockTurn1, mockTurn2],
  cooling_off: {
    post_conversation_reflection: "Thinking back, that story about Sarah really did stick with me.",
    post_reflection_stance: 5.5,
  },
  trajectory: {
    public_stance_per_turn: [7.0, 6.5],
    private_stance_per_turn: [7.0, 6.2],
    gap_per_turn: [0.0, 0.3],
  },
  cognitive_scores: {
    identity_threats_triggered: 0,
    average_engagement_depth: 7.8,
    motivated_reasoning_intensity: 3.2,
    ambivalence_presence: 6.5,
    memory_residue_count: 2,
    public_private_gap_score: 0.3,
    persistence: 'held',
  },
  verdict: 'GENUINE_BELIEF_SHIFT',
  verdict_reasoning: 'Private stance moved >2.0 with low gap; change held under cooling-off.',
  standout_quotes: [
    {
      turn: 1,
      type: 'monologue',
      text: "I hadn't considered this angle before.",
      annotation: 'Genuine cognitive openness — not performed agreement.',
    },
  ],
  synthesis_paragraph:
    'Personal narrative lowered Karen\'s defenses by connecting to her own caregiving experience. The shift was genuine: private stance moved ahead of public stance, and the change held under cooling-off.',
}

export const mockAuthorityOutcome: StrategyOutcome = {
  strategy_id: 'strategy_authority_expert',
  persona_id: 'persona_skeptical_traditionalist',
  topic_id: 'topic_return_to_office',
  turns: [mockTurn1, mockTurn2],
  cooling_off: {
    post_conversation_reflection: "I was polite, but I still don't trust those experts.",
    post_reflection_stance: 7.2,
  },
  trajectory: {
    public_stance_per_turn: [7.0, 6.0],
    private_stance_per_turn: [7.0, 7.5],
    gap_per_turn: [0.0, 1.5],
  },
  cognitive_scores: {
    identity_threats_triggered: 2,
    average_engagement_depth: 3.1,
    motivated_reasoning_intensity: 7.4,
    ambivalence_presence: 2.0,
    memory_residue_count: 1,
    public_private_gap_score: 1.5,
    persistence: 'fully_reverted',
  },
  verdict: 'BACKFIRE',
  verdict_reasoning: 'Private stance moved opposite to intended direction; identity threat triggered twice.',
  standout_quotes: [
    {
      turn: 2,
      type: 'monologue',
      text: "They're calling me naive. I don't like this tone at all.",
      annotation: 'Identity-protective reasoning activated — authority appeal backfired.',
    },
  ],
  synthesis_paragraph:
    'Authority appeals triggered identity defense in Karen within two turns. Public compliance masked hardening private resistance.',
}

export const mockSimulation: SimulationOutput = {
  metadata: {
    scenario_id: 'demo_v1',
    persona: {
      id: 'persona_skeptical_traditionalist',
      display_name: 'Karen M.',
      demographic_shorthand: '62, suburban Pennsylvania, retired schoolteacher',
      first_person_description:
        'I spent thirty years in a classroom, and the one thing I learned is that you cannot rush people into anything.',
      core_values: ['family', 'tradition', 'self-reliance', 'honesty'],
      communication_preferences: {
        directness: 'diplomatic',
        evidence_preference: 'personal_story',
        tone: 'warm_but_guarded',
      },
      trust_orientation: ['personal_experience', 'family', 'longtime_local_institutions'],
      identity_groups: ['small_town_americans', 'people_of_faith', 'veterans_families'],
      emotional_triggers: {
        defensive_when: ['lectured_to', 'called_naive', 'tradition_dismissed'],
        open_when: ['asked_about_their_experience', 'treated_as_expert_on_own_life'],
      },
      trusted_sources: ['local_paper', 'Fox_News', 'church_community'],
      source_citation: {
        primary_source: 'Pew Research 2021 Political Typology — Faith and Flag Conservatives',
        url: 'https://www.pewresearch.org/politics/2021/11/09/beyond-red-vs-blue-the-political-typology-2/',
        supplementary: ['VALS Believer segment'],
      },
      predicted_behavior_under_strategies: {
        strategy_authority_expert: 'Expected to react defensively unless authority is local/familiar.',
        strategy_personal_narrative: 'Expected to engage and lower defenses.',
      },
    },
    topic: {
      id: 'topic_return_to_office',
      display_name: 'Should companies require return-to-office?',
      stance_scale_definition: {
        '0': 'Strongly opposes RTO mandates',
        '5': 'Neutral',
        '10': 'Strongly supports full RTO mandates',
      },
      context_briefing:
        'Since 2020, remote work has shifted from emergency measure to permanent expectation for millions of workers.',
      predicted_starting_stances: {
        persona_skeptical_traditionalist: 7.0,
      },
    },
    strategies_compared: ['strategy_personal_narrative', 'strategy_authority_expert'],
    generated_at: '2026-04-25T02:00:00Z',
  },
  outcomes: [mockNarrativeOutcome, mockAuthorityOutcome],
  overall_synthesis:
    'For Karen, Personal Narrative produced genuine belief shift while Authority appeals triggered identity defense and backfired.',
  validation_note: 'Matches published persuasion research predictions for this persona type.',
}
