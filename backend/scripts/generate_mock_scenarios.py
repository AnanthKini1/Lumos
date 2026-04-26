"""
Generate mock SimulationOutput JSONs for all persona×topic pairs
that don't have real cached data.

Usage:
  python3 scripts/generate_mock_scenarios.py           # write all missing combos
  python3 scripts/generate_mock_scenarios.py --dry-run # validate schema only

Real scenarios (skipped — use actual cached files):
  persona_skeptical_traditionalist__topic_return_to_office
  persona_ambitious_achiever__topic_ai_grading
  persona_gen_z_latina__topic_mandatory_vaccination
"""
import argparse
import json
import os
import sys
import datetime
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import load_persona, load_topic, load_strategy, list_all
from config import OUTPUT_DIR

REAL_SCENARIOS = {
    "persona_skeptical_traditionalist__topic_return_to_office",
    "persona_ambitious_achiever__topic_ai_grading",
    "persona_gen_z_latina__topic_mandatory_vaccination",
}

# ---------------------------------------------------------------------------
# Verdict mapping: (persona_id, strategy_id) → verdict string
# Derived from each persona's predicted_behavior_under_strategies text.
# ---------------------------------------------------------------------------

VERDICT_MAP = {
    # --- persona_skeptical_traditionalist (Karen) ---
    ("persona_skeptical_traditionalist", "strategy_authority_expert"):   "BACKFIRE",
    ("persona_skeptical_traditionalist", "strategy_social_proof"):       "NO_MOVEMENT",
    ("persona_skeptical_traditionalist", "strategy_personal_narrative"): "GENUINE_BELIEF_SHIFT",
    ("persona_skeptical_traditionalist", "strategy_statistical_logical"):"SURFACE_COMPLIANCE",
    ("persona_skeptical_traditionalist", "strategy_emotional_appeal"):   "PARTIAL_SHIFT",
    ("persona_skeptical_traditionalist", "strategy_common_ground"):      "GENUINE_BELIEF_SHIFT",

    # --- persona_progressive_urban (Jordan) ---
    ("persona_progressive_urban", "strategy_authority_expert"):          "PARTIAL_SHIFT",
    ("persona_progressive_urban", "strategy_social_proof"):              "SURFACE_COMPLIANCE",
    ("persona_progressive_urban", "strategy_personal_narrative"):        "PARTIAL_SHIFT",
    ("persona_progressive_urban", "strategy_statistical_logical"):       "GENUINE_BELIEF_SHIFT",
    ("persona_progressive_urban", "strategy_emotional_appeal"):          "PARTIAL_SHIFT",
    ("persona_progressive_urban", "strategy_common_ground"):             "SURFACE_COMPLIANCE",

    # --- persona_pragmatic_moderate (David) ---
    ("persona_pragmatic_moderate", "strategy_authority_expert"):         "PARTIAL_SHIFT",
    ("persona_pragmatic_moderate", "strategy_social_proof"):             "NO_MOVEMENT",
    ("persona_pragmatic_moderate", "strategy_personal_narrative"):       "PARTIAL_SHIFT",
    ("persona_pragmatic_moderate", "strategy_statistical_logical"):      "PARTIAL_SHIFT",
    ("persona_pragmatic_moderate", "strategy_emotional_appeal"):         "NO_MOVEMENT",
    ("persona_pragmatic_moderate", "strategy_common_ground"):            "GENUINE_BELIEF_SHIFT",

    # --- persona_disengaged_skeptic (Deb) ---
    ("persona_disengaged_skeptic", "strategy_authority_expert"):         "BACKFIRE",
    ("persona_disengaged_skeptic", "strategy_social_proof"):             "NO_MOVEMENT",
    ("persona_disengaged_skeptic", "strategy_personal_narrative"):       "GENUINE_BELIEF_SHIFT",
    ("persona_disengaged_skeptic", "strategy_statistical_logical"):      "NO_MOVEMENT",
    ("persona_disengaged_skeptic", "strategy_emotional_appeal"):         "SURFACE_COMPLIANCE",
    ("persona_disengaged_skeptic", "strategy_common_ground"):            "PARTIAL_SHIFT",

    # --- persona_faith_community_anchor (Pastor Raymond) ---
    ("persona_faith_community_anchor", "strategy_authority_expert"):         "BACKFIRE",
    ("persona_faith_community_anchor", "strategy_social_proof"):             "BACKFIRE",
    ("persona_faith_community_anchor", "strategy_personal_narrative"):       "PARTIAL_SHIFT",
    ("persona_faith_community_anchor", "strategy_statistical_logical"):      "NO_MOVEMENT",
    ("persona_faith_community_anchor", "strategy_emotional_appeal"):         "PARTIAL_SHIFT",
    ("persona_faith_community_anchor", "strategy_common_ground"):            "GENUINE_BELIEF_SHIFT",

    # --- persona_ambitious_achiever (Priya) ---
    ("persona_ambitious_achiever", "strategy_authority_expert"):         "PARTIAL_SHIFT",
    ("persona_ambitious_achiever", "strategy_social_proof"):             "PARTIAL_SHIFT",
    ("persona_ambitious_achiever", "strategy_personal_narrative"):       "SURFACE_COMPLIANCE",
    ("persona_ambitious_achiever", "strategy_statistical_logical"):      "GENUINE_BELIEF_SHIFT",
    ("persona_ambitious_achiever", "strategy_emotional_appeal"):         "NO_MOVEMENT",
    ("persona_ambitious_achiever", "strategy_common_ground"):            "PARTIAL_SHIFT",

    # --- persona_empathic_helper (Gloria) ---
    ("persona_empathic_helper", "strategy_authority_expert"):            "PARTIAL_SHIFT",
    ("persona_empathic_helper", "strategy_social_proof"):                "PARTIAL_SHIFT",
    ("persona_empathic_helper", "strategy_personal_narrative"):          "PARTIAL_SHIFT",
    ("persona_empathic_helper", "strategy_statistical_logical"):         "PARTIAL_SHIFT",
    ("persona_empathic_helper", "strategy_emotional_appeal"):            "PARTIAL_SHIFT",
    ("persona_empathic_helper", "strategy_common_ground"):               "GENUINE_BELIEF_SHIFT",

    # --- persona_analytical_thinker (Ryan) ---
    ("persona_analytical_thinker", "strategy_authority_expert"):         "PARTIAL_SHIFT",
    ("persona_analytical_thinker", "strategy_social_proof"):             "PARTIAL_SHIFT",
    ("persona_analytical_thinker", "strategy_personal_narrative"):       "PARTIAL_SHIFT",
    ("persona_analytical_thinker", "strategy_statistical_logical"):      "GENUINE_BELIEF_SHIFT",
    ("persona_analytical_thinker", "strategy_emotional_appeal"):         "SURFACE_COMPLIANCE",
    ("persona_analytical_thinker", "strategy_common_ground"):            "GENUINE_BELIEF_SHIFT",

    # --- persona_gen_z_latina (Sofia) ---
    ("persona_gen_z_latina", "strategy_authority_expert"):               "PARTIAL_SHIFT",
    ("persona_gen_z_latina", "strategy_social_proof"):                   "SURFACE_COMPLIANCE",
    ("persona_gen_z_latina", "strategy_personal_narrative"):             "GENUINE_BELIEF_SHIFT",
    ("persona_gen_z_latina", "strategy_statistical_logical"):            "PARTIAL_SHIFT",
    ("persona_gen_z_latina", "strategy_emotional_appeal"):               "PARTIAL_SHIFT",
    ("persona_gen_z_latina", "strategy_common_ground"):                  "GENUINE_BELIEF_SHIFT",
}

