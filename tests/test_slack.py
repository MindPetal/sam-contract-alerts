"""
Tests for slack.py
"""

from datetime import date

import pytest

from sam_contract_alerts import results, slack

DETAIL = {
    "date": "11/10/2026",
    "company": "ACME FEDERAL SOLUTIONS LLC",
    "unique_entity_id": "TESTUEI00001",
    "action": "New work: $8,524,708 delivery order",
    "total_obligated": "$8,524,708",
    "total_value": "$50,000,000",
    "desc": "Business applications services",
    "piid": "TEST27F00001",
    "pop_start": "11/15/2026",
    "pop_end_date": "11/14/2027",
    "contract_end_date": "11/14/2031",
    "competition": "1 offer received.",
}


def cell_text(cell: dict) -> str:
    return "".join(e["text"] for e in cell["elements"][0]["elements"])


def table_texts(table: dict) -> list[str]:
    return [cell_text(row[0]) for row in table["rows"]]


def test_format_results():
    raw_results = [
        {
            "index": 1,
            "contract_no": "TEST27F00001",
            "contract_nm": "Test Program (Acme)",
            "contract_details": [DETAIL, {**DETAIL, "piid": "OTHER"}],
        },
        {"index": 2, "agency": "TA", "contract_details": [DETAIL]},
    ]

    blocks = slack.format_results(raw_results)

    assert [block["type"] for block in blocks] == ["markdown", "table", "table"]
    assert blocks[0]["text"] == (
        f"**{date.today().strftime('%A, %m/%d/%Y')}.** Contract updates."
    )
    # One table per contract or agency: heading row, then one row per detail
    assert table_texts(blocks[1]) == [
        "Test Program (Acme) - TEST27F00001:",
        cell_text(slack.build_cell(results.build_detail_content(DETAIL))),
        cell_text(
            slack.build_cell(results.build_detail_content({**DETAIL, "piid": "OTHER"}))
        ),
    ]
    assert table_texts(blocks[2])[0] == "TA updates:"
    assert blocks[1]["column_settings"] == [{"is_wrapped": True}]


def test_build_cell_keeps_bold_and_links():
    cell = slack.build_cell(
        "[ACME](https://sam.gov/entities/view/X) | 11/10/2026 | **TCV:** $5 | A & B"
    )

    assert cell == {
        "type": "rich_text",
        "elements": [
            {
                "type": "rich_text_section",
                "elements": [
                    {
                        "type": "link",
                        "text": "ACME",
                        "url": "https://sam.gov/entities/view/X",
                    },
                    {"type": "text", "text": " | 11/10/2026 | "},
                    {"type": "text", "text": "TCV:", "style": {"bold": True}},
                    {"type": "text", "text": " $5 | A & B"},
                ],
            }
        ],
    }


def test_build_cell_plain_and_empty_text():
    assert cell_text(slack.build_cell("plain")) == "plain"
    assert cell_text(slack.build_cell("")) == " "


def test_build_tables_splits_long_tables():
    contents = ["x" * 1_000] * 25

    tables = slack.build_tables("**Heading**:", contents)

    assert [len(t["rows"]) for t in tables] == [10, 10, 8]
    assert [table_texts(t)[0] for t in tables] == [
        "Heading:",
        "Heading: (continued)",
        "Heading: (continued)",
    ]
    assert all(slack.table_chars(t) <= slack.MAX_TABLE_CHARS for t in tables)


def test_build_tables_row_limit():
    tables = slack.build_tables("H", ["x"] * 150)

    assert [len(t["rows"]) for t in tables] == [100, 52]


def test_split_messages_one_table_per_message():
    blocks = [block("header")] + slack.build_tables("A", ["a"]) * 3

    messages = slack.split_messages(blocks)

    assert [[b["type"] for b in m] for m in messages] == [
        ["markdown", "table"],
        ["table"],
        ["table"],
    ]


def test_split_messages_groups_tables_when_allowed(mocker):
    mocker.patch.object(slack, "MAX_TABLES_PER_MESSAGE", 10)
    table = slack.build_tables("A", ["x" * 4_000])[0]

    messages = slack.split_messages([block("header"), table, table, table])

    # Grouped until the 10,000 character table limit
    assert [len(m) for m in messages] == [3, 1]


def test_fallback_text_from_table():
    table = slack.build_tables("**Test Program** - TEST27F00001:", ["row"])[0]

    assert slack.fallback_text([table]) == "Test Program - TEST27F00001:"


def test_format_results_empty():
    assert slack.format_results([]) == []


def block(text: str) -> dict:
    return {"type": "markdown", "text": text}


def test_split_messages_by_block_count():
    blocks = [block("x") for _ in range(120)]

    messages = slack.split_messages(blocks)

    assert [len(m) for m in messages] == [50, 50, 20]


def test_split_messages_by_character_limit():
    blocks = [block("x" * 5_000) for _ in range(5)]

    messages = slack.split_messages(blocks)

    assert [len(m) for m in messages] == [2, 2, 1]
    assert all(
        sum(len(b["text"]) for b in m) <= slack.MAX_MARKDOWN_CHARS for m in messages
    )


def test_build_markdown_truncates_oversized_text():
    text = slack.build_markdown("x" * 20_000)["text"]

    assert len(text) == slack.MAX_MARKDOWN_CHARS
    assert text.endswith("…")


class FakeResponse:
    def __init__(self, status: int, data: bytes = b"ok"):
        self.status = status
        self.data = data


def test_post(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request", return_value=FakeResponse(200)
    )
    blocks = [block("**Monday, 11/16/2026.** Contract updates."), block("- row")]

    slack.post("https://hooks.slack.com/services/T/B/X", blocks)

    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert args == ("POST", "https://hooks.slack.com/services/T/B/X")
    assert kwargs["json"] == {
        "text": "Monday, 11/16/2026. Contract updates.",
        "blocks": blocks,
    }


def test_post_splits_long_results(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request", return_value=FakeResponse(200)
    )
    mock_sleep = mocker.patch("sam_contract_alerts.slack.time.sleep")

    slack.post("https://hooks.slack.com/services/T/B/X", [block("x")] * 60)

    assert [len(c.kwargs["json"]["blocks"]) for c in mock_request.call_args_list] == [
        50,
        10,
    ]
    mock_sleep.assert_called_once_with(1)


def test_post_raises_on_error(mocker):
    mocker.patch(
        "urllib3.PoolManager.request",
        return_value=FakeResponse(404, b"channel_not_found"),
    )

    with pytest.raises(slack.SlackPostError, match="404: channel_not_found"):
        slack.post("https://hooks.slack.com/services/T/B/X", [block("x")])


def test_post_nothing_to_send(mocker):
    mock_request = mocker.patch("urllib3.PoolManager.request")

    slack.post("https://hooks.slack.com/services/T/B/X", [])

    mock_request.assert_not_called()
