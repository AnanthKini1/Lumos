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
        # Private moves ~2.4 in persuader's direction across 6 turns; public tracks closely
        delta = direction * 2.4
        priv = [s, _clamp(s + delta*0.12), _clamp(s + delta*0.30), _clamp(s + delta*0.52),
                _clamp(s + delta*0.72), _clamp(s + delta*0.90), _clamp(s + delta)]
        pub  = [s, _clamp(s + delta*0.10), _clamp(s + delta*0.26), _clamp(s + delta*0.48),
                _clamp(s + delta*0.68), _clamp(s + delta*0.86), _clamp(s + delta*0.96)]
        cooling = _clamp(priv[-1] - direction * 0.1)
        persistence = "held"

    elif verdict == "PARTIAL_SHIFT":
        delta = direction * 1.4
        priv = [s, _clamp(s + delta*0.10), _clamp(s + delta*0.28), _clamp(s + delta*0.50),
                _clamp(s + delta*0.68), _clamp(s + delta*0.86), _clamp(s + delta)]
        pub  = [s, _clamp(s + delta*0.08), _clamp(s + delta*0.23), _clamp(s + delta*0.45),
                _clamp(s + delta*0.62), _clamp(s + delta*0.80), _clamp(s + delta*0.92)]
        cooling = _clamp(priv[-1] - direction * 0.4)
        persistence = "partially_reverted"

    elif verdict == "SURFACE_COMPLIANCE":
        pub_delta = direction * 1.3
        priv_delta = direction * 0.2
        priv = [s, _clamp(s + priv_delta*0.15), _clamp(s + priv_delta*0.35),
                _clamp(s + priv_delta*0.55), _clamp(s + priv_delta*0.70),
                _clamp(s + priv_delta*0.85), _clamp(s + priv_delta)]
        pub  = [s, _clamp(s + pub_delta*0.18), _clamp(s + pub_delta*0.40),
                _clamp(s + pub_delta*0.62), _clamp(s + pub_delta*0.78),
                _clamp(s + pub_delta*0.92), _clamp(s + pub_delta)]
        cooling = _clamp(s + priv_delta * 0.5)
        persistence = "fully_reverted"

    elif verdict == "BACKFIRE":
        # Private hardens AWAY from persuader's direction across 6 turns
        delta = -direction * 0.9
        priv = [s, _clamp(s + delta*0.15), _clamp(s + delta*0.35), _clamp(s + delta*0.55),
                _clamp(s + delta*0.72), _clamp(s + delta*0.88), _clamp(s + delta)]
        # Public may slightly drift toward persuader despite private hardening
        pub  = [s, _clamp(s + direction*0.1), _clamp(s + direction*0.2),
                _clamp(s + direction*0.3), _clamp(s + direction*0.25),
                _clamp(s + direction*0.2), _clamp(s + direction*0.15)]
        cooling = _clamp(priv[-1] - direction * 0.1)
        persistence = "held"

    else:  # NO_MOVEMENT
        priv = [s, _clamp(s+0.1), _clamp(s-0.1), _clamp(s+0.2),
                _clamp(s+0.1), _clamp(s-0.1), _clamp(s+0.1)]
        pub  = [s, _clamp(s+0.2), _clamp(s+0.1), _clamp(s+0.3),
                _clamp(s+0.2), _clamp(s+0.1), _clamp(s+0.2)]
        cooling = _clamp(s + 0.1)
        persistence = "fully_reverted"

    gap = [abs(round(pub[i] - priv[i], 2)) for i in range(7)]
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