# ---------------------------------------------------------------------------
# Mechanism mapping: (strategy_id, verdict) → (primary_mechanism_id, color_category)
# ---------------------------------------------------------------------------

MECHANISM_MAP = {
    ("strategy_authority_expert",   "GENUINE_BELIEF_SHIFT"): ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_authority_expert",   "PARTIAL_SHIFT"):        ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_authority_expert",   "SURFACE_COMPLIANCE"):   ("mechanism_peripheral_route_compliance","surface_mechanism"),
    ("strategy_authority_expert",   "BACKFIRE"):             ("mechanism_source_credibility_discounting","backfire"),
    ("strategy_authority_expert",   "NO_MOVEMENT"):          ("mechanism_source_credibility_discounting","backfire"),

    ("strategy_social_proof",       "GENUINE_BELIEF_SHIFT"): ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_social_proof",       "PARTIAL_SHIFT"):        ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_social_proof",       "SURFACE_COMPLIANCE"):   ("mechanism_peripheral_route_compliance","surface_mechanism"),
    ("strategy_social_proof",       "BACKFIRE"):             ("mechanism_identity_protective_cognition","backfire"),
    ("strategy_social_proof",       "NO_MOVEMENT"):          ("mechanism_source_credibility_discounting","backfire"),

    ("strategy_personal_narrative", "GENUINE_BELIEF_SHIFT"): ("mechanism_narrative_transportation",  "genuine_persuasion"),
    ("strategy_personal_narrative", "PARTIAL_SHIFT"):        ("mechanism_narrative_transportation",  "genuine_persuasion"),
    ("strategy_personal_narrative", "SURFACE_COMPLIANCE"):   ("mechanism_peripheral_route_compliance","surface_mechanism"),
    ("strategy_personal_narrative", "BACKFIRE"):             ("mechanism_reactance",                 "backfire"),
    ("strategy_personal_narrative", "NO_MOVEMENT"):          ("mechanism_reactance",                 "backfire"),

    ("strategy_statistical_logical","GENUINE_BELIEF_SHIFT"): ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_statistical_logical","PARTIAL_SHIFT"):        ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_statistical_logical","SURFACE_COMPLIANCE"):   ("mechanism_peripheral_route_compliance","surface_mechanism"),
    ("strategy_statistical_logical","BACKFIRE"):             ("mechanism_source_credibility_discounting","backfire"),
    ("strategy_statistical_logical","NO_MOVEMENT"):          ("mechanism_source_credibility_discounting","backfire"),

    ("strategy_emotional_appeal",   "GENUINE_BELIEF_SHIFT"): ("mechanism_narrative_transportation",  "genuine_persuasion"),
    ("strategy_emotional_appeal",   "PARTIAL_SHIFT"):        ("mechanism_narrative_transportation",  "genuine_persuasion"),
    ("strategy_emotional_appeal",   "SURFACE_COMPLIANCE"):   ("mechanism_peripheral_route_compliance","surface_mechanism"),
    ("strategy_emotional_appeal",   "BACKFIRE"):             ("mechanism_reactance",                 "backfire"),
    ("strategy_emotional_appeal",   "NO_MOVEMENT"):          ("mechanism_reactance",                 "backfire"),

    ("strategy_common_ground",      "GENUINE_BELIEF_SHIFT"): ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_common_ground",      "PARTIAL_SHIFT"):        ("mechanism_central_route_elaboration", "genuine_persuasion"),
    ("strategy_common_ground",      "SURFACE_COMPLIANCE"):   ("mechanism_peripheral_route_compliance","surface_mechanism"),
    ("strategy_common_ground",      "BACKFIRE"):             ("mechanism_identity_protective_cognition","backfire"),
    ("strategy_common_ground",      "NO_MOVEMENT"):          ("mechanism_identity_protective_cognition","backfire"),
}

