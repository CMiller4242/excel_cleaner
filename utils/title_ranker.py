"""
Healthcare Title Ranking System
Assigns priority scores to job titles for contact selection
"""

import re
from typing import Tuple


class HealthcareTitleRanker:
    """
    Rank healthcare job titles by decision-making authority.

    Ranking Scale (lower number = higher priority):
    1 = Executive Leadership (C-suite, VPs)
    2 = Senior Directors / Department Heads
    3 = Mid-Level Management (Managers, Administrators)
    4 = Supervisors / Team Leads
    5 = Clinical Titles (Nurses, NPs, PAs, Technicians)
    6 = Administrative Support
    7 = Unknown / Other
    """

    # Rank 1: Executive Leadership
    EXECUTIVE_KEYWORDS = [
        'CHIEF', 'CEO', 'CFO', 'COO', 'CMO', 'CNO', 'CIO', 'CTO',
        'PRESIDENT',
        'VICE PRESIDENT', 'VP', 'V.P.',
        'CHIEF EXECUTIVE', 'CHIEF OPERATING', 'CHIEF FINANCIAL',
        'CHIEF MEDICAL', 'CHIEF NURSING', 'CHIEF CLINICAL',
        'CHIEF ADMINISTRATIVE', 'CHIEF INFORMATION',
        'EXECUTIVE VICE PRESIDENT', 'EVP'
    ]

    # Rank 2: Senior Directors / Department Heads
    DIRECTOR_KEYWORDS = [
        'EXECUTIVE DIRECTOR',
        'SENIOR DIRECTOR',
        'DIRECTOR',
        'DEPT HEAD', 'DEPARTMENT HEAD',
        'HEAD OF'
    ]

    # Rank 3: Mid-Level Management
    MANAGER_KEYWORDS = [
        'MANAGER',
        'ADMINISTRATOR',
        'COORDINATOR',
        'PRACTICE MANAGER', 'OFFICE MANAGER',
        'NURSING MANAGER', 'NURSE MANAGER',
        'OPERATIONS MANAGER', 'CLINICAL MANAGER',
        'PATIENT SERVICES MANAGER',
        'HEALTH INFORMATION MANAGER'
    ]

    # Rank 4: Supervisors / Team Leads
    SUPERVISOR_KEYWORDS = [
        'SUPERVISOR',
        'TEAM LEAD', 'LEAD',
        'CHARGE', 'CHARGE NURSE',
        'UNIT SUPERVISOR', 'NURSING SUPERVISOR'
    ]

    # Rank 5: Clinical Titles
    CLINICAL_KEYWORDS = [
        'NURSE PRACTITIONER', 'NP',
        'PHYSICIAN ASSISTANT', 'PA',
        'REGISTERED NURSE', 'RN',
        'LICENSED PRACTICAL NURSE', 'LPN',
        'MEDICAL ASSISTANT', 'MA',
        'NURSE',
        'TECHNICIAN', 'TECH',
        'TECHNOLOGIST',
        'THERAPIST',
        'SPECIALIST'
    ]

    # Rank 6: Administrative Support
    ADMIN_KEYWORDS = [
        'ADMINISTRATIVE ASSISTANT',
        'EXECUTIVE ASSISTANT',
        'ASSISTANT',
        'RECEPTIONIST', 'RECEPTION',
        'FRONT DESK',
        'PATIENT ACCESS',
        'SECRETARY',
        'CLERK'
    ]

    @classmethod
    def rank_title(cls, title: str) -> Tuple[int, str]:
        """
        Rank a job title by decision-making authority.

        Args:
            title: Job title string

        Returns:
            Tuple of (rank_number, rank_name)
            - rank_number: 1-7 (lower = higher priority)
            - rank_name: Human-readable rank category
        """
        if not title or not isinstance(title, str):
            return (7, "Unknown")

        # Normalize title for matching
        title_upper = title.upper().strip()

        # Check each rank in priority order

        # Rank 1: Executive
        if any(keyword in title_upper for keyword in cls.EXECUTIVE_KEYWORDS):
            return (1, "Executive Leadership")

        # Rank 2: Director
        if any(keyword in title_upper for keyword in cls.DIRECTOR_KEYWORDS):
            return (2, "Senior Director")

        # Rank 3: Manager/Administrator
        if any(keyword in title_upper for keyword in cls.MANAGER_KEYWORDS):
            return (3, "Manager/Administrator")

        # Rank 4: Supervisor
        if any(keyword in title_upper for keyword in cls.SUPERVISOR_KEYWORDS):
            return (4, "Supervisor/Lead")

        # Rank 5: Clinical
        if any(keyword in title_upper for keyword in cls.CLINICAL_KEYWORDS):
            return (5, "Clinical")

        # Rank 6: Administrative Support
        if any(keyword in title_upper for keyword in cls.ADMIN_KEYWORDS):
            return (6, "Administrative Support")

        # Rank 7: Unknown
        return (7, "Unknown/Other")

    @classmethod
    def get_rank_number(cls, title: str) -> int:
        """Get just the rank number (for sorting)"""
        return cls.rank_title(title)[0]

    @classmethod
    def get_rank_name(cls, title: str) -> str:
        """Get just the rank category name"""
        return cls.rank_title(title)[1]
