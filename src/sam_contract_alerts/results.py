"""
Turn SAM.gov award records into display fields and the Markdown text shared
by every chat channel.
"""

from datetime import date, datetime

from dateutil.relativedelta import relativedelta

# Awards whose period of performance started within this window count as new
NEW_AWARD_WINDOW = relativedelta(months=1)


def format_award_type(award_type: str) -> str:
    """
    Lowercase an all-caps award type.
    """
    words = []
    for word in award_type.split():
        if len(word) <= 3:
            words.append(word.upper())
        else:
            words.append(word.lower())
    return " ".join(words)


def format_competition(
    number_of_offers: str,
    extent_competed: str,
    type_of_set_aside: str,
) -> str:
    """
    Build the competition summary sentence.
    """
    parts = []

    if number_of_offers:
        try:
            count = int(number_of_offers)
        except (TypeError, ValueError):
            count = None
        if count is not None:
            noun = "offer" if count == 1 else "offers"
            parts.append(f"{count} {noun} received.")

    extent_clean = extent_competed.strip().rstrip(".").strip()
    set_aside_clean = type_of_set_aside.strip().rstrip(".").strip()

    # Only surface the extent of competition when it is "NOT COMPETED";
    descriptors = []
    if extent_clean.upper() == "NOT COMPETED":
        descriptors.append(extent_clean)
    if set_aside_clean:
        descriptors.append(set_aside_clean)

    if descriptors:
        sentence = ", ".join(descriptors).capitalize()
        parts.append(f"{sentence}.")

    return " ".join(parts)


def extract_contract_details(award_summary: dict, now: datetime | None = None) -> dict:
    """
    Extract contract details from award summary
    """
    contract_info = {}

    award_details = award_summary.get("award_details", {})

    dates = award_details.get("dates", {})
    date_signed = dates.get("date_signed", "")[:10]
    parsed_date = datetime.strptime(date_signed, "%Y-%m-%d")
    contract_info["date"] = parsed_date.strftime("%m/%d/%Y")

    awardee_data = award_details.get("awardee_data", {})
    awardee_header = awardee_data.get("awardee_header", {})
    contract_info["company"] = awardee_header.get("awardee_name", "")

    awardee_uei = awardee_data.get("awardee_uei_information", {}) or {}
    contract_info["unique_entity_id"] = awardee_uei.get("unique_entity_id", "")

    reason = award_summary.get("contract_id", {}).get("reason_for_modification") or {}
    reason_name = reason.get("name", "")
    contract_info["reason"] = reason_name.strip().capitalize() if reason_name else ""

    obligation = award_details.get("dollars", {}).get("action_obligation", "")
    if obligation != "" and obligation is not None:
        contract_info["obligation"] = f"${float(obligation):,.12g}"
    else:
        contract_info["obligation"] = ""

    core_data = award_summary.get("core_data", {}) or {}
    award_type = (core_data.get("award_or_idv_type", {}) or {}).get("name", "")
    award_type = format_award_type(award_type) if award_type else ""

    obligation_part = " ".join(
        part for part in [contract_info["obligation"], award_type] if part
    )
    if contract_info["reason"]:
        contract_info["action"] = f"{contract_info['reason']}: {obligation_part}"
    else:
        contract_info["action"] = obligation_part

    total_dollars = award_details.get("total_contract_dollars", {})
    total_obligated = total_dollars.get("total_base_and_exercised_options_value", "")
    contract_info["total_obligated"] = (
        f"${float(total_obligated):,.12g}" if total_obligated else ""
    )

    total_value = total_dollars.get("total_base_and_all_options_value", "")
    contract_info["total_value"] = f"${float(total_value):,.12g}" if total_value else ""

    pop_start = dates.get("period_of_performance_start_date", "")
    if pop_start:
        parsed_pop_start = datetime.strptime(pop_start[:10], "%Y-%m-%d")
        contract_info["pop_start"] = parsed_pop_start.strftime("%m/%d/%Y")
    else:
        parsed_pop_start = None
        contract_info["pop_start"] = ""

    product_service = award_details.get("product_or_service_information", {})
    contract_info["desc"] = product_service.get(
        "description_of_contract_requirement", ""
    )

    contract_info["piid"] = award_summary.get("contract_id", {}).get("piid", "")

    current_completion = dates.get("current_completion_date", "")
    if current_completion:
        parsed_pop = datetime.strptime(current_completion[:10], "%Y-%m-%d")
        contract_info["pop_end_date"] = parsed_pop.strftime("%m/%d/%Y")
    else:
        contract_info["pop_end_date"] = ""

    ultimate_completion = dates.get("ultimate_completion_date", "")
    if ultimate_completion:
        parsed_end = datetime.strptime(ultimate_completion[:10], "%Y-%m-%d")
        contract_info["contract_end_date"] = parsed_end.strftime("%m/%d/%Y")
    else:
        contract_info["contract_end_date"] = ""

    award_competition = award_details.get("competition_information", {}) or {}
    core_competition = core_data.get("competition_information", {}) or {}

    number_of_offers = award_competition.get("number_of_offers_received", "")
    extent_competed = (core_competition.get("extent_competed", {}) or {}).get(
        "name", ""
    )
    type_of_set_aside = (core_competition.get("type_of_set_aside", {}) or {}).get(
        "name", ""
    )

    # Only surface competition details for new awards: PoP start within the
    # past month, in the future, or unknown.
    cutoff = ((now or datetime.now()) - NEW_AWARD_WINDOW).date()
    if parsed_pop_start is not None and parsed_pop_start.date() < cutoff:
        contract_info["competition"] = ""
    else:
        contract_info["competition"] = format_competition(
            number_of_offers, extent_competed, type_of_set_aside
        )

    return contract_info


