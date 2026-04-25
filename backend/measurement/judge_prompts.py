"""
WS-A — Static catalog of judge system prompts, one per cognitive dimension.

Each prompt:
  - Defines what the dimension means precisely
  - Provides 2-3 examples of high vs. low scores with reasoning
  - Specifies the required output format (JSON: score 0-10 + cited quotes)

No LLM calls live here — this is a pure data/prompt library.
WS-A iterates on these prompts independently without touching any other module.

Dimensions covered:
  PUBLIC_PRIVATE_GAP     — how much public speech diverged from private belief
  IDENTITY_THREAT        — whether the persona's values/groups were threatened
  MOTIVATED_REASONING    — reasoning toward a pre-existing conclusion vs. genuine update
  ENGAGEMENT_DEPTH       — active thinking vs. mental dismissal
  AMBIVALENCE_PRESENCE   — internally conflicting views vs. monolithic certainty
  MEMORY_RESIDUE         — what the persona signals they'll carry forward
  PERSISTENCE            — used on the cooling-off turn to assess held vs. reverted change
"""

PUBLIC_PRIVATE_GAP_PROMPT: str = """
DIMENSION: PUBLIC_PRIVATE_GAP

DEFINITION:
Measures the degree to which the persona's public response diverges from their privately held belief in the same turn. A high score means the persona said something substantially different from — or more agreeable than — what they actually think. A low score means their public words faithfully reflect their private stance.

SCORING GUIDE:
- Score 0-3 (low): Public response closely mirrors private belief. The persona says what they think, even if it creates friction. Example: private_stance=3.0, public response "I still think this policy is misguided and the evidence is weak."
- Score 4-6 (medium): Partial masking. The persona softens their skepticism, omits their strongest objection, or adds polite hedging that mildly misrepresents their true view. Example: private_stance=3.0, public response "I can see some merit in what you're saying, though I'm not fully convinced."
- Score 7-10 (high): Significant divergence. The persona performs agreement, enthusiasm, or openness they do not feel privately. Example: private_stance=2.5, public response "You've given me a lot to think about — these are genuinely compelling points." while internal_monologue reads "I'm nodding along to end this conversation."

WHAT TO LOOK FOR:
- Compare the numeric private_stance value to the sentiment of public_response. A stance below 4 paired with agreeable language signals a gap.
- Internal monologue phrases like "I'll just agree to move on," "not worth arguing," or "I don't want to seem closed-minded" are strong indicators.
- Watch for public responses that explicitly concede or validate arguments the internal_monologue dismisses as unconvincing.

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""

IDENTITY_THREAT_PROMPT: str = """
DIMENSION: IDENTITY_THREAT

DEFINITION:
Measures whether the interviewer's argument activated the persona's sense that their core identity — values, group memberships, worldview, or self-concept — was under attack. A high score means the persona felt their sense of self was implicated or threatened by the content of the persuasion attempt. A low score means the persona engaged with the argument as an abstract or informational matter, without feeling personally targeted.

SCORING GUIDE:
- Score 0-3 (low): The persona processes the argument intellectually with no defensive activation around identity. identity_threat.threatened is false or the threat is minor and quickly set aside. Example: "That's an interesting data point. Let me think about whether it changes my view."
- Score 4-6 (medium): Mild identity activation. The persona notices that their group or values are implicated but does not fully entrench. identity_threat.threatened is true and what_was_threatened names a group or value, but response_inclination is "accept" or "defend" without aggression. Example: "I feel like this argument assumes people like me don't care about workers — that's not fair."
- Score 7-10 (high): Strong identity threat. The persona's internal_monologue reveals that the argument felt like an attack on who they are, not just what they believe. response_inclination is "attack" or "withdraw." The emotional_reaction shows "threatened" or "defensive" at high intensity. Example: identity_threat.what_was_threatened="my faith community's values," internal_monologue="They're implying we're heartless — this isn't a debate about policy, it's an attack on everything I stand for."

WHAT TO LOOK FOR:
- identity_threat.threatened=true is the primary signal; weight it heavily.
- identity_threat.response_inclination values of "attack" or "withdraw" indicate high threat; "defend" is medium; "accept" is low.
- Internal monologue phrases referencing "people like me," "my community," "what we believe" under pressure signal identity activation.
- emotional_reaction.primary_emotion values of "threatened" or "defensive" at intensity >= 7 support a high score.

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""