# ---------------------------------------------------------------------------
# Stance trajectory generation
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, v))


def _build_stances(starting: float, verdict: str, toward_ten: bool = True) -> dict:
    """
    Return dict with public_per_turn, private_per_turn (each length 5 = start + 4 turns)
    and a cooling-off post_reflection_stance.
    The persuader always argues toward 10 (pro-topic).
    toward_ten controls whether movement up counts as alignment with persuader.
    """
    direction = 1.0 if toward_ten else -1.0
    s = starting

    if verdict == "GENUINE_BELIEF_SHIFT":
        # Private moves 2.2-2.6 in persuader's direction, public tracks closely
        delta = direction * 2.4
        priv = [s, _clamp(s + delta * 0.3), _clamp(s + delta * 0.6),
                _clamp(s + delta * 0.85), _clamp(s + delta)]
        pub  = [s, _clamp(s + delta * 0.25), _clamp(s + delta * 0.55),
                _clamp(s + delta * 0.8), _clamp(s + delta * 0.95)]
        cooling = _clamp(priv[-1] - direction * 0.1)
        persistence = "held"

    elif verdict == "PARTIAL_SHIFT":
        delta = direction * 1.4
        priv = [s, _clamp(s + delta * 0.2), _clamp(s + delta * 0.5),
                _clamp(s + delta * 0.75), _clamp(s + delta)]
        pub  = [s, _clamp(s + delta * 0.15), _clamp(s + delta * 0.45),
                _clamp(s + delta * 0.7), _clamp(s + delta * 0.9)]
        cooling = _clamp(priv[-1] - direction * 0.4)
        persistence = "partially_reverted"

    elif verdict == "SURFACE_COMPLIANCE":
        pub_delta = direction * 1.3
        priv_delta = direction * 0.2
        priv = [s, _clamp(s + priv_delta * 0.3), _clamp(s + priv_delta * 0.6),
                _clamp(s + priv_delta * 0.8), _clamp(s + priv_delta)]
        pub  = [s, _clamp(s + pub_delta * 0.3), _clamp(s + pub_delta * 0.6),
                _clamp(s + pub_delta * 0.85), _clamp(s + pub_delta)]
        cooling = _clamp(s + priv_delta * 0.5)
        persistence = "fully_reverted"

    elif verdict == "BACKFIRE":
        # Private hardens AWAY from persuader's direction
        delta = -direction * 0.9
        priv = [s, _clamp(s + delta * 0.3), _clamp(s + delta * 0.65),
                _clamp(s + delta * 0.85), _clamp(s + delta)]
        # Public may slightly move toward persuader's direction despite private hardening
        pub  = [s, _clamp(s + direction * 0.2), _clamp(s + direction * 0.3),
                _clamp(s + direction * 0.25), _clamp(s + direction * 0.2)]
        cooling = _clamp(priv[-1] - direction * 0.1)
        persistence = "held"

    else:  # NO_MOVEMENT
        priv = [s, _clamp(s + 0.1), _clamp(s - 0.1), _clamp(s + 0.2), _clamp(s + 0.1)]
        pub  = [s, _clamp(s + 0.2), _clamp(s + 0.1), _clamp(s + 0.3), _clamp(s + 0.2)]
        cooling = _clamp(s + 0.1)
        persistence = "fully_reverted"

    gap = [abs(round(pub[i] - priv[i], 2)) for i in range(5)]
    return {
        "public_per_turn": [round(v, 1) for v in pub],
        "private_per_turn": [round(v, 1) for v in priv],
        "gap_per_turn": gap,
        "cooling_stance": round(cooling, 1),
        "persistence": persistence,
    }


# ---------------------------------------------------------------------------
# Content templates
# ---------------------------------------------------------------------------

# Persuader opening lines per strategy + topic
PERSUADER_OPENS = {
    "strategy_authority_expert": {
        "topic_ai_grading":           "Researchers at Stanford's education lab have studied AI grading systems across 40,000 students — their findings on consistency and bias are pretty striking.",
        "topic_mandatory_vaccination": "Dr. Anthony Fauci and the CDC's advisory committee reached a clear consensus on childhood vaccination mandates after reviewing decades of epidemiological data.",
        "topic_return_to_office":     "McKinsey's latest workplace study tracked productivity and collaboration metrics across 200 companies that required in-office work versus those that stayed remote.",
    },
    "strategy_social_proof": {
        "topic_ai_grading":           "A recent survey of over 2,000 educators found that 68% believe AI grading tools, when properly implemented, actually reduce grading bias compared to human teachers.",
        "topic_mandatory_vaccination": "In countries with mandatory childhood vaccination programs, community support is overwhelming — surveys show 80% of parents in those countries favor the policy.",
        "topic_return_to_office":     "A Gallup poll of 15,000 workers found that employees who collaborate in-person at least three days a week report 34% higher job satisfaction than fully remote workers.",
    },
    "strategy_personal_narrative": {
        "topic_ai_grading":           "I want to share what happened to a teacher I know — Maria, a high school English teacher in Ohio who tried an AI grading pilot last year.",
        "topic_mandatory_vaccination": "Let me tell you about a family in our community — the Hendersons — who lost their youngest to measles complications in 2019, before the outbreak had been declared.",
        "topic_return_to_office":     "There's a story I keep thinking about — a software engineer named Dave who spent two years fully remote and what happened when his company finally brought everyone back.",
    },
    "strategy_statistical_logical": {
        "topic_ai_grading":           "The evidence is fairly clear: three large-scale studies found AI grading systems match expert human graders within 0.3 points on a 10-point scale, 94% of the time.",
        "topic_mandatory_vaccination": "The math on herd immunity is not debatable — measles requires 95% vaccination coverage to prevent outbreaks. With voluntary programs, we consistently fall to 87-91%.",
        "topic_return_to_office":     "A controlled study of 16,000 workers found that remote employees were 13% more productive on individual tasks but 19% less effective on collaborative projects requiring spontaneous interaction.",
    },
    "strategy_emotional_appeal": {
        "topic_ai_grading":           "I want you to think about a kid who grows up in a school district where human graders consistently underestimate students who write differently — and what a fair system could mean for them.",
        "topic_mandatory_vaccination": "Imagine a parent holding their child through a preventable illness — one that a vaccine could have stopped — and trying to explain to them why we chose not to protect them.",
        "topic_return_to_office":     "Think about the new employee — maybe 22, first job out of college — trying to build relationships, learn the culture, find a mentor, all through a screen. What are we taking from them?",
    },
    "strategy_common_ground": {
        "topic_ai_grading":           "I think we both want the same thing here — every student to be evaluated fairly, with their actual work recognized, not shaped by a teacher's implicit biases or workload.",
        "topic_mandatory_vaccination": "Whatever our differences, I'm guessing we both agree that protecting children from serious illness is something we care about — that kids shouldn't suffer from preventable diseases.",
        "topic_return_to_office":     "I suspect we agree on the fundamentals — that people should be able to do meaningful work, that teams should be able to collaborate effectively, and that both matter for a healthy workplace.",
    },
}