def header_text() -> str:
    """
    Message header shown above all contract updates
    """
    return f"**{date.today().strftime('%A, %m/%d/%Y')}.** Contract updates."


def result_heading(result: dict) -> str:
    """
    Heading for one tracked contract or NAICS agency group
    """
    if "contract_no" in result:
        return f"**{result['contract_nm']}** - {result['contract_no']}:"

    return f"**{result['agency']}** updates:"


def build_detail_lines(detail: dict) -> list[str]:
    """
    Build the display lines for one contract detail: awardee, date and contract
    no; amounts; dates; description; then competition when present. Blank parts
    and lines are left out.
    """
    desc = detail["desc"].replace("|!#^", " ").replace("\n", " ")
    desc = " ".join(desc.split())
    contract_url = build_search_url(detail["piid"])
    unique_entity_id = detail.get("unique_entity_id", "")

    if unique_entity_id and detail["company"]:
        entity_url = build_entity_url(unique_entity_id)
        company_text = f"[{detail['company']}]({entity_url})"
    else:
        company_text = detail["company"]

    lines = [
        [company_text, detail["date"], f"[{detail['piid']}]({contract_url})"],
        [
            detail["action"],
            f"**To Date:** {detail['total_obligated']}",
            f"**TCV:** {detail['total_value']}",
        ],
        [
            f"**Contract Start:** {detail['pop_start']}",
            f"**PoP End:** {detail['pop_end_date']}",
            f"**Contract End:** {detail['contract_end_date']}",
        ],
        [desc],
        [detail.get("competition", "")],
    ]

    joined = (" | ".join(part for part in line if part) for line in lines)
    return [line for line in joined if line]


def build_detail_content(detail: dict) -> str:
    """
    Build the content for one contract detail, one line per newline
    """
    return "\n".join(build_detail_lines(detail))


def build_search_url(piid: str) -> str:
    """
    Build SAM.gov search URL for viewing contracts
    """

    return (
        f"https://sam.gov/search/?sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bkey%5D={piid}"
        f"&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bvalue%5D={piid}"
    )


def build_entity_url(unique_entity_id: str) -> str:
    """
    Build SAM.gov entity URL for viewing an awardee's core data
    """

    return f"https://sam.gov/entities/view/{unique_entity_id}/coreData?status=Active"
