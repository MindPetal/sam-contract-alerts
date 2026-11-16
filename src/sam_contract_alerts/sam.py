"""
Call the SAM.gov contract awards search API.
"""

import logging
import time

import client
from client.rest import ApiException

log = logging.getLogger(__name__)


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

    try:
        if "contract_no" in criteria:
            search_params = {}
            if criteria.get("idv_no"):
                # PIIDs are only unique within their parent IDV
                search_params["referenced_idv_piid"] = criteria["idv_no"]

            api_response = api_instance.search(
                api_key=api_key,
                piid=criteria["contract_no"],
                date_signed=yday,
                limit=10,
                offset=0,
                **search_params,
            )
        elif "parent_contract_no" in criteria:
            # Search for child awards under an IDV
            api_response = api_instance.search(
                api_key=api_key,
                referenced_idv_piid=criteria["parent_contract_no"],
                date_signed=yday,
                limit=10,
                offset=0,
            )
        elif "naics" in criteria:
            api_response = api_instance.search(
                api_key=api_key,
                naics_code=criteria["naics"],
                contracting_subtier_name=criteria["agency"],
                date_signed=yday,
                limit=20,
                offset=0,
            )
    except ApiException as e:
        log.exception("Exception when calling SamApi->search: %s\n" % e)
        raise

    time.sleep(4)

    if api_response is None:
        log.info("API response is None")
        return []

    response_dict = api_response.to_dict()
    results = response_dict.get("award_summary") or []
    log.info("API response count: %d (date: %s)", len(results), yday)
    return results
