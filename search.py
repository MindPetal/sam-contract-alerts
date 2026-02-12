"""
Script executes via github actions to call sam.gov contract awards
API and post results to MS Teams.
"""

import logging
import sys
import time
from datetime import date, datetime, timedelta

import client
from client.rest import ApiException

log = logging.getLogger("search")
logging.basicConfig(level=logging.INFO)


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
            api_response = api_instance.search(
                api_key=api_key,
                piid=criteria["contract_no"],
                date_signed=yday,
                limit=10,
                offset=0,
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
        return []
    
    response_dict = api_response.to_dict()
    return response_dict.get("award_summary") or []


def build_textblock(content: str) -> dict:
    """
    Build TextBlock for MS Teams
    """
    return {"type": "TextBlock", "text": content, "wrap": True}


def extract_contract_details(award_summary: dict) -> dict:
    """
    Extract contract details from award summary
    """
    contract_info = {}

    award_details = award_summary.get("award_details", {})

    dates = award_details.get("dates", {})
    date_signed = dates.get("date_signed", "").split("T")[0]
    parsed_date = datetime.strptime(date_signed, "%Y-%m-%d")
    contract_info["date"] = parsed_date.strftime("%B %d, %Y")

    awardee_data = award_details.get("awardee_data", {}).get("awardee_header", {})
    contract_info["company"] = awardee_data.get("awardee_name", "")

    reason = award_summary.get("contract_id", {}).get("reason_for_modification") or {}
    contract_info["reason"] = reason.get("name", "")

    obligation = award_details.get("dollars", {}).get("action_obligation", "")
    contract_info["obligation"] = f"${float(obligation):,.12g}" if obligation else ""

    total_dollars = award_details.get("total_contract_dollars", {})
    total_value = total_dollars.get("total_base_and_all_options_value", "")
    contract_info["total_value"] = f"${float(total_value):,.12g}" if total_value else ""

    product_service = award_details.get("product_or_service_information", {})
    contract_info["desc"] = product_service.get("description_of_contract_requirement", "")

    contract_info["piid"] = award_summary.get("contract_id", {}).get("piid", "")

    return contract_info


def format_results(raw_results: list[dict]) -> list:
    """
    Format results strings
    """
    items = []

    if raw_results:
        header = f'**{date.today().strftime("%A, %m/%d/%Y")}.** Contract updates.'
        items += [build_textblock(header), build_textblock("")]

        for result in raw_results:
            if "contract_no" in result:
                content = (
                    f'**{result["index"]}. {result["contract_nm"]}** - '
                    f'{result["contract_no"]}'
                )
            elif "naics" in result:
                agency = result["agency"]
                content = (
                    f'**{result["index"]}. {agency}** - '
                    f'NAICS {result["naics"]} updates'
                )

            for detail in result["contract_details"]:
                desc = detail["desc"].replace("|!#^", " ").replace("\n", " ")
                desc = " ".join(desc.split())
                contract_url = build_search_url(detail["piid"])
                content += (
                    f'\n\n- **Contract:** [{detail["piid"]}]({contract_url}) | '
                    f'**Date Signed:** {detail["date"]} | **Company:** '
                    f'{detail["company"]} | '
                    f'**Reason:** {detail["reason"]} | '
                    f'**Obligation:** {detail["obligation"]} | '
                    f'**Total Value:** {detail["total_value"]} | '
                    f"**Description:** {desc}"
                )

            items += [build_textblock(content), build_textblock("")]

    return items


def build_search_url(piid: str) -> str:
    """
    Build SAM.gov search URL for viewing contracts
    """

    return (
        f"https://sam.gov/search/?sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bkey%5D={piid}"
        f"&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bvalue%5D={piid}"
    )


def search_contracts(
    api_client: client.ApiClient,
    sam_api_key: str,
    contract_list: str,
    yday: str,
) -> list:
    """Process contract number searches and return results."""
    results = []

    if not contract_list:
        return results

    contract_triplets = contract_list.split(",")

    for triplet in contract_triplets:
        log.info("Processing contract number search")

        contract_no, contract_nm, contract_type = triplet.split(":")
        contract_no = contract_no.strip()
        contract_nm = contract_nm.strip()
        contract_type = contract_type.strip()

        contract_details = []

        if contract_type == "IDV":
            # Make API calls for parent and child awards
            log.info("Searching for IDV parent contract updates..")
            criteria = {"contract_no": contract_no}
            parent_updates = search(api_client, sam_api_key, yday, criteria)

            for update in parent_updates:
                contract_info = extract_contract_details(update)
                contract_details.append(contract_info)

            log.info("Searching for child award updates under IDV..")
            criteria = {"parent_contract_no": contract_no}
            child_updates = search(api_client, sam_api_key, yday, criteria)

            for update in child_updates:
                contract_info = extract_contract_details(update)
                contract_details.append(contract_info)

        elif contract_type == "AWARD":
            # Single award search
            log.info("Searching for contract updates..")
            criteria = {"contract_no": contract_no}
            award_updates = search(api_client, sam_api_key, yday, criteria)

            for update in award_updates:
                contract_info = extract_contract_details(update)
                contract_details.append(contract_info)

        if contract_details:
            results.append(
                {
                    "contract_no": contract_no,
                    "contract_nm": contract_nm,
                    "contract_details": contract_details,
                }
            )

    return results


def search_naics(
    api_client: client.ApiClient,
    sam_api_key: str,
    naics_list: str,
    yday: str,
) -> list:
    """Process NAICS searches and return results."""
    results = []

    if not naics_list:
        return results

    naics_triplets = naics_list.split(",")

    for triplet in naics_triplets:
        log.info("Processing NAICS search")

        naics, agency, abbr = triplet.split(":")
        naics = naics.strip()
        agency = agency.strip()
        abbr = abbr.strip()
        criteria = {"naics": naics, "agency": agency}
        contract_updates = search(api_client, sam_api_key, yday, criteria)

        if contract_updates:
            contract_details = []

            for update in contract_updates:
                contract_info = extract_contract_details(update)
                contract_details.append(contract_info)

            results.append(
                {
                    "naics": naics,
                    "agency": abbr,
                    "contract_details": contract_details,
                }
            )

    return results


def process_search(
    api_client: client.ApiClient, sam_api_key: str, contract_list: str, naics_list: str
) -> list:
    """Prepare sam.gov search and format results."""
    yday = (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y")

    contract_results = search_contracts(api_client, sam_api_key, contract_list, yday)
    naics_results = search_naics(api_client, sam_api_key, naics_list, yday)

    raw_results = contract_results + naics_results

    if raw_results:
        # Inject index into results
        n = 1

        for result in raw_results:
            result["index"] = n
            n += 1

    return format_results(raw_results)


def teams_post(api_client: client.ApiClient, items: list[dict]) -> None:
    """
    Execute MS Teams post
    """
    api_instance = client.MsApi(api_client)

    try:
        api_instance.teams_post(
            body={
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "version": "1.0",
                            "body": [{"type": "Container", "items": items}],
                            "msteams": {"width": "Full"},
                        },
                    }
                ],
            }
        )

    except ApiException as e:
        log.exception("Exception when calling MsApi->teams_post: %s\n" % e)
        raise


def main(
    sam_api_key: str, contract_list: str, naics_list: str, ms_webhook_url: str
) -> None:
    """
    Primary processing function
    """
    log.info("Start processing")
    api_config = client.Configuration()
    api_config.host = "https://api.sam.gov"
    api_client = client.ApiClient(api_config)

    log.info("Process search")
    contract_results = process_search(
        api_client, sam_api_key, contract_list, naics_list
    )

    if contract_results:
        log.info("Process Teams posts")
        api_config.host = ms_webhook_url
        teams_post(api_client, contract_results)
    else:
        log.info("No contract updates found")


""" Read in sam_api_key, contract_list, naics_list, ms_webhook_url
"""
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