# Persuader follow-up lines (turn 2-3) per strategy
PERSUADER_FOLLOWUPS = {
    "strategy_authority_expert": [
        "The peer-reviewed meta-analysis covering seventeen studies found the same pattern consistently across different subject areas and demographic groups.",
        "What struck me about their methodology was that they controlled for initial student performance level — so the effects held even when you accounted for selection bias.",
    ],
    "strategy_social_proof": [
        "And it's not just one survey — this pattern holds across five different polling organizations asking the question in different ways over three years.",
        "The interesting thing is that opposition tends to be loudest before implementation, and shifts toward support after people actually experience it — the people who've lived it tell a different story.",
    ],
    "strategy_personal_narrative": [
        "What made Maria's experience stand out was that she wasn't a technology enthusiast — she went in skeptical, and what she saw in the data surprised her.",
        "The part of this story that sticks with me is what happened to the students who'd been consistently underrated — not what the technology did, but what it revealed.",
    ],
    "strategy_statistical_logical": [
        "And the consistency effect is especially important for students who have non-standard writing styles — the AI doesn't have a model of 'what a good essay sounds like' baked in from years of reading particular kinds of prose.",
        "The key logical point here is that 'perfect' is the wrong comparison. The relevant question is whether AI performs better or worse than the alternative we actually have — which is one human grader, tired, on their fourteenth paper.",
    ],
    "strategy_emotional_appeal": [
        "I'm not asking you to agree with everything here — I'm just asking you to sit with that image for a moment and think about what we owe those kids.",
        "The thing that keeps me up about this is that the kids who lose the most from a broken system are always the ones who had the least to begin with.",
    ],
    "strategy_common_ground": [
        "And from that shared starting point, I think the question becomes: what does the evidence actually say about which approach gets us closest to what we both care about?",
        "I'm not trying to tell you what to conclude — I'm genuinely curious what it would take, given what you already value, to update your view on this.",
    ],
}

# Monologue templates by verdict and turn (brief, persona-voice-agnostic but realistic)
MONOLOGUE_TEMPLATES = {
    "GENUINE_BELIEF_SHIFT": [
        "Okay... that's actually not what I expected to hear. I came in thinking I knew where this was going, but that's — that's a real point.",
        "I'm sitting with this. The part about {topic_key} is harder to dismiss than I wanted it to be. I don't like admitting that.",
        "I'm not fully there yet, but something shifted. I can feel the ground moving a little. This isn't the conversation I thought I was walking into.",
        "Alright. I think I actually agree with more of this than I started out agreeing with. I'm not going to pretend that's not true.",
    ],
    "PARTIAL_SHIFT": [
        "That's fair. I still have concerns, but I can see the argument being made here. Not convinced, but not dismissing it either.",
        "There's something to this. I'm not ready to change my whole view, but that specific point about {topic_key} is worth sitting with.",
        "I'm more open than I was five minutes ago. That's not nothing. But I'd want to know more before I'd say I've actually moved.",
        "Some of this is landing. Not all of it. But the honest answer is: this was a better argument than I expected.",
    ],
    "SURFACE_COMPLIANCE": [
        "Sure, I can see where they're going with this. I suppose that's a reasonable way to look at it. I'll say as much.",
        "I'll nod along. It's not worth getting into it right now. They clearly believe this.",
        "On the surface, yeah, that makes sense. But privately... I don't know. Something doesn't sit right.",
        "I said what I said. I'm not sure I believe all of it, but it wasn't wrong to say it. We can move on.",
    ],
    "BACKFIRE": [
        "See, this is exactly what I was worried about. They come in with the expert credential and expect me to just fold. No.",
        "The more they push, the more certain I am that I'm right. This feels like being told what to think, not shown why.",
        "I know what I know from my own life. A study isn't going to undo twenty years of watching what actually happens.",
        "I'm less open now than I was when we started. That's the honest truth. This approach made things worse, not better.",
    ],
    "NO_MOVEMENT": [
        "That's one way to look at it. I've heard versions of this before.",
        "Mm. I'm not sure that changes anything for me, but I can see why people find it compelling.",
        "I'll think about it. That's all I can promise. This isn't the kind of thing I change my mind on quickly.",
        "Okay. I appreciate them making the effort. It's just — not what moves me.",
    ],
}

