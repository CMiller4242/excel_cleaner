"""
Email Validation Runner

Handles threaded execution of email validation with progress tracking
and EMAIL_VALIDATION sheet generation.
"""

import threading
import logging
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmailValidationRunner:
    """
    Runs email validation in background thread with progress tracking.

    Features:
    - Bulk-first validation with chunking
    - In-session caching (duplicate email detection)
    - Non-fatal error handling
    - Progress reporting via callback
    - EMAIL_VALIDATION sheet generation with traceability
    """

    def __init__(
        self,
        emailable_client,
        workbook_session,
        config: Dict,
        validation_cache: Dict,
        progress_callback: Optional[callable] = None,
        completion_callback: Optional[callable] = None
    ):
        """
        Initialize validation runner.

        Args:
            emailable_client: EmailableClient instance
            workbook_session: WorkbookSession instance
            config: Validation configuration dict with keys:
                - sheets: List of sheet names
                - column_map: {sheet_name: column_name}
                - mode: 'bulk' or 'realtime'
                - chunk_size: int
                - treat_risky_as_bad: bool
            validation_cache: Session validation cache dict
            progress_callback: Optional callback(message, current, total)
            completion_callback: Optional callback(success, result_or_error)
        """
        self.client = emailable_client
        self.workbook_session = workbook_session
        self.config = config
        self.cache = validation_cache
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback

        self.cancelled = False
        self.thread = None

    def start(self):
        """Start validation in background thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def cancel(self):
        """Request cancellation of validation."""
        self.cancelled = True

    def _run(self):
        """Main validation execution (runs in background thread)."""
        try:
            logger.info("Starting email validation")

            # Extract emails from all selected sheets
            email_occurrences = self._extract_emails_from_sheets()

            if not email_occurrences:
                self._complete(True, {
                    'message': 'No email addresses found in selected sheets',
                    'summary': self._empty_summary()
                })
                return

            # Build unique email list
            unique_emails = set(email_occurrences.keys())
            total_occurrences = sum(len(occs) for occs in email_occurrences.values())

            self._progress(f"Found {len(unique_emails)} unique emails ({total_occurrences} total occurrences)", 0, 100)

            # Check cache
            cached_emails = {email for email in unique_emails if email in self.cache}
            uncached_emails = unique_emails - cached_emails

            self._progress(f"Cache hits: {len(cached_emails)}, To validate: {len(uncached_emails)}", 10, 100)

            # Validate uncached emails
            if uncached_emails:
                validation_results = self._validate_emails(list(uncached_emails))

                # Update cache
                for email, result in validation_results.items():
                    self.cache[email] = result

            if self.cancelled:
                self._complete(False, "Validation cancelled")
                return

            # Build EMAIL_VALIDATION dataframe
            self._progress("Building EMAIL_VALIDATION sheet...", 90, 100)
            validation_df = self._build_validation_sheet(email_occurrences)

            # Compute summary
            summary = self._compute_summary(validation_df)

            self._progress("Validation complete!", 100, 100)

            # Store in workbook session
            self.workbook_session.extra_sheets['EMAIL_VALIDATION'] = validation_df

            self._complete(True, {
                'message': 'Email validation completed successfully',
                'summary': summary,
                'sheet_name': 'EMAIL_VALIDATION'
            })

        except Exception as e:
            logger.error(f"Email validation failed: {e}", exc_info=True)
            self._complete(False, f"Validation failed: {e}")

    def _extract_emails_from_sheets(self) -> Dict[str, List[Tuple[str, int]]]:
        """
        Extract email addresses from all selected sheets.

        Returns:
            Dict[normalized_email, List[(sheet_name, row_index)]]
        """
        email_occurrences = defaultdict(list)

        for sheet_name in self.config['sheets']:
            if self.cancelled:
                break

            self._progress(f"Extracting emails from {sheet_name}...", None, None)

            try:
                # Get sheet data
                sheet_state = self.workbook_session.get_sheet(sheet_name)

                # Load if not loaded
                if not sheet_state.is_loaded or sheet_state.df_original is None:
                    self._progress(f"Loading {sheet_name}...", None, None)
                    df = pd.read_excel(self.workbook_session.file_path, sheet_name=sheet_name)
                    self.workbook_session.load_sheet_data(sheet_name, df)
                    sheet_state = self.workbook_session.get_sheet(sheet_name)

                df = sheet_state.df_original
                email_column = self.config['column_map'][sheet_name]

                if email_column not in df.columns:
                    logger.warning(f"Column {email_column} not found in sheet {sheet_name}")
                    continue

                # Extract emails
                for idx, email in df[email_column].items():
                    if pd.isna(email) or not email:
                        continue

                    # Normalize
                    normalized = self._normalize_email(str(email))

                    if not normalized:
                        continue

                    # Basic format validation
                    if not self._is_valid_email_format(normalized):
                        # Record as invalid format
                        email_occurrences[normalized].append((sheet_name, int(idx), 'invalid_format'))
                    else:
                        email_occurrences[normalized].append((sheet_name, int(idx), 'pending'))

            except Exception as e:
                logger.error(f"Failed to extract emails from {sheet_name}: {e}")
                # Continue with other sheets (non-fatal)

        return dict(email_occurrences)

    def _validate_emails(self, emails: List[str]) -> Dict[str, Dict]:
        """
        Validate list of emails using Emailable API.

        Args:
            emails: List of normalized email addresses

        Returns:
            Dict[email, validation_result_dict]
        """
        results = {}
        mode = self.config.get('mode', 'bulk')

        if mode == 'bulk':
            results = self._validate_bulk(emails)
        else:
            results = self._validate_realtime(emails)

        return results

    def _validate_bulk(self, emails: List[str]) -> Dict[str, Dict]:
        """Validate emails using bulk API."""
        results = {}
        chunk_size = self.config.get('chunk_size', 10000)
        chunks = [emails[i:i+chunk_size] for i in range(0, len(emails), chunk_size)]

        total_chunks = len(chunks)

        for chunk_idx, chunk in enumerate(chunks):
            if self.cancelled:
                break

            self._progress(
                f"Processing bulk job {chunk_idx + 1}/{total_chunks} ({len(chunk)} emails)...",
                20 + (chunk_idx * 60 // total_chunks),
                100
            )

            try:
                # Create bulk job
                bulk_id = self.client.create_bulk(chunk)
                logger.info(f"Created bulk job {bulk_id} with {len(chunk)} emails")

                # Wait for completion with progress updates
                def bulk_progress(total, processed, status):
                    if not self.cancelled:
                        percent = (processed / total * 100) if total > 0 else 0
                        self._progress(
                            f"Bulk job {chunk_idx + 1}/{total_chunks}: {status} ({processed}/{total})",
                            20 + (chunk_idx * 60 // total_chunks) + int(percent * 0.6 / total_chunks),
                            100
                        )

                self.client.wait_for_bulk_completion(
                    bulk_id,
                    poll_interval=5,
                    max_wait=3600,
                    progress_callback=bulk_progress
                )

                # Fetch results
                self._progress(f"Downloading results for job {chunk_idx + 1}/{total_chunks}...", None, None)

                for result in self.client.fetch_bulk_results(bulk_id):
                    email = self._normalize_email(result['Email'])
                    results[email] = result

            except Exception as e:
                logger.error(f"Bulk validation failed for chunk {chunk_idx + 1}: {e}")
                # Mark chunk emails as errors (non-fatal)
                for email in chunk:
                    results[email] = {
                        'Email': email,
                        'Email_Validated': False,
                        'Email_Status': 'unknown',
                        'Email_Substatus': '',
                        'Email_Free': False,
                        'Email_Domain': '',
                        'Email_MX_Found': False,
                        'Email_Role': False,
                        'Email_Disposable': False,
                        'Email_AcceptAll': False,
                        'Email_Error': str(e),
                        'Email_Validated_At': datetime.utcnow().isoformat()
                    }

        return results

    def _validate_realtime(self, emails: List[str]) -> Dict[str, Dict]:
        """Validate emails using real-time API."""
        results = {}
        total = len(emails)

        for idx, email in enumerate(emails):
            if self.cancelled:
                break

            self._progress(f"Validating {idx + 1}/{total}...", 20 + (idx * 70 // total), 100)

            try:
                result = self.client.validate_email(email)
                results[email] = result
            except Exception as e:
                logger.error(f"Real-time validation failed for {email}: {e}")
                results[email] = {
                    'Email': email,
                    'Email_Validated': False,
                    'Email_Status': 'unknown',
                    'Email_Substatus': '',
                    'Email_Free': False,
                    'Email_Domain': '',
                    'Email_MX_Found': False,
                    'Email_Role': False,
                    'Email_Disposable': False,
                    'Email_AcceptAll': False,
                    'Email_Error': str(e),
                    'Email_Validated_At': datetime.utcnow().isoformat()
                }

        return results

    def _build_validation_sheet(self, email_occurrences: Dict[str, List[Tuple]]) -> pd.DataFrame:
        """
        Build EMAIL_VALIDATION dataframe with traceability.

        Args:
            email_occurrences: Dict[email, List[(sheet_name, row_index, status)]]

        Returns:
            DataFrame with EMAIL_VALIDATION content
        """
        rows = []

        for email, occurrences in email_occurrences.items():
            # Get validation result from cache
            if email in self.cache:
                validation = self.cache[email]
            else:
                # Email not validated (format error or cancelled)
                validation = {
                    'Email_Validated': False,
                    'Email_Status': 'unknown',
                    'Email_Substatus': '',
                    'Email_Free': False,
                    'Email_Domain': '',
                    'Email_MX_Found': False,
                    'Email_Role': False,
                    'Email_Disposable': False,
                    'Email_AcceptAll': False,
                    'Email_Error': 'Not validated',
                    'Email_Validated_At': datetime.utcnow().isoformat()
                }

            # Create row for each occurrence
            for sheet_name, row_index, status in occurrences:
                if status == 'invalid_format':
                    row = {
                        'SourceSheet': sheet_name,
                        'SourceRowIndex': row_index,
                        'Email': email,
                        'Email_Validated': False,
                        'Email_Status': 'invalid_format',
                        'Email_Substatus': '',
                        'Email_Free': False,
                        'Email_Domain': '',
                        'Email_MX_Found': False,
                        'Email_Role': False,
                        'Email_Disposable': False,
                        'Email_AcceptAll': False,
                        'Email_Error': 'Invalid email format',
                        'Email_Validated_At': datetime.utcnow().isoformat()
                    }
                else:
                    row = {
                        'SourceSheet': sheet_name,
                        'SourceRowIndex': row_index,
                        'Email': email,
                        'Email_Validated': validation['Email_Validated'],
                        'Email_Status': validation['Email_Status'],
                        'Email_Substatus': validation['Email_Substatus'],
                        'Email_Free': validation['Email_Free'],
                        'Email_Domain': validation['Email_Domain'],
                        'Email_MX_Found': validation['Email_MX_Found'],
                        'Email_Role': validation['Email_Role'],
                        'Email_Disposable': validation['Email_Disposable'],
                        'Email_AcceptAll': validation['Email_AcceptAll'],
                        'Email_Error': validation['Email_Error'],
                        'Email_Validated_At': validation['Email_Validated_At']
                    }

                rows.append(row)

        df = pd.DataFrame(rows)

        # Ensure column order
        column_order = [
            'SourceSheet', 'SourceRowIndex', 'Email', 'Email_Validated',
            'Email_Status', 'Email_Substatus', 'Email_Free', 'Email_Domain',
            'Email_MX_Found', 'Email_Role', 'Email_Disposable', 'Email_AcceptAll',
            'Email_Error', 'Email_Validated_At'
        ]

        df = df[column_order]

        return df

    def _compute_summary(self, df: pd.DataFrame) -> Dict:
        """Compute validation summary statistics."""
        total_occurrences = len(df)
        unique_emails = df['Email'].nunique()

        # Count by status
        status_counts = df['Email_Status'].value_counts().to_dict()

        deliverable = status_counts.get('deliverable', 0)
        risky = status_counts.get('risky', 0)
        undeliverable = status_counts.get('undeliverable', 0)
        unknown = status_counts.get('unknown', 0) + status_counts.get('invalid_format', 0)

        # Bad = risky + undeliverable (as per requirements)
        bad = risky + undeliverable

        return {
            'total_occurrences': total_occurrences,
            'unique_emails': unique_emails,
            'deliverable': deliverable,
            'risky': risky,
            'undeliverable': undeliverable,
            'unknown': unknown,
            'bad': bad
        }

    def _empty_summary(self) -> Dict:
        """Return empty summary."""
        return {
            'total_occurrences': 0,
            'unique_emails': 0,
            'deliverable': 0,
            'risky': 0,
            'undeliverable': 0,
            'unknown': 0,
            'bad': 0
        }

    def _normalize_email(self, email: str) -> str:
        """Normalize email address (strip, lowercase)."""
        if not email or not isinstance(email, str):
            return ''
        return email.strip().lower()

    def _is_valid_email_format(self, email: str) -> bool:
        """Basic email format validation using regex."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _progress(self, message: str, current: Optional[int], total: Optional[int]):
        """Report progress to callback."""
        if self.progress_callback:
            try:
                self.progress_callback(message, current, total)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")

    def _complete(self, success: bool, result_or_error):
        """Report completion to callback."""
        if self.completion_callback:
            try:
                self.completion_callback(success, result_or_error)
            except Exception as e:
                logger.error(f"Completion callback failed: {e}")
