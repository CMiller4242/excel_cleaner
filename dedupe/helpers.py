"""
Helper functions for deduplication processing
"""

import re
from fuzzywuzzy import fuzz
import pandas as pd

def normalize_email(email):
    """
    Normalize email for comparison

    Args:
        email: Email string

    Returns:
        str: Normalized email (lowercase, stripped)
    """
    if pd.isna(email) or not email:
        return ""

    return str(email).lower().strip()

def normalize_phone(phone):
    """
    Strip all non-digit characters from phone number

    Args:
        phone: Phone number string

    Returns:
        str: Digits only
    """
    if pd.isna(phone) or not phone:
        return ""

    return re.sub(r'\D', '', str(phone))

def normalize_text(text):
    """
    Normalize text for comparison (lowercase, strip, remove extra spaces)

    Args:
        text: Text string

    Returns:
        str: Normalized text
    """
    if pd.isna(text) or not text:
        return ""

    text = str(text).lower().strip()
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space

    return text

def fuzzy_match(str1, str2, threshold=85):
    """
    Check if two strings match above threshold using fuzzy ratio

    Args:
        str1: First string
        str2: Second string
        threshold: Minimum similarity score (0-100)

    Returns:
        tuple: (is_match: bool, similarity: int)
    """
    if not str1 or not str2:
        return False, 0

    similarity = fuzz.ratio(normalize_text(str1), normalize_text(str2))
    is_match = similarity >= threshold

    return is_match, similarity

def get_match_reason(tier, similarity_scores=None):
    """
    Generate human-readable match reason

    Args:
        tier: Match tier (1, 2, or 3)
        similarity_scores: Dict of similarity scores (optional)

    Returns:
        str: Match reason description
    """
    reasons = {
        1: "Tier 1: Exact email match",
        2: "Tier 2: Phone + Name match",
        3: "Tier 3: Company + Location + Name match"
    }

    reason = reasons.get(tier, "Unknown")

    if similarity_scores:
        details = []
        for key, value in similarity_scores.items():
            details.append(f"{key}={value}%")

        if details:
            reason += f" ({', '.join(details)})"

    return reason
