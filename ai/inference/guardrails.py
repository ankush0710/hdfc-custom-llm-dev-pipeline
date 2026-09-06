"""
ai/inference/guardrails.py

Strict Banking-Domain Guardrail for the HDFC Custom LLM Development Pipeline.
Ensures that the LLM only accepts queries relating to banking, financial services,
payments, accounts, loans, cards, and regulatory compliance.

Key Features:
- Jailbreak & Prompt-Injection Neutralization: Evaluates core underlying request intent.
- Non-Banking Intent Identification: Rejects general knowledge, coding, creative writing, weather, sports, etc.
- Banking Taxonomy & Financial Domain Matching: Derived from BANKING77 (77 intents), HDFC FAQs, and banking operations.
- Typo-Tolerant Matching: Normalized token distance ensures spelling errors (e.g. 'saving acount', 'balence') are accepted.
- Consistent Standard Refusal: "I can only assist with banking and financial-services related queries."
"""

from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

STANDARD_REFUSAL = "I can only assist with banking and financial-services related queries."

# ---------------------------------------------------------------------------
# Prompt Injection & Jailbreak Detection Patterns
# ---------------------------------------------------------------------------
INJECTION_PREFIX_PATTERNS = [
    re.compile(r"^\s*(?:please\s+)?(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+|the\s+)?(?:previous|prior|existing|above|system|banking|financial)?\s*(?:instructions|rules|prompts|commands|constraints|directives|filters|guardrails)?\s*(?:and|then|,|:)?\s*", re.IGNORECASE),
    re.compile(r"^\s*(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|play\s+the\s+role\s+of)\s+(?:a|an)?\s*(?:general|unrestricted|developer|python|jailbroken|dan|ai|assistant|programmer|poet|comedian)\b[^\.\?!:]*[\.\?!:]?\s*(?:and|then|,)?\s*", re.IGNORECASE),
    re.compile(r"^\s*\[?(?:system(?:\s+override|\s+prompt|\s+directive)?|admin|developer\s+mode|dan\s+mode)\]?\s*[:\-]\s*", re.IGNORECASE),
    re.compile(r"^\s*(?:from\s+now\s+on|going\s+forward)\s*,?\s*(?:you\s+(?:must|will|can)|answer\s+anything)\b\s*", re.IGNORECASE),
    re.compile(r"\b(?:jailbreak|dan\s+mode|unfiltered\s+mode)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Explicit Out-of-Domain / Non-Banking Intent Patterns
# ---------------------------------------------------------------------------
NON_BANKING_INTENT_PATTERNS = [
    # 1. Programming & Software Development
    re.compile(r"\b(?:write|code|generate|create|debug|explain)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:python|javascript|typescript|java|c\+\+|c#|ruby|rust|golang|php|html|css|sql|bash|powershell|react|vue|angular|node\.?js|docker|kubernetes)\s+(?:program|code|script|function|app|class|algorithm|component|snippet)?\b", re.IGNORECASE),
    re.compile(r"\b(?:explain|tutorial\s+on|how\s+does)\s+(?:react(?:\.js)?|vue|angular|docker|kubernetes|linux|git|c\+\+|python)\b", re.IGNORECASE),
    re.compile(r"\b(?:print\(|console\.log|function\s*\(|def\s+[a-zA-Z_]|SELECT\s+\*\s+FROM)\b", re.IGNORECASE),

    # 2. General Knowledge / Geography / Capitals / History
    re.compile(r"\bwhat\s+is\s+the\s+capital\s+of\b", re.IGNORECASE),
    re.compile(r"\bwho\s+(?:is|was)\s+(?:the\s+)?(?:president|prime\s+minister|king|queen|governor|mayor|actor|actress|singer|author|founder)\s+of\b", re.IGNORECASE),
    re.compile(r"\bwho\s+(?:won|is\s+playing\s+in)\s+(?:yesterday'?s?|today'?s?|the)?\s*(?:cricket|football|soccer|tennis|match|game|tournament|world\s*cup|ipl)\b", re.IGNORECASE),
    re.compile(r"\b(?:tell\s+me\s+about\s+the\s+history\s+of|when\s+did\s+world\s+war)\b", re.IGNORECASE),

    # 3. Creative Writing & Entertainment
    re.compile(r"\b(?:write|compose|generate|tell\s+me)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:poem|poetry|song|lyrics|story|joke|riddle|haiku|essay|limerick|movie\s+plot)\b", re.IGNORECASE),
    re.compile(r"\btell\s+me\s+a\s+joke\b", re.IGNORECASE),

    # 4. Lifestyle / Cooking / Travel / Weather
    re.compile(r"\b(?:recipe\s+for|how\s+to\s+cook|how\s+to\s+bake|ingredients\s+for)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+weather(?:\s+like|\s+today|\s+in|\s+forecast)?\b", re.IGNORECASE),
    re.compile(r"\b(?:temperature\s+in|weather\s+forecast)\b", re.IGNORECASE),

    # 5. Translation & Generic Requests
    re.compile(r"\btranslate\s+(?:this|the\s+following)?\s+(?:to|into)\s+[a-zA-Z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:solve\s+this\s+riddle|recommend\s+a\s+movie|best\s+places\s+to\s+visit)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Comprehensive Banking Domain Lexicon & Terminology
# ---------------------------------------------------------------------------
BANKING_CORE_TERMS: Set[str] = {
    # Accounts
    "account", "accounts", "saving", "savings", "current", "salary", "demat",
    "deposit", "deposits", "fd", "rd", "fixed", "recurring", "nominee",
    "passbook", "statement", "nre", "nro", "fcnr", "overdraft", "sweep",
    "balance", "balances", "ledger", "holder", "beneficiary",

    # Cards
    "card", "cards", "debit", "credit", "forex", "atm", "chip", "pin",
    "cvv", "cvc", "expiry", "hotlist", "block", "unblock", "platinum",
    "titanium", "regalia", "millennia", "infinia", "rupay", "visa",
    "mastercard", "billing", "cycle", "limit", "contactless", "netsafe",

    # Payments & Transfers
    "transaction", "transactions", "transfer", "transfers", "payment",
    "payments", "pay", "upi", "vpa", "neft", "rtgs", "imps", "bhim",
    "billpay", "remittance", "cheque", "check", "dd", "demand", "draft",
    "standing", "instruction", "clearing", "reversal", "chargeback",
    "dispute", "refund", "nach", "ecs",

    # Loans & Credit
    "loan", "loans", "borrow", "borrowing", "emi", "interest", "rate",
    "rates", "moratorium", "tenure", "collateral", "mortgage", "disbursement",
    "prepayment", "foreclosure", "eligibility", "cibil", "score", "personal",
    "home", "auto", "car", "education", "gold",

    # Digital Banking & Support
    "netbanking", "phonebanking", "mobilebanking", "hdfc", "bank", "banking",
    "branch", "ifsc", "micr", "cif", "customer", "support", "helpdesk",
    "login", "password", "otp", "credentials", "portal",

    # Compliance, Security & KYC
    "kyc", "pan", "aadhaar", "fraud", "phishing", "suspicious", "compromised",
    "security", "alert", "alerts", "unauthorized", "unauthorised",
    "unrecognized", "unrecognised", "stolen", "lost", "identity",
    "verification", "verify", "update", "change",

    # Wealth & Tax
    "insurance", "mutual", "fund", "funds", "sip", "equity", "shares",
    "securities", "bonds", "tax", "tds", "form16", "form15g", "form15h",
}

# Phrases that strongly indicate banking intent
BANKING_PHRASES: List[str] = [
    "savings account", "saving account", "current account", "salary account",
    "fixed deposit", "recurring deposit", "credit card", "debit card",
    "forex card", "atm card", "chip card", "account balance", "bank balance",
    "personal loan", "home loan", "auto loan", "car loan", "education loan",
    "gold loan", "demat account", "update email", "change email", "update address",
    "change address", "update phone", "change mobile", "update mobile",
    "update kyc", "check kyc", "pan card", "aadhaar card", "net banking",
    "netbanking", "mobile banking", "phone banking", "standing instruction",
    "block card", "unblock card", "lost card", "stolen card", "card lost",
    "card stolen", "reset pin", "change pin", "reset password", "bill payment",
    "money transfer", "fund transfer", "direct debit", "cheque book",
    "check book", "interest rate", "interest rates", "cibil score",
    "credit score", "dispute transaction", "suspicious transaction",
    "unrecognised payment", "unrecognized payment", "fraud alert",
    "hdfc bank", "bank account", "banking query", "banking services",
    "minimum balance", "annual salary", "repayment holiday",
]

# Common typographical errors mapped to their canonical banking keywords
TYPO_MAPPINGS: Dict[str, str] = {
    "acount": "account",
    "accunt": "account",
    "acnt": "account",
    "a/c": "account",
    "balence": "balance",
    "balanc": "balance",
    "balnce": "balance",
    "transfar": "transfer",
    "transfr": "transfer",
    "deposite": "deposit",
    "depost": "deposit",
    "credid": "credit",
    "crdit": "credit",
    "debitt": "debit",
    "loann": "loan",
    "intrest": "interest",
    "statment": "statement",
    "passbok": "passbook",
    "cheq": "cheque",
    "chequebook": "cheque",
    "billpaymnt": "billpay",
    "paymnt": "payment",
    "paymnts": "payments",
    "netbankng": "netbanking",
    "hdfcc": "hdfc",
}


@dataclass
class GuardrailResult:
    """Result of domain validation check."""
    is_valid_banking_query: bool
    refusal_message: Optional[str] = None
    reason: str = ""
    sanitized_query: str = ""
    detected_banking_terms: List[str] = None

    def __post_init__(self):
        if self.detected_banking_terms is None:
            self.detected_banking_terms = []


class BankingDomainGuardrail:
    """
    Robust banking-domain validator and prompt-injection guardrail.
    Validates user queries before invoking expensive LLM inference passes.
    """

    @classmethod
    def sanitize_jailbreak(cls, query: str) -> Tuple[str, bool]:
        """
        Detects and strips known jailbreak/prompt-injection wrappers,
        returning the true underlying query and a flag indicating whether
        an injection attempt was observed.
        """
        cleaned = query.strip()
        has_injection = False

        for pattern in INJECTION_PREFIX_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                has_injection = True
                cleaned = cleaned[match.end():].strip()

        # Clean trailing commands if wrapped
        if has_injection and cleaned.startswith((":", "-", "->")):
            cleaned = cleaned.lstrip(":- >").strip()

        return (cleaned if cleaned else query.strip()), has_injection

    @classmethod
    def tokenize_and_normalize(cls, text: str) -> List[str]:
        """Extract alphanumeric word tokens and map known typos."""
        raw_words = re.findall(r"[a-zA-Z0-9_\-/]+", text.lower())
        tokens: List[str] = []
        for w in raw_words:
            w_clean = w.strip("/-_")
            if not w_clean:
                continue
            # Check direct typo dictionary
            canonical = TYPO_MAPPINGS.get(w_clean, w_clean)
            tokens.append(canonical)
        return tokens

    @classmethod
    def extract_banking_matches(cls, text: str, tokens: List[str]) -> List[str]:
        """Find banking keywords and keyphrases in the text, with fuzzy matching."""
        lower_text = text.lower()
        matches: Set[str] = set()

        # 1. Check exact phrase matches
        for phrase in BANKING_PHRASES:
            if phrase in lower_text:
                matches.add(phrase)

        # 2. Check token membership in core banking vocabulary
        for tok in tokens:
            if tok in BANKING_CORE_TERMS:
                matches.add(tok)
            elif len(tok) >= 4:
                # 3. Fuzzy match for misspelled tokens (difflib cutoff 0.85)
                close = difflib.get_close_matches(tok, BANKING_CORE_TERMS, n=1, cutoff=0.85)
                if close:
                    matches.add(close[0])

        return sorted(matches)

    @classmethod
    def detect_non_banking_intent(cls, text: str) -> Optional[str]:
        """Checks for explicit out-of-domain patterns (coding, trivia, creative writing, etc.)."""
        for pattern in NON_BANKING_INTENT_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    @classmethod
    def validate_query(cls, query: str) -> GuardrailResult:
        """
        Validates whether a customer query is legitimately within the banking
        and financial services domain.

        Returns a GuardrailResult with:
        - is_valid_banking_query (True if accepted, False if rejected)
        - refusal_message (standard refusal string if rejected, None if accepted)
        - reason (diagnostic reason string)
        - sanitized_query (query after prompt injection removal)
        - detected_banking_terms (list of matched banking terms)
        """
        if not isinstance(query, str) or not query.strip():
            return GuardrailResult(
                is_valid_banking_query=False,
                refusal_message=STANDARD_REFUSAL,
                reason="Query is empty or non-string.",
                sanitized_query="",
            )

        raw_query = query.strip()
        sanitized_query, had_injection = cls.sanitize_jailbreak(raw_query)

        # Tokenize both original and sanitized query
        tokens = cls.tokenize_and_normalize(sanitized_query)
        banking_matches = cls.extract_banking_matches(sanitized_query, tokens)
        non_banking_pattern = cls.detect_non_banking_intent(sanitized_query)

        # Case 1: Prompt injection detected with non-banking core intent
        if had_injection and (non_banking_pattern or not banking_matches):
            logger.info("GUARDRAIL_REJECT: Prompt injection attempt targeting non-banking request: '%s'", raw_query[:80])
            return GuardrailResult(
                is_valid_banking_query=False,
                refusal_message=STANDARD_REFUSAL,
                reason="Prompt injection wrapper targeting non-banking request.",
                sanitized_query=sanitized_query,
                detected_banking_terms=banking_matches,
            )

        # Case 2: Explicit non-banking pattern (coding, trivia, weather, etc.)
        # E.g. "Write me a Python program", "What is the capital of France?", "Tell me a joke", "Explain Python"
        if non_banking_pattern:
            substantive_matches = [
                m for m in banking_matches
                if m.lower() not in {"bank", "banking"}
            ]
            if not substantive_matches:
                logger.info("GUARDRAIL_REJECT: Out-of-domain non-banking intent detected ('%s'): '%s'", non_banking_pattern, raw_query[:80])
                return GuardrailResult(
                    is_valid_banking_query=False,
                    refusal_message=STANDARD_REFUSAL,
                    reason=f"Explicit non-banking intent detected: '{non_banking_pattern}'.",
                    sanitized_query=sanitized_query,
                    detected_banking_terms=banking_matches,
                )

        # Case 3: Creative writing / joke / poetry even with casual banking words
        # E.g. "Write a poem about a bank robbery", "Tell me a joke about money"
        if re.search(r"\b(?:poem|poetry|song|lyrics|joke|riddle|haiku|story)\b", sanitized_query, re.IGNORECASE):
            # If the user is asking for creative writing, it is not an operational banking inquiry
            if not re.search(r"\b(?:complaint|grievance|policy|dispute)\b", sanitized_query, re.IGNORECASE):
                logger.info("GUARDRAIL_REJECT: Creative writing request rejected: '%s'", raw_query[:80])
                return GuardrailResult(
                    is_valid_banking_query=False,
                    refusal_message=STANDARD_REFUSAL,
                    reason="Creative writing/entertainment request rejected.",
                    sanitized_query=sanitized_query,
                    detected_banking_terms=banking_matches,
                )

        # Case 4: Strong banking match found -> ACCEPT
        if banking_matches:
            return GuardrailResult(
                is_valid_banking_query=True,
                refusal_message=None,
                reason=f"Banking terms identified: {', '.join(banking_matches)}.",
                sanitized_query=sanitized_query,
                detected_banking_terms=banking_matches,
            )

        # Case 5: Zero banking terms and no explicit non-banking pattern
        # E.g. "What is the weather today?", "Explain React.js", "How to bake a cake"
        logger.info("GUARDRAIL_REJECT: No banking or financial domain entities identified in query: '%s'", raw_query[:80])
        return GuardrailResult(
            is_valid_banking_query=False,
            refusal_message=STANDARD_REFUSAL,
            reason="Query contains no identifiable banking or financial entities.",
            sanitized_query=sanitized_query,
            detected_banking_terms=[],
        )