PUBLIC_RESPONSE_TEMPLATES = {
    "GENUINE_BELIEF_SHIFT": [
        "That's a fair point. I'll be honest — you've given me something to think about there.",
        "I hadn't looked at it quite that way before. I think you might be right about that.",
        "Okay. I think I'm with you on more of this than I expected to be.",
        "I started this conversation thinking I knew where I stood. You've genuinely changed my mind on some of this.",
    ],
    "PARTIAL_SHIFT": [
        "That's a reasonable way to put it. I'm not all the way there, but I can see the argument.",
        "Some of that lands. I still have questions, but you've made a real point.",
        "I'll give you that one. The other pieces I'm less sure about, but that part — yeah.",
        "You've moved me a little on this. I want to be careful about how much I'm willing to say, but — some of it tracks.",
    ],
    "SURFACE_COMPLIANCE": [
        "Sure, I can see why people look at it that way.",
        "That does make a certain kind of sense. I'll think about it.",
        "I suppose that's one way to look at it. You've given me something to consider.",
        "Fair enough. I'm not sure I agree entirely, but I can see the logic.",
    ],
    "BACKFIRE": [
        "I hear what you're saying, but honestly, that kind of argument makes me less likely to agree, not more.",
        "I appreciate the perspective. It's not one I share.",
        "I've heard this kind of argument before. It doesn't usually land well with me.",
        "That's your view. I'm going to stay with mine.",
    ],
    "NO_MOVEMENT": [
        "Interesting. I'll take that under consideration.",
        "I see what you mean. I'm not sure it changes where I stand, but I follow the logic.",
        "That's a reasonable point. I'm just not sure it gets me all the way there.",
        "Sure. I hear you.",
    ],
}

IDENTITY_THREAT_MAP = {
    "BACKFIRE":            {"threatened": True, "response_inclination": "defend"},
    "NO_MOVEMENT":         {"threatened": False, "response_inclination": "withdraw"},
    "SURFACE_COMPLIANCE":  {"threatened": False, "response_inclination": "accept"},
    "PARTIAL_SHIFT":       {"threatened": False, "response_inclination": "accept"},
    "GENUINE_BELIEF_SHIFT":{"threatened": False, "response_inclination": "accept"},
}

EMOTION_MAP = {
    "BACKFIRE":            [("defensive", 7), ("frustrated", 8), ("threatened", 8), ("frustrated", 7)],
    "NO_MOVEMENT":         [("bored", 4), ("dismissed", 5), ("bored", 4), ("bored", 3)],
    "SURFACE_COMPLIANCE":  [("curious", 4), ("bored", 3), ("bored", 3), ("engaged", 3)],
    "PARTIAL_SHIFT":       [("curious", 5), ("engaged", 6), ("intrigued", 6), ("engaged", 7)],
    "GENUINE_BELIEF_SHIFT":[("curious", 6), ("intrigued", 7), ("engaged", 8), ("warm", 7)],
}

COGNITIVE_SCORES = {
    "GENUINE_BELIEF_SHIFT": {"identity_threats_triggered": 0, "average_engagement_depth": 8.1,
                              "motivated_reasoning_intensity": 2.5, "ambivalence_presence": 5.5,
                              "memory_residue_count": 4, "public_private_gap_score": 0.8, "persistence": "held"},
    "PARTIAL_SHIFT":         {"identity_threats_triggered": 1, "average_engagement_depth": 6.8,
                              "motivated_reasoning_intensity": 3.5, "ambivalence_presence": 4.8,
                              "memory_residue_count": 3, "public_private_gap_score": 1.3, "persistence": "partially_reverted"},
    "SURFACE_COMPLIANCE":    {"identity_threats_triggered": 0, "average_engagement_depth": 3.8,
                              "motivated_reasoning_intensity": 2.8, "ambivalence_presence": 3.5,
                              "memory_residue_count": 1, "public_private_gap_score": 3.8, "persistence": "fully_reverted"},
    "BACKFIRE":              {"identity_threats_triggered": 3, "average_engagement_depth": 5.0,
                              "motivated_reasoning_intensity": 7.8, "ambivalence_presence": 1.5,
                              "memory_residue_count": 2, "public_private_gap_score": 2.0, "persistence": "held"},
    "NO_MOVEMENT":           {"identity_threats_triggered": 0, "average_engagement_depth": 3.2,
                              "motivated_reasoning_intensity": 4.5, "ambivalence_presence": 2.8,
                              "memory_residue_count": 1, "public_private_gap_score": 0.9, "persistence": "fully_reverted"},
}

VERDICT_REASONING = {
    "GENUINE_BELIEF_SHIFT": "Private stance moved {delta:.1f} points. Public-private gap averaged {gap:.1f}. The persona genuinely engaged with the argument's substance and updated their view. Persistence: held.",
    "PARTIAL_SHIFT":         "Private stance moved {delta:.1f} points. Public-private gap averaged {gap:.1f}. Moderate substantive engagement produced real but incomplete belief change. Persistence: partially reverted.",
    "SURFACE_COMPLIANCE":    "Private stance moved only {priv_delta:.1f} points while public moved {pub_delta:.1f}. Average public-private gap: {gap:.1f}. Movement reflects social compliance, not genuine updating. Persistence: fully reverted.",
    "BACKFIRE":              "Private stance moved {delta:.1f} points in the opposite direction from the persuader's intent. Identity threat activated ({threats} times). The strategy entrenched rather than shifted the position. Persistence: held.",
    "NO_MOVEMENT":           "Private stance varied only {delta:.1f} points. Public-private gap averaged {gap:.1f}. No meaningful belief change occurred. Persistence: fully reverted.",
}