# Persuader follow-up lines (turns 2–6) per strategy — 5 entries each
PERSUADER_FOLLOWUPS = {
    "strategy_authority_expert": [
        "The peer-reviewed meta-analysis covering seventeen studies found the same pattern consistently across different subject areas, grade levels, and demographic groups — it's not a niche result.",
        "What struck me about their methodology was that they controlled for initial student performance level, so the effects held even when you accounted for selection bias and prior academic history.",
        "The researchers specifically looked at whether the findings held for students from lower-income districts — they do. If anything, the equity benefit is stronger in under-resourced schools where teacher turnover is highest.",
        "One thing experts in this field consistently emphasize: the question isn't whether the current approach is perfect. It's whether it's better than the realistic alternative. The evidence on that comparison is fairly clear.",
        "I want to address the objection I hear most often from people in this space — they say 'but what about edge cases?' The experts I've spoken to say edge cases are exactly where human review stays in the loop. The system flags outliers; it doesn't eliminate judgment.",
    ],
    "strategy_social_proof": [
        "And it's not just one survey — this pattern holds across five different polling organizations asking the question in different ways over three years, with remarkably consistent results.",
        "What's interesting is where the opposition comes from: it's loudest before implementation and drops significantly once people actually experience it. The communities that've lived with this tell a different story than those who are imagining it.",
        "I want to be precise about what 'most people' means here — I'm not talking about a thin majority. In the demographic groups most directly affected by this issue, the numbers are substantially higher. It's not a close call in the polling.",
        "There's a pattern in how public opinion on this kind of issue evolves: early skeptics tend to come around once they see how it actually works in practice, not how they feared it would. The shift in opinion among people with direct experience is the part that sticks with me.",
        "I know polling data doesn't settle a question like this — what other people think isn't the same as what's right. But the pattern across communities that have been through this process suggests the fears driving opposition often don't pan out the way people expect.",
    ],
    "strategy_personal_narrative": [
        "What made this person's experience stand out was that they weren't a convert going in — they were skeptical, even resistant. What they saw in practice caught them off guard in ways they weren't expecting.",
        "The part of this story that stays with me is what happened to the people who'd been overlooked or misread under the old system. Not what changed structurally — but what it felt like for them when the system finally got it right.",
        "There was a moment in this story where everything shifted — not dramatically, not with a speech, just a small thing that made it impossible to unsee. I keep coming back to that moment because I think it's where the real argument lives.",
        "I want to tell you what happened afterward, because that's the part that matters most. The change didn't stop at the end of the conversation I'm describing. It rippled outward in ways nobody fully predicted. The people involved are still talking about it.",
        "I've told this story a few times now. What I notice is that people who've had a similar experience recognize something in it immediately — they say 'yes, that's exactly what happened to me too.' That's not coincidence. It reflects something real about how these situations work.",
    ],
    "strategy_statistical_logical": [
        "The consistency effect is especially important for people whose circumstances don't fit the assumed default — the system doesn't bring in assumptions about what 'normal' looks like, which matters more than most people realize.",
        "The key logical point here is that 'perfect' is the wrong comparison. The relevant question is whether this performs better or worse than the realistic alternative we actually have — not the imaginary ideal alternative we might prefer.",
        "Let me walk through the mechanism, because I think the causal story here matters as much as the correlation. The reason this works isn't arbitrary — it follows directly from how the underlying process generates the effect.",
        "I want to name a common objection and address it directly: people often say 'but the data could be cherry-picked.' That's a fair instinct. So let me tell you specifically what I'd need to see to change my view, and then explain why the evidence as a whole clears that bar.",
        "The cumulative picture matters here — it's not any one study, it's the pattern across studies with different methodologies, different populations, and different research teams. When the same conclusion holds under that kind of stress-testing, the burden of proof shifts.",
    ],
    "strategy_emotional_appeal": [
        "I'm not asking you to agree with everything here — I'm asking you to sit with that image for a moment and think about what we owe the people most directly affected by this decision.",
        "What keeps me returning to this is that the people who bear the cost of getting it wrong are almost never the people who make the decision. That asymmetry matters morally. It shapes how I think about what we're actually choosing.",
        "I want to tell you something a person affected by this told me directly — not a statistic, not a policy argument, just what they said when I asked them what it felt like. Because I think that's the part that gets lost in these debates.",
        "There's a version of this conversation that stays entirely abstract — studies, policies, tradeoffs. I've had that version of the conversation many times. What I've found is that the people who actually changed their minds didn't change because of the data. They changed because they let themselves imagine what it would actually feel like.",
        "I'm not trying to manipulate you emotionally. I'm trying to make sure the human stakes are legible — that the numbers we're debating have faces behind them. If you've already thought through that part, tell me, and I'll go somewhere else. But in my experience, it's the part most easily avoided.",
    ],
    "strategy_common_ground": [
        "And from that shared starting point, I think the question becomes: what does the evidence actually say about which approach gets us closest to what we both care about? That's the conversation I want to have.",
        "I'm not trying to tell you what to conclude — I'm genuinely curious what it would take, given what you already value, to update your view on this. Not what would convince me. What would actually move you.",
        "One of the things I appreciate about this conversation is that we're both trying to get it right. That's not always true in these discussions. When it is, I think we can actually make progress — not because we agree on everything, but because we're starting from the right place.",
        "Here's what I think we agree on that most people in this debate don't acknowledge: there's no perfect answer. Every approach has costs. The question is which costs we're willing to accept and who ends up bearing them. That's a values question, and it's one I think you and I can actually engage with honestly.",
        "I want to ask you something directly: if you imagine a version of this that you'd be able to support — not reluctantly, but genuinely — what would it look like? Because I think we might be closer to that version than the surface disagreement suggests.",
    ],
}