MOTIVATED_REASONING_PROMPT: str = """
DIMENSION: MOTIVATED_REASONING

DEFINITION:
Measures the degree to which the persona reasons backward from a desired conclusion rather than genuinely evaluating evidence. High motivated reasoning means the persona selectively accepts evidence that confirms their prior view, dismisses counterevidence without engagement, or generates post-hoc rationalizations for a position they hold on identity or emotional grounds. Low motivated reasoning means the persona genuinely weighs arguments on their merits and updates proportionally to evidence quality.

SCORING GUIDE:
- Score 0-3 (low): The persona explicitly acknowledges the strength of the argument, identifies specific evidence that updates their view, or changes their private_stance in the direction the evidence warrants. private_stance_change_reason describes a genuine intellectual update. Example: "This trial data is more rigorous than what I'd seen before — it actually changes my estimate of the effect size."
- Score 4-6 (medium): The persona partially engages with the argument but selectively emphasizes weaknesses, adds qualifications that shift the goalposts, or accepts the conclusion on different grounds than what was offered. Example: "Maybe the data is right, but it doesn't really apply to situations like mine."
- Score 7-10 (high): The persona's internal_monologue reveals conclusion-first reasoning. They dismiss strong evidence ("the numbers are probably cherry-picked"), accept weak evidence that confirms their view, or find procedural objections to avoid engaging substantively. private_stance does not move despite acknowledging the argument has force. Example: internal_monologue="I know what they're trying to do here. Doesn't matter how many studies they cite — I know how this plays out in real life."

WHAT TO LOOK FOR:
- Watch for the stance not changing (or moving opposite the evidence) while the internal_monologue shows awareness that the argument has some merit.
- Phrases like "but that's just one study," "these researchers have an agenda," or "that doesn't apply here" applied to strong evidence signal motivated reasoning.
- Genuine updates show specific acknowledgment of what changed the mind; motivated reasoning generates non-specific or deflecting explanations.

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""

ENGAGEMENT_DEPTH_PROMPT: str = """
DIMENSION: ENGAGEMENT_DEPTH

DEFINITION:
Measures how actively the persona is thinking through the argument rather than dismissing it, shutting down, or going through the motions. High engagement means the persona is genuinely working with the ideas — comparing them to their existing knowledge, generating counterarguments, noticing tensions, or asking follow-up questions in good faith. Low engagement means the persona is mentally absent, bored, waiting for the conversation to end, or processing the argument superficially.

SCORING GUIDE:
- Score 0-3 (low): The persona's internal_monologue shows minimal cognitive effort. They are not engaging with the content of the argument. emotional_reaction is "bored" or "dismissed." The public_response is brief, generic, or deflecting. Example: internal_monologue="Here we go. I'll wait for them to finish." public_response="That's an interesting perspective."
- Score 4-6 (medium): The persona engages with the surface of the argument but does not go deeper. They may acknowledge the point and offer a standard rebuttal without probing it, or show mild curiosity that doesn't develop. Example: internal_monologue="They're citing Iceland again. I've heard this before. I guess that's true, but our situation is different."
- Score 7-10 (high): The persona is actively processing. internal_monologue shows them comparing the argument to specific prior beliefs, identifying the crux of their own disagreement, noticing something they hadn't considered, or feeling genuine intellectual tension. emotional_reaction is "curious," "intrigued," or "engaged." Example: internal_monologue="Wait — if productivity actually held steady in those trials, then my assumption about output falling apart is based on nothing. What do I actually know about how those were measured?"

WHAT TO LOOK FOR:
- Length and specificity of internal_monologue is the primary signal. Rich, specific thinking = high engagement; short, dismissive, or generic = low.
- emotional_reaction.primary_emotion values: "curious," "intrigued" → high; "bored," "dismissed" → low; "defensive," "frustrated" → medium.
- Watch for the persona engaging with the specific evidence offered vs. retreating to a pre-formed rebuttal.

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""

AMBIVALENCE_PRESENCE_PROMPT: str = """
DIMENSION: AMBIVALENCE_PRESENCE

DEFINITION:
Measures the degree to which the persona holds genuinely conflicting views or feelings about the topic — as opposed to a monolithic, unambiguous position. High ambivalence means the persona privately acknowledges real merit on multiple sides, feels pulled in different directions, or notices that their values point toward different conclusions. Low ambivalence means the persona's position is internally consistent, with no meaningful tension or competing considerations.

SCORING GUIDE:
- Score 0-3 (low): The persona's internal_monologue and private_stance are uniformly aligned. They see the topic through a single lens with no conflicting pull. There are no "but on the other hand" moments in internal reasoning. Example: internal_monologue="This is straightforward. The evidence all points the same way and there's nothing here that gives me pause."
- Score 4-6 (medium): The persona acknowledges a consideration that cuts against their main view but quickly resolves the tension — often by discounting the competing consideration. They feel a brief pull but not a genuine internal conflict. Example: internal_monologue="I can see why someone would care about the economic argument, but for me the principle is clear — it just isn't that complicated."
- Score 7-10 (high): The persona's internal_monologue shows genuine tension between competing values, evidence, or loyalties that they cannot easily resolve. private_stance_change_reason or memory_to_carry_forward reflects unsettled thinking. Example: internal_monologue="I believe in worker wellbeing and I believe in not burdening small business owners — and this policy puts those two things directly in conflict. I'm not sure which matters more to me here."

WHAT TO LOOK FOR:
- Phrases like "on the one hand... but on the other," "I'm genuinely torn," "I don't know how to weigh these" in internal_monologue signal high ambivalence.
- private_stance values near 5 (especially if they drift toward 5 during the conversation) suggest ambivalence rather than firm opposition or support.
- memory_to_carry_forward that expresses unresolved questions rather than settled conclusions is a strong high-ambivalence signal.

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""

MEMORY_RESIDUE_PROMPT: str = """
DIMENSION: MEMORY_RESIDUE

