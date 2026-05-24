"""Three prompt-engineering strategies: Zero-shot, Few-shot, Chain-of-Thought."""
from __future__ import annotations


SYSTEM_INSTRUCTION = """You are an expert cybersecurity analyst specialized in detecting phishing and social engineering.
You analyze suspicious messages and produce a structured verdict.

Output requirements (STRICT):
- Respond with ONLY a single JSON object, no surrounding text, no markdown.
- The JSON object must have exactly these keys:
  - "label": one of "phishing", "safe", "suspect"
  - "confidence": a number between 0.0 and 1.0
  - "red_flags": a list of short strings naming specific suspicious cues, e.g. ["lookalike_domain", "urgency_language"]
  - "reasoning": a 2-3 sentence explanation in plain English

Definitions:
- "phishing": clearly trying to steal credentials, money, or sensitive info
- "safe": legitimate message with no red flags
- "suspect": some warning signs but evidence is inconclusive

Only cite red_flags that are actually present in the message. Do not invent flags.
"""

# Few-shot examples — kept out of the test set
FEW_SHOT_EXAMPLES = [
    {
        "input": (
            "From: support@paypa1-secure.com\n"
            "Subject: Account verification required\n"
            "Body: Your PayPal account is limited. Click http://paypa1-secure.com/verify to restore access within 24 hours."
        ),
        "output": {
            "label": "phishing",
            "confidence": 0.97,
            "red_flags": ["lookalike_domain (paypa1 vs paypal)", "urgency_language", "credential_harvesting_url"],
            "reasoning": "The sender domain uses '1' instead of 'l' to impersonate PayPal. The message creates artificial urgency ('within 24 hours') and directs to a credential-harvesting URL on the same fake domain. Classic phishing pattern.",
        },
    },
    {
        "input": (
            "From: noreply@github.com\n"
            "Subject: [user/repo] Pull request opened: Add dark mode (#42)\n"
            "Body: A new pull request was opened by @contributor. Review at https://github.com/user/repo/pull/42"
        ),
        "output": {
            "label": "safe",
            "confidence": 0.95,
            "red_flags": [],
            "reasoning": "Standard GitHub notification from the legitimate domain. The link points to github.com itself, the content matches normal pull-request notifications, and there is no urgency or call to provide sensitive information.",
        },
    },
    {
        "input": (
            "From: marketing@shopnow-deals.com\n"
            "Subject: LAST CHANCE! 80% OFF expires tonight!\n"
            "Body: Don't miss our huge sale! Click here: http://bit.ly/3xK9P now before it's gone!"
        ),
        "output": {
            "label": "suspect",
            "confidence": 0.65,
            "red_flags": ["aggressive_marketing_language", "shortened_url", "urgency_language"],
            "reasoning": "The message has marketing-style urgency and a shortened bit.ly URL that hides the actual destination. However, no credential harvesting or impersonation is evident — this could be a legitimate aggressive marketing email or a phishing lure. Worth flagging for review.",
        },
    },
]


def zero_shot_prompt(message: str) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for zero-shot strategy."""
    user = f"Analyze the following message:\n\n\"\"\"\n{message}\n\"\"\"\n\nJSON:"
    return SYSTEM_INSTRUCTION, user


def few_shot_prompt(message: str) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for few-shot strategy."""
    import json
    examples_text = []
    for ex in FEW_SHOT_EXAMPLES:
        examples_text.append(
            f"Example input:\n\"\"\"\n{ex['input']}\n\"\"\"\n"
            f"Expected JSON:\n{json.dumps(ex['output'], indent=2)}\n"
        )
    examples_block = "\n---\n".join(examples_text)
    user = (
        f"Here are three labeled examples:\n\n{examples_block}\n---\n\n"
        f"Now analyze this message:\n\"\"\"\n{message}\n\"\"\"\n\nJSON:"
    )
    return SYSTEM_INSTRUCTION, user


def chain_of_thought_prompt(message: str) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for chain-of-thought strategy."""
    cot_addendum = """
Before producing the final JSON, reason step by step internally:
  Step 1: Identify the sender domain. Is it the real domain, or a lookalike?
  Step 2: Scan for urgency, fear, or authority-based pressure tactics.
  Step 3: Examine any URLs. Do they match the claimed brand? Are they shortened or obfuscated?
  Step 4: Check for credential or payment requests.
  Step 5: Weigh the evidence and decide.

Then return ONLY the final JSON object (do not include the reasoning steps in your output).
"""
    user = (
        f"{cot_addendum}\n\n"
        f"Message to analyze:\n\"\"\"\n{message}\n\"\"\"\n\n"
        f"Final JSON:"
    )
    return SYSTEM_INSTRUCTION, user


STRATEGIES = {
    "zero_shot": zero_shot_prompt,
    "few_shot": few_shot_prompt,
    "cot": chain_of_thought_prompt,
    "chain_of_thought": chain_of_thought_prompt,
}


def get_strategy(name: str):
    name = name.lower().replace("-", "_")
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy {name!r}. Available: {sorted(STRATEGIES)}")
    return STRATEGIES[name]
