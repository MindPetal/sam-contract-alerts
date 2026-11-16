"""
Build MS Teams Adaptive Card content and post it to a Teams webhook.

Each chat destination gets its own module with the same interface:
format_results(results) -> payload items, and post(webhook_url, items).
"""

import logging
from datetime import date

import client
from client.rest import ApiException

log = logging.getLogger(__name__)


def build_textblock(content: str) -> dict:
    """
    Build TextBlock for MS Teams
    """
    return {"type": "TextBlock", "text": content, "wrap": True}


def build_row(content: str, stripe_index: int) -> dict:
    """
    Build a striped single-cell TableRow
    """
    return {
        "type": "TableRow",
        "style": "emphasis" if stripe_index % 2 else "default",
        "cells": [
            {"type": "TableCell", "items": [build_textblock(content)]},
        ],
    }


def build_detail_content(detail: dict) -> str:
    """
    Build the pipe-delimited content string for one contract detail
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

    fields = [
        f"{company_text}",
        f"{detail['date']}",
        f"[{detail['piid']}]({contract_url})",
        f"{detail['action']}",
        f"**To Date:** {detail['total_obligated']}",
        f"**TCV:** {detail['total_value']}",
        f"**Start:** {detail['pop_start']}",
        f"**End:** {detail['pop_end_date']}",
        f"**Contract End:** {detail['contract_end_date']}",
        f"{desc}",
    ]

    if detail.get("competition"):
        fields.append(f"{detail['competition']}")

    return " | ".join(fields)


def build_details_table(heading: str, details: list[dict]) -> dict:
    """
    Build a striped single-column table with the heading as a header row and
    one row per contract detail
    """
    header_row = {
        "type": "TableRow",
        "style": "accent",
        "cells": [
            {"type": "TableCell", "items": [build_textblock(heading)]},
        ],
    }
    return {
        "type": "Table",
        "columns": [{"width": 1}],
        "firstRowAsHeaders": True,
        "gridStyle": "default",
        "rows": [header_row]
        + [
            build_row(build_detail_content(detail), i)
            for i, detail in enumerate(details)
        ],
    }


def format_results(raw_results: list[dict]) -> list:
    """
    Format results strings
    """
    items = []

    if raw_results:
        header = f"**{date.today().strftime('%A, %m/%d/%Y')}.** Contract updates."
        items += [build_textblock(header), build_textblock("")]

        for result in raw_results:
            if "contract_no" in result:
                heading = f"**{result['contract_nm']}** - {result['contract_no']}:"
            elif "agency" in result:
                heading = f"**{result['agency']}** updates:"

            items.append(build_details_table(heading, result["contract_details"]))
            items.append(build_textblock(""))

    return items


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


def post(webhook_url: str, items: list[dict]) -> None:
    """
    Execute MS Teams post
    """
    api_config = client.Configuration()
    api_config.host = webhook_url
    api_instance = client.MsApi(client.ApiClient(api_config))

    try:
        api_instance.teams_post(
            body={
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "version": "1.5",
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