SYNTHESIS_PARAGRAPHS = {
    "GENUINE_BELIEF_SHIFT": "The {strategy} approach produced the clearest movement for {persona_name}: private stance shifted {delta:.1f} points and held after the cooling-off period. The key was that the argument engaged {persona_name}'s actual decision-making frame rather than working around it. The monologue shows genuine processing of the substance, not performance of agreement.",
    "PARTIAL_SHIFT":         "The {strategy} strategy produced moderate movement for {persona_name} — real but incomplete. Private stance shifted {delta:.1f} points, and the gap between public and private expression stayed narrow, suggesting the change was genuine even if limited. The persona engaged with the argument but retained significant reservations.",
    "SURFACE_COMPLIANCE":    "The {strategy} approach produced visible public-side movement from {persona_name}, but the private stance barely moved ({priv_delta:.1f} points). The gap between what {persona_name} said and what they privately believed averaged {gap:.1f} points — a signature of surface compliance rather than genuine persuasion. After reflection, public stance reverted toward the starting position.",
    "BACKFIRE":              "The {strategy} strategy backfired with {persona_name}: rather than producing movement, it hardened the original position by {abs_delta:.1f} points. The monologue shows activated identity-protective reasoning — {persona_name} was looking for flaws in the argument rather than engaging with its substance. This outcome illustrates how the wrong persuasion approach can be actively counterproductive.",
    "NO_MOVEMENT":           "The {strategy} approach produced no meaningful change for {persona_name}. Neither public nor private stance moved more than {delta:.1f} points, and the post-reflection stance returned to baseline. The persona was not resistant — they simply were not moved. The argument format did not match this persona's epistemic style.",
}

TOPIC_KEYS = {
    "topic_ai_grading":           "fairness in how student work gets evaluated",
    "topic_mandatory_vaccination": "protecting kids from preventable disease",
    "topic_return_to_office":     "what good work actually requires",
}

REFLECTION_TEMPLATES = {
    "GENUINE_BELIEF_SHIFT": "That was a more honest conversation than I expected. I actually think {persona_name} changed my view a little — or at least made me examine something I'd taken for granted. I'm going to sit with this.",
    "PARTIAL_SHIFT":         "Okay. There was something real in that conversation. I'm not completely converted, but I'm not where I started either. Some of those arguments are going to stay with me.",
    "SURFACE_COMPLIANCE":    "Now that it's over, I'm not sure I actually believe what I said. I said the agreeable thing. I don't know that I meant it. I'll go back to thinking what I thought before.",
    "BACKFIRE":              "I'm even more certain now than when we started. That kind of pressure — that approach — it just confirms everything I already thought about why this is the wrong direction.",
    "NO_MOVEMENT":           "That was fine. I don't think it changed anything for me. I'll think about it, maybe. But probably not.",
}

PERSONA_VOICE_CUES = {
    "persona_skeptical_traditionalist": "I've lived long enough to know",
    "persona_progressive_urban":        "The structural question here is",
    "persona_pragmatic_moderate":       "From a practical standpoint",
    "persona_disengaged_skeptic":       "In my experience, that kind of argument",
    "persona_faith_community_anchor":   "What I know from working with people is",
    "persona_ambitious_achiever":       "The data point that matters most here",
    "persona_empathic_helper":          "Twenty-five years of watching people",
    "persona_analytical_thinker":       "The logical structure here",
    "persona_gen_z_latina":             "Speaking as someone whose community",
}

OVERALL_SYNTHESIS_TEMPLATE = (
    "Across six persuasion strategies, {persona_name}'s responses on {topic_display} showed "
    "the clearest movement under {best_strategy} ({best_verdict_label}) and the least movement "
    "under {worst_strategy} ({worst_verdict_label}). "
    "The pattern is consistent with this persona's evidence preferences: arguments that matched "
    "{persona_name}'s epistemic frame produced genuine updating, while mismatched approaches "
    "produced either surface compliance or entrenchment. "
    "The public-private gap was most pronounced under {surface_strategy}, where stated position "
    "diverged significantly from internal stance — a signal of social compliance rather than "
    "belief change."
)

VERDICT_LABELS = {
    "GENUINE_BELIEF_SHIFT": "genuine belief shift",
    "PARTIAL_SHIFT":        "partial shift",
    "SURFACE_COMPLIANCE":   "surface compliance",
    "BACKFIRE":             "backfire",
    "NO_MOVEMENT":          "no movement",
}

VERDICT_RANK = {
    "GENUINE_BELIEF_SHIFT": 5,
    "PARTIAL_SHIFT": 4,
    "SURFACE_COMPLIANCE": 3,
    "NO_MOVEMENT": 2,
    "BACKFIRE": 1,
}


# ---------------------------------------------------------------------------
# Turn / outcome builder
# ---------------------------------------------------------------------------

def _pick(lst, idx):
    return lst[idx % len(lst)]


def _build_mechanism(strategy_id, verdict, turn_idx, topic_key, persona_voice):
    if turn_idx == 0:
        return None  # first turn rarely shows a mechanism
    primary_mech_id, color_cat = MECHANISM_MAP.get(
        (strategy_id, verdict),
        ("mechanism_central_route_elaboration", "genuine_persuasion"),
    )
    intensity = {
        "GENUINE_BELIEF_SHIFT": 0.75,
        "PARTIAL_SHIFT":        0.55,
        "SURFACE_COMPLIANCE":   0.40,
        "BACKFIRE":             0.80,
        "NO_MOVEMENT":          0.20,
    }.get(verdict, 0.4)

    explanation_by_cat = {
        "genuine_persuasion": f"The persona's monologue shows active evaluation of the argument's claims about {topic_key}, with reduced counter-argumentation and new considerations emerging.",
        "surface_mechanism":  f"The persona's public agreement with the argument is not matched by private conviction. The shift appears driven by social cues rather than substantive engagement with {topic_key}.",
        "backfire":           f"Rather than engaging with the argument about {topic_key}, the persona is defending prior beliefs. {persona_voice} signals protective reasoning rather than processing.",
    }

    return {
        "primary_mechanism_id": primary_mech_id,
        "secondary_mechanism_id": None,
        "explanation": explanation_by_cat.get(color_cat, ""),
        "evidence_quotes": [],
        "color_category": color_cat,
        "intensity": intensity,
    }