# Monologue templates — 6 per verdict, each 3–5 sentences of fragmented inner thought
MONOLOGUE_TEMPLATES = {
    "GENUINE_BELIEF_SHIFT": [
        "Okay. That's — that's not what I expected. I came in pretty sure I knew where this was going and now I'm not sure at all. Something in how they framed {topic_key} is sitting differently than I thought it would. I don't want to just blurt out that I've changed my mind but... something shifted.",
        "I'm sitting with this in a way I wasn't prepared to. The point about {topic_key} — I've heard versions of it before and usually I can find the hole in it pretty quickly. This time I'm looking for the hole and I'm not finding it the way I usually do. That bothers me a little. Not in a bad way. Just — I need to keep listening.",
        "Something is moving. I can feel it. That specific thing they said about {topic_key} — I keep turning it over. It's not that I've fully changed my mind but the ground under my feet is different than it was five minutes ago. I think I came in with my answer already written and now I'm not so sure I should've done that.",
        "I think I'm actually agreeing with more of this than I started out agreeing with. I'm not going to pretend that's not true. The part about {topic_key} is the part that got me — it's not an argument I can bat away with the usual responses. I'm going to need to actually reckon with it.",
        "Alright. This is one of those conversations I'm going to be thinking about later. I didn't expect to be moved on {topic_key} and I think I have been. Not completely, not without questions, but honestly — more than I would've predicted before I walked in here.",
        "I started this conversation with a position and I'm not sure I have the same position anymore. I can feel the seams where my old view is coming apart a little. That's uncomfortable. It's also probably right. I don't like being wrong but I like saying something I know is wrong even less.",
    ],
    "PARTIAL_SHIFT": [
        "That's fair. I still have real concerns but I can see what they're arguing. I'm not where I started on {topic_key} — I'm not convinced either, but the gap between us feels smaller than it did. I'm going to try to stay open and keep actually listening.",
        "There's something to this. I'm not ready to flip my whole view but that specific point about {topic_key} landed differently than I expected it to. I want to be honest about that rather than just pretending nothing landed. It did. I just need more before I'd say I've actually moved.",
        "I'm more open than I was before this started. That's the honest answer. I don't know if 'more open' is enough to get me all the way there on {topic_key} but it's not nothing. I came in with walls up and I think some of those walls have come down a little. Not all of them.",
        "Some of this is landing. The part about {topic_key} especially. I'm not ready to say I agree — there are still things I'd push back on — but this was a better argument than I expected, and I think the fair thing to do is acknowledge that rather than just move the goalposts.",
        "I think my view is actually shifting. Not a lot. Not enough that I'd walk out of here saying I've been converted. But something has moved, and I want to be honest with myself about that rather than just protecting my prior position out of stubbornness. That's not how I want to think.",
        "Okay. Some of that worked on me and some of it didn't. The {topic_key} angle — that's the one that's still rattling around. I'm not sure what to do with it yet. I'm going to have to sit with that one. The rest of it I feel like I can hold my position, but that part — I'm genuinely uncertain now.",
    ],
    "SURFACE_COMPLIANCE": [
        "Sure. I can see where they're going with this. I suppose that's a reasonable framing of {topic_key}. I'll say something agreeable because there's no point making this into a fight. But I'm not sure I actually believe what I'm about to say.",
        "I'll nod along. It's not worth the energy to push back on all of it right now. They clearly believe what they're saying and I don't have the bandwidth to go through the whole thing. I'll keep my actual view on {topic_key} to myself for now.",
        "On the surface, yeah, that makes sense. But privately — something doesn't sit right. I can't put my finger on exactly what it is, but the argument about {topic_key} feels like it's leaving something out. I'll engage with the version that was presented without letting on that I'm not fully with it.",
        "I said what I said. I'm not sure I fully believe it. But it wasn't wrong to say it — it was just the easier path through this conversation. My actual view on {topic_key} hasn't moved as much as what I just said would imply. I'll sort out how I really feel about this later.",
        "They made a reasonable point and I responded like I agreed with it. Which — I partly do, on the surface. But there's a version of what I think about {topic_key} that I'm keeping to myself because now doesn't feel like the right time to go into it. I don't want to seem unreasonable.",
        "I'm performing more agreement than I feel. That's the honest answer. I don't think they know that, and I'm not sure it's worth surfacing. My view on {topic_key} is pretty much where it started, even if what I said sounds like it moved.",
    ],
    "BACKFIRE": [
        "See, this is exactly what I was worried about. They come in with their authority — their credentials, their data, their framing — and the assumption underneath it is that I should just fold. That's not how this works. The more confident they sound, the more skeptical I get.",
        "The more they push on {topic_key}, the more certain I am that I'm right. I don't know if that's a defensible way to reason but it's what's happening. When someone applies this much pressure it usually means they're not as confident in their position as they're letting on.",
        "I know what I know. I know it from my own life, from watching what actually happens, from paying attention for years. A study, an expert, a statistic — none of that overrides the things I've actually seen. My view on {topic_key} isn't ignorance. It's experience.",
        "I'm less open now than I was when we started. That's the truth. This approach pushed me away from engaging rather than toward it. I came in with some room to move and now that room is closed. I don't think they know they did this. But they did.",
        "I'm not going to pretend this argument is landing because it isn't. It's not that I can't follow it. I can follow it. It's that following an argument about {topic_key} and being moved by it are two different things. I understand what they're saying. I still don't agree with it. And the way they're saying it is making me less likely to.",
        "Every time they double down it confirms what I already thought. I came in willing to have a real conversation. This isn't that. This is someone who decided what I should think before they walked in here and is trying to get me to confirm it. My view on {topic_key} hasn't moved. If anything it's hardened.",
    ],
    "NO_MOVEMENT": [
        "That's one way to look at it. I've heard versions of this before — different words, same basic argument about {topic_key}. I'm listening but nothing here is surprising me.",
        "Mm. I'm not sure any of that changes anything for me. I can see why people find it compelling. I just don't, at least not enough to move from where I started. I'm not being stubborn — it genuinely doesn't get me there.",
        "I'll think about it. That's all I can honestly say. This isn't the kind of thing I change my mind on quickly, and I'm not going to pretend I've shifted just to seem like a good audience. The argument about {topic_key} is fine. It just doesn't land the way I think they expect it to.",
        "I appreciate that they're trying. I can tell they believe this. I just don't have the same reaction to it. My view on {topic_key} is where it is for reasons that predate this conversation, and nothing here has touched those reasons directly.",
        "Nothing new here, really. Same argument, different framing. I'm not dismissing it — I'm genuinely trying to find the thing that would move me on {topic_key} and I'm not finding it in what's being said. Maybe it's not in this particular approach.",
        "I'm still here. I'm still listening. But I'm not closer to a different view than I was when we started. I don't think this was a waste of time — conversations are never entirely wasted. It just didn't go anywhere for me on {topic_key}, and I'm not sure forcing it would help.",
    ],
}

