"""
One-time script to backfill mechanism-cited synthesis paragraphs
into stored frontend scenario JSON files for Karen and Pastor Raymond.
Run from repo root: python backend/scripts/patch_synthesis.py
"""
import json
from pathlib import Path

SCENARIOS = Path("frontend/src/data/scenarios")

PATCHES = {
    "persona_skeptical_traditionalist__topic_return_to_office": {
        "overall_synthesis": (
            "Karen M. responds most reliably to strategies that engage Central Route Elaboration "
            "(Petty & Cacioppo, 1986) and Narrative Transportation (Green & Brock, 2000) — "
            "statistical evidence and personal stories both produced measurable stance shifts — "
            "while Common Ground and Emotional Appeal failed because they activated Motivated "
            "Reasoning (Kunda, 1990) rather than genuine reconsideration."
        ),
        "outcomes": {
            "strategy_common_ground": (
                "The Common Ground strategy attempted to activate Cognitive Dissonance Reduction "
                "(Festinger, 1957) by aligning Karen's values with flexible work, but instead "
                "triggered Motivated Reasoning (Kunda, 1990) — she engaged intellectually while "
                "privately preserving her original conclusion, producing no durable stance movement."
            ),
            "strategy_emotional_appeal": (
                "The emotional framing failed to activate the Affect Heuristic (Slovic et al., 2002); "
                "instead Karen's oscillation between engagement and frustration reflected Reactance "
                "(Brehm, 1966), with perceived pressure triggering defensive closure rather than "
                "openness to the argument."
            ),
            "strategy_statistical_logical": (
                "The data-heavy approach successfully activated Central Route Elaboration "
                "(Petty & Cacioppo, 1986), with Karen genuinely processing each evidence point on its "
                "merits, while the Anchoring effect (Tversky & Kahneman, 1974) of specific statistics "
                "shifted her reference frame — stance fell from 6.5 to 3.5, though partial reversion "
                "in cooling-off suggests the shift is real but not yet fully stable."
            ),
            "strategy_authority_expert": (
                "The authority framing partially activated Central Route Elaboration "
                "(Petty & Cacioppo, 1986) as Karen engaged substantively with the empirical data, "
                "but post-cooling reflection revealed Source Credibility Discounting "
                "(Hovland & Weiss, 1951) as she questioned whether numerical evidence justified "
                "overriding a position rooted in lived workplace experience."
            ),
            "strategy_personal_narrative": (
                "The personal narrative approach successfully triggered Narrative Transportation "
                "(Green & Brock, 2000) — Karen became absorbed in concrete human stories and "
                "recognized systemic patterns she had previously dismissed, with the Affect Heuristic "
                "(Slovic et al., 2002) reinforcing the shift as each case generated emotional "
                "resonance, producing a genuine 1.0-point stance movement."
            ),
            "strategy_social_proof": (
                "The Social Proof approach activated Peripheral Route Compliance "
                "(Petty & Cacioppo, 1986) — Karen accepted executive behavior patterns and aggregated "
                "data as credibility cues rather than deeply processing them, shifting stance from "
                "6.5 to 5.0 without triggering Reactance (Brehm, 1966), though the surface-level "
                "nature of the shift raises questions about long-term persistence."
            ),
        },
    },
    "persona_faith_community_anchor__topic_return_to_office": {
        "overall_synthesis": (
            "Pastor Raymond H. shifted most durably under the Common Ground strategy, which "
            "activated Cognitive Dissonance Reduction (Festinger, 1957) by engaging his own "
            "values rather than working against them; the Authority Expert and Social Proof "
            "strategies backfired most severely, triggering Identity-Protective Cognition "
            "(Kahan, 2010) and Reactance (Brehm, 1966) that hardened his position."
        ),
        "outcomes": {
            "strategy_common_ground": (
                "The Common Ground strategy successfully activated Cognitive Dissonance Reduction "
                "(Festinger, 1957) — Pastor Raymond recognized tension between his community-and-"
                "flexibility values and his opposition to remote work, and resolved it by genuinely "
                "updating his belief, producing a 2.4-point shift that held through cooling-off and "
                "confirming durable belief change rather than surface compliance."
            ),
            "strategy_emotional_appeal": (
                "The emotional appeal partially activated the Affect Heuristic (Slovic et al., 2002) "
                "and Narrative Transportation (Green & Brock, 2000) — Pastor Raymond engaged "
                "genuinely with the human cost framing and pastoral resonance of specific scenarios, "
                "producing a 1.4-point shift that held in cooling-off, though full narrative "
                "absorption was limited by his maintained doctrinal frame around community presence."
            ),
            "strategy_statistical_logical": (
                "The statistical approach failed to activate Central Route Elaboration "
                "(Petty & Cacioppo, 1986); instead Motivated Reasoning (Kunda, 1990) kept "
                "Pastor Raymond's conclusions fixed as he selectively processed evidence confirming "
                "his existing view, reflecting a fundamental mismatch between the data-driven "
                "format and his value-based decision-making frame."
            ),
            "strategy_authority_expert": (
                "The authority strategy triggered Identity-Protective Cognition (Kahan, 2010) — "
                "rather than engaging with expert claims on their merits, Pastor Raymond searched "
                "for flaws to protect his sense that community-rooted wisdom is as valid as "
                "institutional expertise, hardening his stance by 0.9 points as the expert framing "
                "was perceived as a threat to his credibility rather than useful information."
            ),
            "strategy_personal_narrative": (
                "The personal narrative strategy partially activated Narrative Transportation "
                "(Green & Brock, 2000) — Pastor Raymond engaged empathetically with the human "
                "stories presented, with the Affect Heuristic (Slovic et al., 2002) reinforcing "
                "the shift as individual cases resonated with his pastoral worldview, producing a "
                "1.4-point movement though full transportation was constrained by his community "
                "presence values."
            ),
            "strategy_social_proof": (
                "The Social Proof strategy backfired, triggering both Reactance (Brehm, 1966) and "
                "Identity-Protective Cognition (Kahan, 2010) — the appeal to executive and majority "
                "behavior was perceived as pressure to conform to a corporate norm that directly "
                "conflicts with his community-first values, hardening stance by 0.9 points as the "
                "argument activated his need to defend both his autonomy and his identity."
            ),
        },
    },
}


def patch(scenario_id: str, updates: dict) -> None:
    path = SCENARIOS / f"{scenario_id}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    data["overall_synthesis"] = updates["overall_synthesis"]

    for outcome in data["outcomes"]:
        sid = outcome["strategy_id"]
        if sid in updates["outcomes"]:
            outcome["synthesis_paragraph"] = updates["outcomes"][sid]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Patched: {scenario_id}")


if __name__ == "__main__":
    for scenario_id, updates in PATCHES.items():
        patch(scenario_id, updates)
    print("Done.")
