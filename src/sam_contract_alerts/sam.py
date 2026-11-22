"""
Call the SAM.gov contract awards search API.
"""

import logging
import random
import time
from collections.abc import Callable
from http import HTTPStatus

import urllib3

import client
from client.rest import ApiException

log = logging.getLogger(__name__)

# Retry transient SAM.gov failures.
RETRY_DELAYS = (10, 30)
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER = 120

# Seconds to connect, and to wait for a response, on each attempt
REQUEST_TIMEOUT = (10, 90)


class SamSearchError(Exception):
    """
    A SAM.gov search failed. reason is the HTTP reason phrase, or None when
    there was no HTTP response (e.g. a timeout).
    """

    def __init__(self, message: str, status: int | str, reason: str | None = None):
        super().__init__(message)
        self.status = status
        self.reason = reason


def http_reason(error: Exception) -> str | None:
    """
    Reason phrase of an HTTP error response. Only the status and reason are
    kept since the rest of the error can include the request URL and API key.
    """
    if not isinstance(error, ApiException) or not error.status:
        return None

    if error.reason:
        return error.reason

    try:
        return HTTPStatus(error.status).phrase
    except ValueError:
        return "Unknown error"


def describe(criteria: dict) -> str:
    """
    Kind of search, for log messages.
    """
    if "contract_no" in criteria:
        return "contract"
    if "parent_contract_no" in criteria:
        return "IDV child awards"
    return "NAICS"


def retry_delay(error: Exception, retry: int) -> float | None:
    """
    Seconds to wait before retrying, or None if the error isn't transient
    """
    if isinstance(error, ApiException):
        if error.status not in RETRY_STATUSES:
            return None

        retry_after = (error.headers or {}).get("Retry-After", "")
        if error.status == 429 and str(retry_after).isdigit():
            return min(int(retry_after), MAX_RETRY_AFTER)

    return RETRY_DELAYS[retry] + random.uniform(0, 3)


def call_with_retry(request: Callable, criteria: dict):
    """
    Run a SAM.gov request, retrying transient failures with backoff. Raises
    SamSearchError once the retries are used up.
    """
    attempts = len(RETRY_DELAYS) + 1

    for attempt in range(1, attempts + 1):
        try:
            return request()
        except (ApiException, urllib3.exceptions.HTTPError) as e:
            delay = retry_delay(e, attempt - 1) if attempt < attempts else None
            status = getattr(e, "status", None) or type(e).__name__

            if delay is None:
                message = (
                    f"SAM.gov search for {describe(criteria)} failed ({status}),"
                    f" attempt {attempt} of {attempts}"
                )
                log.error(message)
                # "from None" keeps the original error, which includes the
                # request URL, out of the traceback
                raise SamSearchError(message, status, http_reason(e)) from None

            log.warning(
                "SAM.gov search for %s failed (%s), attempt %d of %d."
                " Retrying in %.0fs",
                describe(criteria),
                status,
                attempt,
                attempts,
                delay,
            )
            time.sleep(delay)


def search(
    api_client: client.ApiClient,
    api_key: str,
    yday: str,
    criteria: dict,
) -> list[dict]:
    """
    Execute sam.gov contract awards search
    """
    api_instance = client.SamApi(api_client)

    def request():
        if "contract_no" in criteria:
            search_params = {}
            if criteria.get("idv_no"):
                # PIIDs are only unique within their parent IDV
                search_params["referenced_idv_piid"] = criteria["idv_no"]

            return api_instance.search(
                api_key=api_key,
                piid=criteria["contract_no"],
                date_signed=yday,
                limit=10,
                offset=0,
                _request_timeout=REQUEST_TIMEOUT,
                **search_params,
            )
        elif "parent_contract_no" in criteria:
            # Search for child awards under an IDV
            return api_instance.search(
                api_key=api_key,
                referenced_idv_piid=criteria["parent_contract_no"],
                date_signed=yday,
                limit=10,
                offset=0,
                _request_timeout=REQUEST_TIMEOUT,
            )
        elif "naics" in criteria:
            # Several NAICS codes can be searched at once, separated by "~"
            return api_instance.search(
                api_key=api_key,
                naics_code=criteria["naics"],
                contracting_subtier_name=criteria["agency"],
                date_signed=yday,
                limit=100,
                offset=0,
                _request_timeout=REQUEST_TIMEOUT,
            )

        raise ValueError(f"Unknown search criteria: {sorted(criteria)}")

    api_response = call_with_retry(request, criteria)

    time.sleep(4)

    if api_response is None:
        log.info("API response is None")
        return []

    response_dict = api_response.to_dict()
    results = response_dict.get("award_summary") or []
    log.info("API response count: %d (date: %s)", len(results), yday)
    return results
