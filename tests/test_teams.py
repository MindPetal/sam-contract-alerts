"""
Tests for teams.py
"""

from datetime import date

import client
from sam_contract_alerts import teams


def test_build_textblock():
    result = teams.build_textblock("Test content")
    expected = {"type": "TextBlock", "text": "Test content", "wrap": True}

    assert result == expected


def test_format_results_with_contract_no():
    raw_results = [
        {
            "index": 1,
            "contract_no": "123456789",
            "contract_nm": "Test Contract",
            "contract_details": [
                {
                    "date": "Feb 25, 2024",
                    "company": "Test Company",
                    "action": "Exercise an option: $50,000 delivery order",
                    "total_obligated": "$86,974,480.71",
                    "total_value": "$170,000,000",
                    "desc": "Test description",
                    "piid": "123456789",
                    "unique_entity_id": "SAMPLEUEI12345",
                    "pop_start": "Mar 01, 2024",
                    "pop_end_date": "Jun 30, 2025",
                    "contract_end_date": "Jun 30, 2026",
                }
            ],
        }
    ]

    result = teams.format_results(raw_results)

    assert len(result) == 4
    assert (
        result[0]["text"]
        == f"**{date.today().strftime('%A, %m/%d/%Y')}.** Contract updates."
    )

    table = result[2]
    assert table["type"] == "Table"
    assert table["firstRowAsHeaders"] is True
    assert len(table["rows"]) == 2
    heading_text = table["rows"][0]["cells"][0]["items"][0]["text"]
    assert table["rows"][0]["style"] == "accent"
    assert "Test Contract" in heading_text
    assert "123456789" in heading_text
    assert "1." not in heading_text
    row_text = table["rows"][1]["cells"][0]["items"][0]["text"]
    assert " | " in row_text
    assert "[123456789]" in row_text
    assert "**Contract:**" not in row_text
    assert "sam.gov" in row_text
    assert "Test Company" in row_text
    assert (
        "[Test Company](https://sam.gov/entities/view/SAMPLEUEI12345/coreData?status=Active)"
        in row_text
    )
    # company name appears before contract no
    assert row_text.index("Test Company") < row_text.index("[123456789]")
    assert "Exercise an option: $50,000 delivery order" in row_text
    assert "**To Date:** $86,974,480.71" in row_text
    assert "**TCV:** $170,000,000" in row_text
    assert "**Start:** Mar 01, 2024" in row_text
    assert "**End:** Jun 30, 2025" in row_text
    assert "**Contract End:** Jun 30, 2026" in row_text
    assert "Test description" in row_text


def test_format_results_with_naics():
    raw_results = [
        {
            "index": 1,
            "agency": "Test Agency",
            "contract_details": [
                {
                    "date": "Feb 25, 2024",
                    "company": "Test Company",
                    "action": "Exercise an option: $50,000 delivery order",
                    "total_obligated": "$86,974,480.71",
                    "total_value": "$170,000,000",
                    "desc": "Test description",
                    "piid": "987654321",
                    "pop_start": "Mar 01, 2024",
                    "pop_end_date": "Jun 30, 2025",
                    "contract_end_date": "Jun 30, 2026",
                }
            ],
        }
    ]

    result = teams.format_results(raw_results)

    assert len(result) == 4
    heading_text = result[2]["rows"][0]["cells"][0]["items"][0]["text"]
    assert heading_text == "**Test Agency** updates:"
    assert "NAICS" not in heading_text
    assert "1." not in heading_text

    table = result[2]
    assert table["type"] == "Table"
    assert table["firstRowAsHeaders"] is True
    assert len(table["rows"]) == 2
    assert table["rows"][0]["style"] == "accent"
    row_text = table["rows"][1]["cells"][0]["items"][0]["text"]
    assert " | " in row_text
    assert "[987654321]" in row_text
    assert "**Contract:**" not in row_text
    assert "**To Date:** $86,974,480.71" in row_text
    assert "**End:** Jun 30, 2025" in row_text
    assert "**Contract End:** Jun 30, 2026" in row_text
    # company name appears before contract no
    assert row_text.index("Test Company") < row_text.index("[987654321]")


def test_format_results_multiple_details_single_table():
    detail = {
        "date": "Feb 25, 2024",
        "company": "Test Company",
        "action": "Exercise an option: $50,000 delivery order",
        "total_obligated": "$86,974,480.71",
        "total_value": "$170,000,000",
        "desc": "Test description",
        "piid": "PIID-A",
        "pop_start": "Mar 01, 2024",
        "pop_end_date": "Jun 30, 2025",
        "contract_end_date": "Jun 30, 2026",
    }
    raw_results = [
        {
            "index": 1,
            "contract_no": "IDV123",
            "contract_nm": "Test IDV",
            "contract_details": [
                {**detail, "piid": "PIID-A"},
                {**detail, "piid": "PIID-B"},
            ],
        }
    ]

    result = teams.format_results(raw_results)

    # One table with the heading as a header row plus a data row per contract
    tables = [item for item in result if item.get("type") == "Table"]
    assert len(tables) == 1

    rows = tables[0]["rows"]
    assert len(rows) == 3
    assert rows[0]["style"] == "accent"
    assert "Test IDV" in rows[0]["cells"][0]["items"][0]["text"]
    assert rows[1]["style"] == "default"
    assert rows[2]["style"] == "emphasis"
    assert "PIID-A" in rows[1]["cells"][0]["items"][0]["text"]
    assert "PIID-B" in rows[2]["cells"][0]["items"][0]["text"]


def test_format_results_blank_reason_omitted():
    raw_results = [
        {
            "index": 1,
            "contract_no": "123456789",
            "contract_nm": "Test Contract",
            "contract_details": [
                {
                    "date": "Feb 25, 2024",
                    "company": "Test Company",
                    "action": "$50,000 delivery order",
                    "total_obligated": "$86,974,480.71",
                    "total_value": "$170,000,000",
                    "desc": "Test description",
                    "piid": "123456789",
                    "unique_entity_id": "SAMPLEUEI12345",
                    "pop_start": "Mar 01, 2024",
                    "pop_end_date": "Jun 30, 2025",
                    "contract_end_date": "Jun 30, 2026",
                }
            ],
        }
    ]

    result = teams.format_results(raw_results)

    row_text = result[2]["rows"][1]["cells"][0]["items"][0]["text"]
    # blank reason field is omitted, so no empty segment between piid and obligation
    assert "|  |" not in row_text
    assert "[123456789](https://sam.gov/search/" in row_text
    assert "$50,000" in row_text
    # piid link is immediately followed by obligation
    assert row_text.index("$50,000") - row_text.index("[123456789]") < 200
    assert "Test description" in row_text


def test_format_results_empty():
    result = teams.format_results([])

    assert result == []


def test_post(mocker):
    items = [{"type": "TextBlock", "text": "Test", "wrap": True}]

    mock_teams_post = mocker.patch.object(client.MsApi, "teams_post", autospec=True)

    teams.post("https://webhook.example.com", items)

    mock_teams_post.assert_called_once()
    api_instance = mock_teams_post.call_args.args[0]
    assert api_instance.api_client.configuration.host == "https://webhook.example.com"
    body = mock_teams_post.call_args.kwargs["body"]
    assert body["type"] == "message"
    assert body["attachments"][0]["content"]["body"][0]["items"] == items
