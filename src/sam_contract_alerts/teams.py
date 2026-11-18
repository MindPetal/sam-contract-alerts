"""
Build MS Teams Adaptive Card content and post it to a Teams webhook.

Each chat destination gets its own module with the same interface:
format_results(results) -> payload items, and post(webhook_url, items).
"""

import logging

import client
from client.rest import ApiException
from sam_contract_alerts import results

log = logging.getLogger(__name__)


def build_textblock(content: str) -> dict:
    """
    Build TextBlock for MS Teams
    """
    return {"type": "TextBlock", "text": content, "wrap": True}


def build_row(lines: list[str], stripe_index: int) -> dict:
    """
    Build a striped single-cell TableRow with one TextBlock per line, so each
    line starts on its own row without extra paragraph spacing
    """
    items = [build_textblock(line) for line in lines]

    for item in items[1:]:
        item["spacing"] = "None"

    return {
        "type": "TableRow",
        "style": "emphasis" if stripe_index % 2 else "default",
        "cells": [{"type": "TableCell", "items": items}],
    }


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
            build_row(results.build_detail_lines(detail), i)
            for i, detail in enumerate(details)
        ],
    }


def format_results(raw_results: list[dict]) -> list:
    """
    Format results strings
    """
    items = []

    if raw_results:
        items += [build_textblock(results.header_text()), build_textblock("")]

        for result in raw_results:
            heading = results.result_heading(result)
            items.append(build_details_table(heading, result["contract_details"]))
            items.append(build_textblock(""))

    return items


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
