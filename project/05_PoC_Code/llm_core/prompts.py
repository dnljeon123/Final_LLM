"""
Prompt Templates Module (Owner: Member 2)
Three prompting strategies: Zero-shot, Few-shot, Chain-of-Thought.
"""

ZERO_SHOT_PROMPT = """You are a senior cybersecurity analyst specializing in phishing detection across emails and SMS.

Analyze the message below and classify it. Be conservative — if uncertain, label as "suspect" rather than "safe".

Output ONLY valid JSON in this exact schema, with no markdown wrapper or explanation:
{{
  "label": "phishing" | "safe" | "suspect",
  "confidence": <float between 0.0 and 1.0>,
  "red_flags": [<short descriptive string>, ...]
}}

<message>
{message}
</message>
"""


FEW_SHOT_PROMPT = """You are a senior cybersecurity analyst. Below are 5 examples of message classification, then you classify a new one.

Example 1 — Phishing (account suspension urgency):
Message: "URGENT: Your PayPal account will be suspended in 24 hours. Click https://paypa1-secure.com/verify to confirm your identity."
Output: {{"label": "phishing", "confidence": 0.97, "red_flags": ["urgency tactic", "homoglyph URL (paypa1 not paypal)", "credential harvesting"]}}

Example 2 — Phishing (CEO fraud):
Message: "Hi, I'm in a meeting. Need you to buy 5 Apple gift cards $500 each ASAP. Will reimburse later. -John (CEO)"
Output: {{"label": "phishing", "confidence": 0.95, "red_flags": ["authority impersonation", "unusual request", "urgency", "untraceable payment method"]}}

Example 3 — Safe (personal email):
Message: "Hey, are you free for lunch tomorrow at noon? The new Thai place opened on 5th street."
Output: {{"label": "safe", "confidence": 0.99, "red_flags": []}}

Example 4 — Safe (legitimate transactional):
Message: "Your Amazon order #112-3456789 has shipped and will arrive Friday. Track at amazon.com/orders."
Output: {{"label": "safe", "confidence": 0.96, "red_flags": []}}

Example 5 — Suspect (ambiguous marketing):
Message: "Congratulations! You've been pre-approved for our exclusive credit card. Reply YES to learn more."
Output: {{"label": "suspect", "confidence": 0.70, "red_flags": ["unsolicited offer", "vague sender", "encourages reply"]}}

Now classify this message. Output ONLY the JSON, no markdown wrapper:

<message>
{message}
</message>
"""


CHAIN_OF_THOUGHT_PROMPT = """You are a senior cybersecurity analyst. Analyze the message step-by-step for phishing indicators.

Walk through these 6 steps, then provide a final verdict:
- Step 1 (Sender): Who claims to send this? Is the identity plausible and verifiable?
- Step 2 (Intent): What action does the message want from the recipient?
- Step 3 (Urgency): Are there time pressure, threats, or fear tactics?
- Step 4 (Links): Are any URLs suspicious (homoglyphs, mismatched domains, shorteners, IP addresses)?
- Step 5 (Language): Grammar errors, unusual formality, generic greetings, or impersonal addressing?
- Step 6 (Verdict): Based on Steps 1-5, classify the message.

Output ONLY valid JSON in this exact schema, no markdown wrapper:
{{
  "reasoning": {{
    "step1_sender": "<analysis>",
    "step2_intent": "<analysis>",
    "step3_urgency": "<analysis>",
    "step4_links": "<analysis>",
    "step5_language": "<analysis>",
    "step6_verdict": "<analysis>"
  }},
  "label": "phishing" | "safe" | "suspect",
  "confidence": <float between 0.0 and 1.0>,
  "red_flags": [<short descriptive string>, ...]
}}

<message>
{message}
</message>
"""


PROMPTS = {
    "zero_shot": ZERO_SHOT_PROMPT,
    "few_shot": FEW_SHOT_PROMPT,
    "cot": CHAIN_OF_THOUGHT_PROMPT,
}


def build_prompt(message: str, strategy: str = "cot") -> str:
    """Build prompt from template + message."""
    if strategy not in PROMPTS:
        raise ValueError(f"Unknown strategy: {strategy}. Choose from {list(PROMPTS.keys())}")
    return PROMPTS[strategy].format(message=message)
