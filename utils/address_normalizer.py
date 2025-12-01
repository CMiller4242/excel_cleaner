"""
Address Normalization Utility
Standardizes address abbreviations for accurate duplicate detection
"""

import re


class AddressNormalizer:
    """
    Normalize addresses by expanding abbreviations and standardizing format.

    Handles:
    - Street type abbreviations (ST → STREET, AVE → AVENUE, etc.)
    - Directional abbreviations (N → NORTH, SW → SOUTHWEST)
    - Unit designators (STE → SUITE, APT → APARTMENT)
    - Common variations and misspellings
    """

    # Street type abbreviations (USPS standard + common variations)
    STREET_TYPES = {
        # Primary street types
        'ALY': 'ALLEY',
        'ALLEY': 'ALLEY',
        'AVE': 'AVENUE',
        'AVENUE': 'AVENUE',
        'BLVD': 'BOULEVARD',
        'BOULEVARD': 'BOULEVARD',
        'CIR': 'CIRCLE',
        'CIRCLE': 'CIRCLE',
        'CT': 'COURT',
        'COURT': 'COURT',
        'DR': 'DRIVE',
        'DRIVE': 'DRIVE',
        'HWY': 'HIGHWAY',
        'HIGHWAY': 'HIGHWAY',
        'LN': 'LANE',
        'LANE': 'LANE',
        'PKWY': 'PARKWAY',
        'PARKWAY': 'PARKWAY',
        'PL': 'PLACE',
        'PLACE': 'PLACE',
        'RD': 'ROAD',
        'ROAD': 'ROAD',
        'SQ': 'SQUARE',
        'SQUARE': 'SQUARE',
        'ST': 'STREET',
        'STREET': 'STREET',
        'TER': 'TERRACE',
        'TERRACE': 'TERRACE',
        'TRL': 'TRAIL',
        'TRAIL': 'TRAIL',
        'WAY': 'WAY',

        # Additional common abbreviations
        'BLVRD': 'BOULEVARD',
        'CRC': 'CIRCLE',
        'CRCL': 'CIRCLE',
        'CRCLE': 'CIRCLE',
        'CRESCENT': 'CRESCENT',
        'CRES': 'CRESCENT',
        'CRSNT': 'CRESCENT',
        'EXPWY': 'EXPRESSWAY',
        'EXPRESSWAY': 'EXPRESSWAY',
        'FRWY': 'FREEWAY',
        'FREEWAY': 'FREEWAY',
        'LOOP': 'LOOP',
        'PIKE': 'PIKE',
        'TPKE': 'TURNPIKE',
        'TURNPIKE': 'TURNPIKE',
    }

    # Directional abbreviations
    DIRECTIONALS = {
        'N': 'NORTH',
        'S': 'SOUTH',
        'E': 'EAST',
        'W': 'WEST',
        'NE': 'NORTHEAST',
        'NW': 'NORTHWEST',
        'SE': 'SOUTHEAST',
        'SW': 'SOUTHWEST',
        'NORTH': 'NORTH',
        'SOUTH': 'SOUTH',
        'EAST': 'EAST',
        'WEST': 'WEST',
        'NORTHEAST': 'NORTHEAST',
        'NORTHWEST': 'NORTHWEST',
        'SOUTHEAST': 'SOUTHEAST',
        'SOUTHWEST': 'SOUTHWEST',
    }

    # Unit designators
    UNIT_TYPES = {
        'APT': 'APARTMENT',
        'APARTMENT': 'APARTMENT',
        'BLDG': 'BUILDING',
        'BUILDING': 'BUILDING',
        'FL': 'FLOOR',
        'FLOOR': 'FLOOR',
        'FLR': 'FLOOR',
        'RM': 'ROOM',
        'ROOM': 'ROOM',
        'STE': 'SUITE',
        'SUITE': 'SUITE',
        'UNIT': 'UNIT',
        '#': 'NUMBER',
    }

    @classmethod
    def normalize(cls, address: str) -> str:
        """
        Normalize an address to standard format.

        Args:
            address: Address string to normalize

        Returns:
            Normalized address string (uppercase, expanded abbreviations)
        """
        if not address or not isinstance(address, str):
            return ""

        # Convert to uppercase
        normalized = address.upper().strip()

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        # Remove punctuation (except # for unit numbers)
        normalized = re.sub(r'[,\.;]', ' ', normalized)
        normalized = ' '.join(normalized.split())

        # Expand abbreviations
        words = normalized.split()
        expanded_words = []

        for i, word in enumerate(words):
            # Check if it's a street type
            if word in cls.STREET_TYPES:
                expanded_words.append(cls.STREET_TYPES[word])
            # Check if it's a directional
            elif word in cls.DIRECTIONALS:
                expanded_words.append(cls.DIRECTIONALS[word])
            # Check if it's a unit type
            elif word in cls.UNIT_TYPES:
                expanded_words.append(cls.UNIT_TYPES[word])
            else:
                expanded_words.append(word)

        normalized = ' '.join(expanded_words)

        return normalized

    @classmethod
    def normalize_dataframe_column(cls, series):
        """
        Normalize all addresses in a pandas Series.

        Args:
            series: Pandas Series containing addresses

        Returns:
            Normalized Series
        """
        return series.apply(cls.normalize)


class TextNormalizer:
    """
    General text normalization for fuzzy matching.
    Less aggressive than address normalization.
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text for comparison.

        - Uppercase
        - Remove extra whitespace
        - Remove punctuation
        - Trim
        """
        if not text or not isinstance(text, str):
            return ""

        # Uppercase
        normalized = text.upper().strip()

        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        return normalized