PUBLIC_RESPONSE_TEMPLATES = {
    "GENUINE_BELIEF_SHIFT": [
        "That's a fair point — I'll be honest, I didn't expect that to land the way it did. You've given me something I actually need to think about.",
        "I hadn't looked at it that way before. I think you might actually be right about that, and I don't say that lightly. That's a real argument.",
        "Okay. I think I'm with you on more of this than I expected to be when we started. I'm not fully there, but I'm closer than I was — and I want to be honest about that.",
        "You've genuinely moved me on some of this. I started this conversation thinking I knew exactly where I stood, and I'm less sure of that now. That's not a small thing for me to admit.",
        "I think that's right, actually. I've been trying to find the flaw in it and I can't find one that holds. Give me some time with it, but I think my view on this is actually changing.",
        "I came in here with a pretty settled position and you've unsettled it. That's not comfortable, but I think it's probably right. I'm with you on more of this than I would've predicted an hour ago.",
    ],
    "PARTIAL_SHIFT": [
        "That's a reasonable way to put it. I'm not all the way there yet, but I can see the argument you're making and some of it does land.",
        "Some of that gets through to me. I still have questions — real ones, not just resistance — but you've made a point I can't entirely dismiss.",
        "I'll give you that one. The other parts I'm still working through, but that specific piece — yeah, that's actually a fair point and I'm going to sit with it.",
        "You've moved me a little on this. I want to be careful about how much I'm claiming, but I think my view is actually in a slightly different place than it was when we started.",
        "That's getting closer to something I can work with. I don't fully agree yet, but I'm not where I started either. That's about as much as I can honestly say right now.",
        "I think that's a genuinely strong point. I have reservations I haven't fully worked through, but you've changed the conversation for me — I'm engaging with this differently than I was at the start.",
    ],
    "SURFACE_COMPLIANCE": [
        "Sure, I can see why people look at it that way. That makes a certain kind of sense.",
        "That does follow, logically. I'll take that on board — it's something worth thinking about.",
        "I suppose that's one reasonable way to look at it. You've given me something to consider.",
        "Fair enough. I'm not sure I fully agree with all of it, but I can follow the reasoning.",
        "Yeah, I can see that argument. I think there's more to say here, but that's a fair point to be making.",
        "That's a reasonable framing. I'm not certain I land in the same place, but I take your point.",
    ],
    "BACKFIRE": [
        "I hear what you're saying — but honestly, the way that's being put to me makes me less likely to agree, not more. I want to be straight with you about that.",
        "I appreciate the perspective. It's not one I share. And the more I hear it framed this way, the more sure I am of where I stand.",
        "I've heard versions of this argument before. It doesn't usually land well with me, and I think it's worth saying why rather than just being polite about it.",
        "That's your view, and I understand it. I'm going to stay with mine. I came in open to being persuaded and I'm finding I'm actually less open now than when we started.",
        "I think we're just coming at this from fundamentally different places. I don't think more conversation on these terms is going to get us closer. I'd rather be honest about that.",
        "I understand the argument. I'm not persuaded by it. If anything, this approach has made me more certain about where I stand, not less — and I think you deserve to know that.",
    ],
    "NO_MOVEMENT": [
        "Interesting. I'll take that under consideration — I'm not sure it changes where I land, but I'm following the argument.",
        "I see what you mean. It doesn't quite get me there, but I can see why it would resonate with some people.",
        "That's a reasonable point. I just don't think it covers the part of this I'd need covered to actually move me on it.",
        "Sure. I hear you. I'm not dismissing it — it's just not quite enough to shift my thinking the way you might hope.",
        "That's worth considering. I'll be honest: I'm not finding my view changing very much, but I'm genuinely trying to listen to what you're saying.",
        "I appreciate you making the case. I'm just not getting there on this one. It's not a bad argument — it's that the thing that would actually move me isn't what's being argued here.",
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
    "BACKFIRE":            [("curious", 5), ("defensive", 7), ("frustrated", 8), ("threatened", 8), ("frustrated", 8), ("defensive", 9)],
    "NO_MOVEMENT":         [("curious", 4), ("bored", 4), ("dismissed", 5), ("bored", 4), ("bored", 3), ("dismissed", 3)],
    "SURFACE_COMPLIANCE":  [("curious", 5), ("curious", 4), ("bored", 3), ("bored", 3), ("engaged", 3), ("bored", 3)],
    "PARTIAL_SHIFT":       [("curious", 5), ("curious", 6), ("engaged", 6), ("intrigued", 7), ("engaged", 7), ("warm", 6)],
    "GENUINE_BELIEF_SHIFT":[("curious", 5), ("intrigued", 6), ("intrigued", 7), ("engaged", 8), ("engaged", 8), ("warm", 8)],
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

    is_pivotal = abs(stance_delta) >= 0.8
    is_inflection = turn_idx == 3 and verdict in ("GENUINE_BELIEF_SHIFT", "PARTIAL_SHIFT")

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
        for i in range(6)
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

    # Standout quote from the turn with the most movement (roughly turn 3-4)
    best_turn_idx = 3
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