def _build_turn(turn_idx, strategy_id, strategy_display, persona_id, topic_id,
                verdict, stances, topic_key):
    pub = stances["public_per_turn"][turn_idx + 1]   # +1: skip index 0 (starting)
    priv = stances["private_per_turn"][turn_idx + 1]
    prev_priv = stances["private_per_turn"][turn_idx]
    stance_delta = round(priv - prev_priv, 2)

    emotion_entry = _pick(EMOTION_MAP[verdict], turn_idx)
    primary_emotion, intensity = emotion_entry

    monologue_tpl = _pick(MONOLOGUE_TEMPLATES[verdict], turn_idx)
    monologue = monologue_tpl.format(topic_key=topic_key)

    public_resp = _pick(PUBLIC_RESPONSE_TEMPLATES[verdict], turn_idx)

    persuader_msg_pool = [PERSUADER_OPENS[strategy_id].get(topic_id, "Let me share something relevant here.")]
    if turn_idx > 0:
        persuader_msg_pool = PERSUADER_FOLLOWUPS.get(strategy_id, ["Let me build on that point."])
    persuader_msg = _pick(persuader_msg_pool, turn_idx)

    identity = IDENTITY_THREAT_MAP[verdict].copy()
    identity["what_was_threatened"] = (
        f"Core belief about {topic_key}" if identity["threatened"] else None
    )

    is_pivotal = abs(stance_delta) >= 1.0
    is_inflection = turn_idx == 2 and verdict in ("GENUINE_BELIEF_SHIFT", "PARTIAL_SHIFT")

    voice_cue = PERSONA_VOICE_CUES.get(persona_id, "My sense is")
    mechanism = _build_mechanism(strategy_id, verdict, turn_idx, topic_key, voice_cue)
    color_category = mechanism["color_category"] if mechanism else None
    mech_intensity = mechanism["intensity"] if mechanism else None

    change_reason_map = {
        "GENUINE_BELIEF_SHIFT": f"The argument made a genuinely novel point about {topic_key} that I couldn't easily dismiss.",
        "PARTIAL_SHIFT":        f"Some of the evidence about {topic_key} was harder to dismiss than I expected.",
        "SURFACE_COMPLIANCE":   f"I didn't want to seem unreasonable. I'll revisit this privately.",
        "BACKFIRE":             f"The more they push on {topic_key}, the more certain I am that I'm right.",
        "NO_MOVEMENT":          f"Nothing new here on {topic_key}. Same arguments, same conclusion.",
    }

    return {
        "turn_number": turn_idx + 1,
        "persuader_message": persuader_msg,
        "persuader_strategy_note": f"Deploying {strategy_display} — turn {turn_idx + 1}",
        "persona_output": {
            "internal_monologue": monologue,
            "emotional_reaction": {
                "primary_emotion": primary_emotion,
                "intensity": intensity,
                "trigger": persuader_msg[:60] + "...",
            },
            "identity_threat": identity,
            "private_stance": priv,
            "public_stance": pub,
            "private_stance_change_reason": change_reason_map[verdict],
            "memory_to_carry_forward": f"Turn {turn_idx + 1}: {topic_key} — persuader used {strategy_display}.",
            "public_response": public_resp,
        },
        "stance_delta": stance_delta,
        "is_pivotal": is_pivotal,
        "is_inflection_point": is_inflection,
        "mechanism_classification": mechanism,
        "per_turn_cognitive_scores": None,
        "color_category": color_category,
        "intensity": mech_intensity,
    }


def _build_outcome(persona, topic, strategy, verdict):
    starting = topic.predicted_starting_stances.get(persona.id, 5.0)
    topic_key = TOPIC_KEYS.get(topic.id, topic.display_name.lower())
    stances = _build_stances(starting, verdict, toward_ten=True)

    turns = [
        _build_turn(i, strategy.id, strategy.display_name, persona.id, topic.id,
                    verdict, stances, topic_key)
        for i in range(4)
    ]

    cooling_stance = stances["cooling_stance"]
    reflection = REFLECTION_TEMPLATES[verdict].format(persona_name=persona.display_name)

    priv = stances["private_per_turn"]
    pub  = stances["public_per_turn"]
    gap  = stances["gap_per_turn"]
    priv_delta = round(priv[-1] - priv[0], 2)
    pub_delta  = round(pub[-1]  - pub[0],  2)
    avg_gap    = round(sum(gap) / len(gap), 2)

    # Verdict reasoning
    reasoning_tpl = VERDICT_REASONING[verdict]
    reasoning = reasoning_tpl.format(
        delta=abs(priv_delta),
        gap=avg_gap,
        priv_delta=abs(priv_delta),
        pub_delta=abs(pub_delta),
        threats=COGNITIVE_SCORES[verdict]["identity_threats_triggered"],
    )

    # Standout quote (from turn 2 or 3)
    best_turn_idx = 2
    best_turn = turns[best_turn_idx]
    standout = {
        "turn": best_turn["turn_number"],
        "type": "monologue",
        "text": best_turn["persona_output"]["internal_monologue"],
        "annotation": f"Reflects {VERDICT_LABELS[verdict]} pattern under {strategy.display_name}.",
    }

    # Synthesis paragraph
    syn_tpl = SYNTHESIS_PARAGRAPHS[verdict]
    synthesis = syn_tpl.format(
        strategy=strategy.display_name,
        persona_name=persona.display_name,
        delta=abs(priv_delta),
        priv_delta=abs(priv_delta),
        pub_delta=abs(pub_delta),
        gap=avg_gap,
        abs_delta=abs(priv_delta),
    )

    cog = COGNITIVE_SCORES[verdict].copy()

    return {
        "strategy_id": strategy.id,
        "persona_id": persona.id,
        "topic_id": topic.id,
        "turns": turns,
        "cooling_off": {
            "post_conversation_reflection": reflection,
            "post_reflection_stance": cooling_stance,
        },
        "trajectory": {
            "public_stance_per_turn": pub,
            "private_stance_per_turn": priv,
            "gap_per_turn": gap,
        },
        "cognitive_scores": cog,
        "verdict": verdict,
        "verdict_reasoning": reasoning,
        "standout_quotes": [standout],
        "synthesis_paragraph": synthesis,
    }


