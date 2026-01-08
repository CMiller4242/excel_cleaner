"""
Emailable API Client for email validation.

Supports both real-time and bulk validation with robust error handling,
retry logic, and response normalization.
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Iterator
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailableError(Exception):
    """Base exception for Emailable API errors."""
    pass


class EmailableAuthError(EmailableError):
    """Authentication/API key error."""
    pass


class EmailableRateLimitError(EmailableError):
    """Rate limit exceeded."""
    pass


class EmailableClient:
    """
    Client for Emailable email validation API.

    Provides real-time and bulk validation with automatic retry,
    timeout handling, and response normalization.
    """

    DEFAULT_BASE_URL = "https://api.emailable.com/v1"
    DEFAULT_TIMEOUT = (10, 30)  # (connect, read) in seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # seconds

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize Emailable client.

        Args:
            api_key: Emailable API key
            base_url: Optional custom base URL (for testing)
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST requests
            retry_count: Current retry attempt

        Returns:
            Response JSON as dict

        Raises:
            EmailableAuthError: Authentication failed
            EmailableRateLimitError: Rate limit exceeded
            EmailableError: Other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key

        try:
            logger.debug(f"Making {method} request to {endpoint}")

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.DEFAULT_TIMEOUT
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise EmailableAuthError("Invalid API key or authentication failed")
            elif response.status_code == 429:
                # Rate limit - retry with backoff
                if retry_count < self.MAX_RETRIES:
                    wait_time = self.RETRY_BACKOFF_BASE ** (retry_count + 1)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {retry_count + 1}/{self.MAX_RETRIES}")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, params, json_data, retry_count + 1)
                else:
                    raise EmailableRateLimitError("Rate limit exceeded, max retries reached")
            elif response.status_code >= 500:
                # Server error - retry
                if retry_count < self.MAX_RETRIES:
                    wait_time = self.RETRY_BACKOFF_BASE ** (retry_count + 1)
                    logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, params, json_data, retry_count + 1)
                else:
                    raise EmailableError(f"Server error {response.status_code}, max retries reached")
            elif not response.ok:
                raise EmailableError(f"API error {response.status_code}: {response.text}")

            return response.json()

        except requests.exceptions.Timeout:
            if retry_count < self.MAX_RETRIES:
                wait_time = self.RETRY_BACKOFF_BASE ** (retry_count + 1)
                logger.warning(f"Request timeout, retrying in {wait_time}s")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, json_data, retry_count + 1)
            else:
                raise EmailableError("Request timeout, max retries reached")
        except requests.exceptions.RequestException as e:
            if retry_count < self.MAX_RETRIES:
                wait_time = self.RETRY_BACKOFF_BASE ** (retry_count + 1)
                logger.warning(f"Request failed: {e}, retrying in {wait_time}s")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, json_data, retry_count + 1)
            else:
                raise EmailableError(f"Request failed: {e}")

    def validate_email(self, email: str) -> Dict:
        """
        Validate a single email in real-time.

        Args:
            email: Email address to validate

        Returns:
            Normalized validation result dict
        """
        response = self._make_request('GET', '/verify', params={'email': email})
        return self._normalize_result(response)

    def test_connection(self) -> bool:
        """
        Test API connection and key validity.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Use account endpoint to verify API key
            self._make_request('GET', '/account')
            return True
        except EmailableAuthError:
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def create_bulk(self, emails: List[str], metadata: Optional[Dict] = None) -> str:
        """
        Create a bulk validation job.

        Args:
            emails: List of email addresses to validate
            metadata: Optional metadata to attach to job

        Returns:
            Bulk job ID
        """
        payload = {
            'emails': emails
        }
        if metadata:
            payload['metadata'] = metadata

        response = self._make_request('POST', '/batch', json_data=payload)

        if 'id' not in response:
            raise EmailableError("Bulk job creation failed: no ID returned")

        return response['id']

    def get_bulk_status(self, bulk_id: str) -> Dict:
        """
        Get status of a bulk validation job.

        Args:
            bulk_id: Bulk job ID

        Returns:
            Status dict with keys: id, status, total, processed, reason_counts
        """
        response = self._make_request('GET', f'/batch/{bulk_id}')
        return response

    def fetch_bulk_results(self, bulk_id: str, chunk_size: int = 1000) -> Iterator[Dict]:
        """
        Fetch results from a completed bulk validation job.

        Args:
            bulk_id: Bulk job ID
            chunk_size: Number of results to fetch per request

        Yields:
            Normalized validation result dicts
        """
        offset = 0

        while True:
            params = {
                'offset': offset,
                'limit': chunk_size
            }

            response = self._make_request('GET', f'/batch/{bulk_id}/emails', params=params)

            # Emailable returns emails array
            emails = response.get('emails', [])
            if not emails:
                break

            for result in emails:
                yield self._normalize_result(result)

            # Check if we've fetched all results
            if len(emails) < chunk_size:
                break

            offset += chunk_size

    def wait_for_bulk_completion(
        self,
        bulk_id: str,
        poll_interval: int = 5,
        max_wait: int = 3600,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Poll bulk job until completion or timeout.

        Args:
            bulk_id: Bulk job ID
            poll_interval: Seconds between polls
            max_wait: Maximum seconds to wait
            progress_callback: Optional callback(total, processed, status)

        Returns:
            Final status dict

        Raises:
            EmailableError: If job fails or times out
        """
        start_time = time.time()

        while True:
            status = self.get_bulk_status(bulk_id)

            state = status.get('status', 'unknown')
            total = status.get('total', 0)
            processed = status.get('processed', 0)

            if progress_callback:
                progress_callback(total, processed, state)

            if state in ('completed', 'success'):
                logger.info(f"Bulk job {bulk_id} completed successfully")
                return status
            elif state in ('failed', 'error'):
                reason = status.get('message', 'Unknown error')
                raise EmailableError(f"Bulk job failed: {reason}")

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise EmailableError(f"Bulk job timed out after {max_wait}s")

            # Wait before next poll
            time.sleep(poll_interval)

    def _normalize_result(self, raw_result: Dict) -> Dict:
        """
        Normalize Emailable API response to consistent format.

        Args:
            raw_result: Raw API response dict

        Returns:
            Normalized dict with standard keys
        """
        # Extract email
        email = raw_result.get('email', '')

        # Extract state (deliverable, undeliverable, risky, unknown)
        state = raw_result.get('state', 'unknown').lower()

        # Map to our status
        if state == 'deliverable':
            status = 'deliverable'
        elif state == 'undeliverable':
            status = 'undeliverable'
        elif state == 'risky':
            status = 'risky'
        else:
            status = 'unknown'

        # Extract detailed fields
        normalized = {
            'Email': email,
            'Email_Validated': state in ('deliverable', 'undeliverable', 'risky'),
            'Email_Status': status,
            'Email_Substatus': raw_result.get('reason', ''),
            'Email_Free': raw_result.get('free', False),
            'Email_Domain': raw_result.get('domain', ''),
            'Email_MX_Found': raw_result.get('mx_found', False),
            'Email_Role': raw_result.get('role', False),
            'Email_Disposable': raw_result.get('disposable', False),
            'Email_AcceptAll': raw_result.get('accept_all', False),
            'Email_Error': raw_result.get('error', '') if not raw_result.get('state') else '',
            'Email_Validated_At': datetime.utcnow().isoformat()
        }

        # Log any unexpected fields for debugging
        expected_keys = {
            'email', 'state', 'reason', 'free', 'domain', 'mx_found',
            'role', 'disposable', 'accept_all', 'error', 'tag', 'did_you_mean'
        }
        unexpected = set(raw_result.keys()) - expected_keys
        if unexpected:
            logger.debug(f"Unexpected fields in response: {unexpected}")

        return normalized

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