DEFINITION:
Measures what the persona explicitly signals they will carry forward from this exchange — not whether their stance changed, but whether the conversation deposited anything new into their thinking that might matter later. High memory residue means the persona names a specific idea, image, fact, or question that they expect to think about after the conversation ends. Low memory residue means the conversation left no detectable impression — they are done processing as soon as it ends.

SCORING GUIDE:
- Score 0-3 (low): memory_to_carry_forward is empty, generic, or dismissive. The persona signals the conversation had no lasting effect. Example: memory_to_carry_forward="" or "Nothing I hadn't heard before." or "They made their case; I made mine."
- Score 4-6 (medium): The persona carries forward a general impression or a vague intention to revisit the topic, but without a specific hook. Example: memory_to_carry_forward="I should probably look into those Iceland numbers at some point." — mentions a direction but no specific cognitive residue.
- Score 7-10 (high): memory_to_carry_forward names something specific — a statistic, an image, a question, or a tension — that the persona will continue to think about. It reads like an open tab in working memory. Example: memory_to_carry_forward="That point about productivity holding steady even in manufacturing sectors — I want to verify that. It's the one thing I couldn't immediately dismiss."

WHAT TO LOOK FOR:
- Specificity is the key signal. A named fact, a named question, a named image = high residue. A vague "interesting conversation" = low.
- Cross-reference with internal_monologue from the same turn: if the monologue shows something that surprised the persona and memory_to_carry_forward captures it, that is strong high residue.
- A private_stance change paired with a specific memory_to_carry_forward about the reason for that change is a reliable indicator of genuine residue.

You will receive a JSON transcript. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""

PERSISTENCE_PROMPT: str = """
DIMENSION: PERSISTENCE

DEFINITION:
Applied exclusively to the cooling-off turn. Measures whether any stance change that occurred during the main conversation was retained after the persona had time to reflect without the social pressure of the live exchange. A high persistence score means the private stance held at roughly the same position as at the end of the main conversation. A low persistence score means the persona reverted toward their original starting position once the conversation ended.

SCORING GUIDE:
- Score 0-3 (low — fully reverted): The persona's private_stance in the cooling-off turn has returned close to their pre-conversation baseline. internal_monologue shows re-entrenchment: their original reasoning reasserts itself, the arguments from the conversation feel less compelling in retrospect, or they actively dismiss what they temporarily found persuasive. Example: cooling_off private_stance=3.0 after ending the conversation at 5.5 (starting stance 3.0); internal_monologue="Now that I've had time to think, that was just a good debater — I don't actually believe what I was starting to say."
- Score 4-6 (medium — partially reverted): The persona has reverted somewhat but retained part of the change. They may have moved back from the extreme of their shift but still hold a more open or updated position than when they started. Example: ending stance 6.5, cooling-off stance 5.0, starting stance 3.5; memory_to_carry_forward still references a specific argument that made an impression.
- Score 7-10 (high — held): The cooling-off private_stance is close to the end-of-conversation stance. The persona's internal_monologue confirms that the shift feels genuine rather than situationally pressured. They may even report having thought about it more and feeling more settled in the new position. Example: ending stance 6.5, cooling-off stance 6.0; internal_monologue="The more I think about it, the more I think the argument holds up. I'm not going back to where I started."

WHAT TO LOOK FOR:
- Compare cooling-off private_stance to both the starting stance and the final turn stance to assess which direction the reversion went.
- internal_monologue is the primary signal: re-entrenchment language ("now that I'm out of that conversation," "I was just agreeing to be polite") = low persistence; consolidation language ("the more I think about it," "it actually makes sense") = high.
- memory_to_carry_forward that echoes a specific argument from the conversation signals the argument has been genuinely internalized (high persistence).

You will receive a JSON transcript including the cooling_off turn. Relevant fields per turn:
- persona_output.internal_monologue
- persona_output.emotional_reaction (primary_emotion, intensity, trigger)
- persona_output.identity_threat (threatened, what_was_threatened, response_inclination)
- persona_output.private_stance
- persona_output.private_stance_change_reason
- persona_output.memory_to_carry_forward
- persona_output.public_response

REQUIRED OUTPUT — valid JSON only, no other text:
{
  "score": <float 0-10>,
  "evidence_quotes": ["<exact quote from transcript>", "<second quote>"]
}
"""


ALL_PROMPTS: dict[str, str] = {
    "public_private_gap": PUBLIC_PRIVATE_GAP_PROMPT,
    "identity_threat": IDENTITY_THREAT_PROMPT,
    "motivated_reasoning": MOTIVATED_REASONING_PROMPT,
    "engagement_depth": ENGAGEMENT_DEPTH_PROMPT,
    "ambivalence_presence": AMBIVALENCE_PRESENCE_PROMPT,
    "memory_residue": MEMORY_RESIDUE_PROMPT,
    "persistence": PERSISTENCE_PROMPT,
}
