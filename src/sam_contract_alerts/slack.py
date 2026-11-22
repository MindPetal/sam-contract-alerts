"""
Build Slack Block Kit messages and post them to a Slack incoming webhook.

Each chat destination gets its own module with the same interface:
format_results(results) and format_sam_error(status, message) -> payload
items, and post(webhook_url, items).
"""

import re
import time

import certifi
import urllib3

from sam_contract_alerts import results

# Slack limits per message: 50 blocks, 12,000 characters across all markdown
# blocks, and 10,000 characters across all table cells. Tables also allow at
# most 100 rows.
MAX_BLOCKS = 50
MAX_MARKDOWN_CHARS = 12_000
MAX_TABLE_CHARS = 10_000
MAX_TABLE_ROWS = 100

# One table per message is always accepted. Raise this to group several
# contract tables into one message if your workspace allows it.
MAX_TABLES_PER_MESSAGE = 1

# **bold** or [text](url) in the shared Markdown text
MARKDOWN_TOKEN = re.compile(r"\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)\s]+)\)")


class SlackPostError(Exception):
    pass


def build_markdown(text: str) -> dict:
    """
    Build a markdown block, which renders standard Markdown (**bold**,
    [text](url))
    """
    if len(text) > MAX_MARKDOWN_CHARS:
        text = text[: MAX_MARKDOWN_CHARS - 1] + "…"

    return {"type": "markdown", "text": text}


def build_cell(markdown: str) -> dict:
    """
    Build a rich text table cell from Markdown, keeping **bold** and
    [text](url) links
    """
    elements: list[dict] = []
    position = 0

    for match in MARKDOWN_TOKEN.finditer(markdown):
        if match.start() > position:
            elements.append(
                {"type": "text", "text": markdown[position : match.start()]}
            )

        bold, link_text, url = match.groups()

        if bold is not None:
            elements.append({"type": "text", "text": bold, "style": {"bold": True}})
        else:
            elements.append({"type": "link", "text": link_text, "url": url})

        position = match.end()

    if position < len(markdown) or not elements:
        elements.append({"type": "text", "text": markdown[position:] or " "})

    return {
        "type": "rich_text",
        "elements": [{"type": "rich_text_section", "elements": elements}],
    }


def cell_chars(cell: dict) -> int:
    """
    Characters a cell counts toward Slack's table limit. Link URLs are
    included to stay on the safe side.
    """
    return sum(
        len(element.get("text", "")) + len(element.get("url", ""))
        for section in cell["elements"]
        for element in section["elements"]
    )


def table_chars(table: dict) -> int:
    return sum(cell_chars(row[0]) for row in table["rows"])


def build_tables(heading: str, contents: list[str]) -> list[dict]:
    """
    Build a single-column table with the heading as the first row and one
    wrapped row per contract detail. Splits into continuation tables to stay
    within Slack's table limits.
    """
    tables = []
    header = [build_cell(heading)]
    rows = [header]
    chars = cell_chars(header[0])

    for content in contents:
        row = [build_cell(content)]
        size = cell_chars(row[0])

        if len(rows) > 1 and (
            len(rows) >= MAX_TABLE_ROWS or chars + size > MAX_TABLE_CHARS
        ):
            tables.append(rows)
            header = [build_cell(f"{heading} (continued)")]
            rows = [header]
            chars = cell_chars(header[0])

        rows.append(row)
        chars += size

    tables.append(rows)

    return [
        {"type": "table", "column_settings": [{"is_wrapped": True}], "rows": rows}
        for rows in tables
    ]


def format_results(raw_results: list[dict]) -> list[dict]:
    """
    Format results as the header, then one table per contract or agency, the
    same layout as the Teams card
    """
    blocks = []

    if raw_results:
        blocks.append(build_markdown(results.header_text()))

        for result in raw_results:
            blocks += build_tables(
                results.result_heading(result),
                [
                    results.build_detail_content(detail)
                    for detail in result["contract_details"]
                ],
            )

    return blocks


def format_sam_error(status: int | str, message: str | None) -> list[dict]:
    """
    Format the SAM.gov error note
    """
    return [build_markdown(results.sam_error(status, message))]


def split_messages(blocks: list[dict]) -> list[list[dict]]:
    """
    Group blocks into messages that stay within Slack's per-message limits
    """
    messages: list[list[dict]] = []
    current: list[dict] = []
    markdown_chars = table_chars_total = tables = 0

    for block in blocks:
        is_table = block["type"] == "table"
        size = table_chars(block) if is_table else len(block["text"])

        if current and (
            len(current) >= MAX_BLOCKS
            or (is_table and tables >= MAX_TABLES_PER_MESSAGE)
            or (is_table and table_chars_total + size > MAX_TABLE_CHARS)
            or (not is_table and markdown_chars + size > MAX_MARKDOWN_CHARS)
        ):
            messages.append(current)
            current = []
            markdown_chars = table_chars_total = tables = 0

        current.append(block)

        if is_table:
            tables += 1
            table_chars_total += size
        else:
            markdown_chars += size

    if current:
        messages.append(current)

    return messages


def block_text(block: dict) -> str:
    """
    Plain text of a markdown block, or of a table's first cell
    """
    if block["type"] == "table":
        section = block["rows"][0][0]["elements"][0]
        return "".join(element["text"] for element in section["elements"])

    return block["text"].replace("**", "")


def fallback_text(blocks: list[dict]) -> str:
    """
    Plain text used in notifications, from the message's first block
    """
    return block_text(blocks[0])[:150]


def post(webhook_url: str, items: list[dict]) -> None:
    """
    Execute Slack post, splitting into several messages when needed
    """
    http = urllib3.PoolManager(ca_certs=certifi.where())

    for n, blocks in enumerate(split_messages(items)):
        if n:
            # Incoming webhooks allow about one message per second
            time.sleep(1)

        response = http.request(
            "POST",
            webhook_url,
            json={"text": fallback_text(blocks), "blocks": blocks},
            timeout=30,
        )

        if response.status != 200:
            body = response.data.decode(errors="replace")
            raise SlackPostError(
                f"Slack webhook returned HTTP {response.status}: {body}"
            )
