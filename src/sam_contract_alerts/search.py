"""
Run the contract and NAICS searches, dedupe the results, and post them to the
chat channel.
"""

import logging
from collections.abc import Iterable
from datetime import datetime, timedelta

import client
from sam_contract_alerts import results, sam, teams
from sam_contract_alerts.config import ContractEntry, NaicsEntry, Settings

log = logging.getLogger(__name__)


def search_contracts(
    api_client: client.ApiClient,
    sam_api_key: str,
    contracts: Iterable[ContractEntry],
    yday: str,
) -> list:
    """Process contract number searches and return results."""
    contract_results = []

    for contract in contracts:
        log.info("Processing contract number search")

        contract_details = []

        if contract.type == "IDV":
            # Make API calls for parent and child awards
            log.info("Searching for IDV parent contract updates..")
            criteria = {"contract_no": contract.contract_no, "idv_no": contract.idv_no}
            parent_updates = sam.search(api_client, sam_api_key, yday, criteria)

            for update in parent_updates:
                contract_info = results.extract_contract_details(update, yday)
                contract_details.append(contract_info)

            log.info("Searching for child award updates under IDV..")
            criteria = {"parent_contract_no": contract.contract_no}
            child_updates = sam.search(api_client, sam_api_key, yday, criteria)

            for update in child_updates:
                contract_info = results.extract_contract_details(update, yday)
                contract_details.append(contract_info)

        elif contract.type == "AWARD":
            # Single award search
            log.info("Searching for contract updates..")
            criteria = {"contract_no": contract.contract_no, "idv_no": contract.idv_no}
            award_updates = sam.search(api_client, sam_api_key, yday, criteria)

            for update in award_updates:
                contract_info = results.extract_contract_details(update, yday)
                contract_details.append(contract_info)

        if contract_details:
            contract_results.append(
                {
                    "contract_no": contract.contract_no,
                    "contract_nm": contract.name,
                    "contract_details": contract_details,
                }
            )

    return contract_results


def search_naics(
    api_client: client.ApiClient,
    sam_api_key: str,
    naics_entries: Iterable[NaicsEntry],
    yday: str,
) -> list:
    """Process NAICS searches and return results grouped by agency."""
    naics_results = []

    for entry in naics_entries:
        contract_details = []

        for naics in entry.naics_codes:
            log.info("Processing NAICS search")
            criteria = {"naics": naics, "agency": entry.agency}
            contract_updates = sam.search(api_client, sam_api_key, yday, criteria)

            for update in contract_updates:
                contract_info = results.extract_contract_details(update, yday)
                contract_details.append(contract_info)

        if contract_details:
            naics_results.append(
                {
                    "agency": entry.abbr,
                    "contract_details": contract_details,
                }
            )

    return naics_results


def process_search(
    api_client: client.ApiClient,
    sam_api_key: str,
    contracts: Iterable[ContractEntry],
    naics_entries: Iterable[NaicsEntry],
    days: int = 1,
) -> list[dict]:
    """Run sam.gov searches and return deduped, indexed results."""
    yday = (datetime.now() - timedelta(days=days)).strftime("%m/%d/%Y")
    log.info("Searching for date: %s", yday)

    contract_results = search_contracts(api_client, sam_api_key, contracts, yday)
    naics_results = search_naics(api_client, sam_api_key, naics_entries, yday)

    raw_results = contract_results + naics_results

    if raw_results:
        # Dedupe contract details by piid
        seen_piids: set[str] = set()
        dedupe_results = []

        for result in raw_results:
            unique_details = []

            for detail in result["contract_details"]:
                piid = detail["piid"]

                if piid not in seen_piids:
                    seen_piids.add(piid)
                    unique_details.append(detail)

            if unique_details:
                result["contract_details"] = unique_details
                dedupe_results.append(result)

        raw_results = dedupe_results

        # Inject index into results
        n = 1

        for result in raw_results:
            result["index"] = n
            n += 1

    return raw_results


def main(settings: Settings) -> None:
    """
    Primary processing function
    """
    log.info("Start processing")
    api_config = client.Configuration()
    api_config.host = "https://api.sam.gov"
    api_client = client.ApiClient(api_config)

    log.info("Process search")
    contract_results = process_search(
        api_client,
        settings.sam_api_key,
        settings.contracts,
        settings.naics,
        settings.days,
    )

    if contract_results:
        log.info("Posting results")
        teams.post(settings.ms_webhook_url, teams.format_results(contract_results))
    else:
        log.info("No contract updates found")