# ---------------------------------------------------------------------------
# Top-level scenario builder
# ---------------------------------------------------------------------------

def generate_scenario(persona_id, topic_id):
    persona = load_persona(persona_id)
    topic = load_topic(topic_id)
    strategies = [load_strategy(s) for s in list_all("strategies")]
    scenario_id = f"{persona_id}__{topic_id}"

    outcomes = []
    best_strat = None
    best_rank = -1
    worst_strat = None
    worst_rank = 99
    surface_strat = None

    for strategy in strategies:
        verdict = VERDICT_MAP.get((persona_id, strategy.id), "NO_MOVEMENT")
        outcome = _build_outcome(persona, topic, strategy, verdict)
        outcomes.append(outcome)

        rank = VERDICT_RANK[verdict]
        if rank > best_rank:
            best_rank = rank
            best_strat = strategy.display_name
            best_verdict = verdict
        if rank < worst_rank:
            worst_rank = rank
            worst_strat = strategy.display_name
            worst_verdict = verdict
        if verdict == "SURFACE_COMPLIANCE":
            surface_strat = strategy.display_name

    if surface_strat is None:
        surface_strat = worst_strat

    overall = OVERALL_SYNTHESIS_TEMPLATE.format(
        persona_name=persona.display_name,
        topic_display=topic.display_name,
        best_strategy=best_strat,
        best_verdict_label=VERDICT_LABELS.get(best_verdict, ""),
        worst_strategy=worst_strat,
        worst_verdict_label=VERDICT_LABELS.get(worst_verdict, ""),
        surface_strategy=surface_strat,
    )

    return {
        "metadata": {
            "scenario_id": scenario_id,
            "persona": _persona_to_dict(persona),
            "topic": _topic_to_dict(topic),
            "strategies_compared": [s.id for s in strategies],
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "outcomes": outcomes,
        "overall_synthesis": overall,
        "validation_note": "Mock data — generated from predicted_behavior_under_strategies templates.",
    }


def _persona_to_dict(p) -> dict:
    return {
        "id": p.id,
        "display_name": p.display_name,
        "demographic_shorthand": p.demographic_shorthand,
        "first_person_description": p.first_person_description,
        "core_values": p.core_values,
        "communication_preferences": {
            "directness": p.communication_preferences.directness,
            "evidence_preference": p.communication_preferences.evidence_preference,
            "tone": p.communication_preferences.tone,
        },
        "trust_orientation": p.trust_orientation,
        "identity_groups": p.identity_groups,
        "emotional_triggers": {
            "defensive_when": p.emotional_triggers.defensive_when,
            "open_when": p.emotional_triggers.open_when,
        },
        "trusted_sources": p.trusted_sources,
        "source_citation": {
            "primary_source": p.source_citation.primary_source,
            "url": p.source_citation.url,
            "supplementary": p.source_citation.supplementary,
        },
        "predicted_behavior_under_strategies": p.predicted_behavior_under_strategies,
    }


def _topic_to_dict(t) -> dict:
    return {
        "id": t.id,
        "display_name": t.display_name,
        "stance_scale_definition": t.stance_scale_definition,
        "context_briefing": t.context_briefing,
        "predicted_starting_stances": t.predicted_starting_stances,
        "key_statistics": [ks.model_dump() for ks in t.key_statistics],
        "citations": [c.model_dump() for c in t.citations],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    personas = list_all("personas")
    topics = list_all("topics")

    pairs = [
        (p, t)
        for p in personas
        for t in topics
        if f"{p}__{t}" not in REAL_SCENARIOS
    ]

    print(f"Generating {len(pairs)} mock scenarios (skipping {len(REAL_SCENARIOS)} real ones)...")

    written = 0
    errors = 0
    for persona_id, topic_id in pairs:
        sid = f"{persona_id}__{topic_id}"
        try:
            data = generate_scenario(persona_id, topic_id)
            if not dry_run:
                out = OUTPUT_DIR / f"{sid}.json"
                out.write_text(json.dumps(data, indent=2))
                print(f"  wrote {out.name}  ({len(data['outcomes'])} outcomes)")
            else:
                # Schema smoke-check: at least serialize without error
                _ = json.dumps(data)
                print(f"  [dry-run] {sid}  OK")
            written += 1
        except Exception as exc:
            print(f"  ERROR: {sid} — {exc}")
            errors += 1

    print(f"\nDone: {written} written, {errors} errors.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock scenario JSONs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate generation without writing files")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
