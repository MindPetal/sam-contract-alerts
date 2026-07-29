"""
Tests for search.py
"""

from datetime import date

import pytest

import client
import search


@pytest.fixture
def api_client():
    api_config = search.client.Configuration()
    api_config.host = "https://api.sam.gov"

    return client.ApiClient(api_config)


def all_text(result: list) -> str:
    """Concatenate every renderable text string (TextBlocks and table cells)."""
    texts = []
    for item in result:
        if item.get("type") == "TextBlock":
            texts.append(item.get("text", ""))
        elif item.get("type") == "Table":
            for row in item["rows"]:
                for cell in row["cells"]:
                    for cell_item in cell["items"]:
                        texts.append(cell_item.get("text", ""))
    return "\n".join(texts)


def test_search_by_contract_no(mocker, api_client):
    # Mock API response
    api_response = client.AwardResponse()
    award_summary = client.AwardSummary()
    award_summary.contract_id = client.ContractId()
    award_summary.award_details = client.AwardDetails(
        total_contract_dollars=client.TotalContractDollars()
    )
    api_response.award_summary = [award_summary]

    mocker.patch("search.client.SamApi.search", return_value=api_response)

    result = search.search(
        api_client, "test-api-key", "02/24/2024", {"contract_no": "123456789"}
    )

    assert result == api_response.to_dict().get("award_summary", [])


def test_search_by_naics(mocker, api_client):
    # Mock API response
    api_response = client.AwardResponse()
    award_summary = client.AwardSummary()
    award_summary.contract_id = client.ContractId()
    award_summary.award_details = client.AwardDetails(
        total_contract_dollars=client.TotalContractDollars()
    )
    api_response.award_summary = [award_summary]

    mocker.patch("search.client.SamApi.search", return_value=api_response)

    result = search.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"naics": "541512", "agency": "Test Agency"},
    )

    assert result == api_response.to_dict().get("award_summary", [])


def test_search_by_referenced_idv_piid(mocker, api_client):
    # Mock API response for child awards
    api_response = client.AwardResponse()
    award_summary = client.AwardSummary()
    award_summary.contract_id = client.ContractId()
    award_summary.award_details = client.AwardDetails(
        total_contract_dollars=client.TotalContractDollars()
    )
    api_response.award_summary = [award_summary]

    mocker.patch("search.client.SamApi.search", return_value=api_response)

    result = search.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"parent_contract_no": "123456789"},
    )

    assert result == api_response.to_dict().get("award_summary", [])


def test_build_textblock():
    result = search.build_textblock("Test content")
    expected = {"type": "TextBlock", "text": "Test content", "wrap": True}

    assert result == expected


def test_extract_contract_details():
    award_summary = {
        "contract_id": {
            "piid": "123456789",
            "modification_number": "0",
            "reason_for_modification": {"name": "Exercise An Option"},
        },
        "award_details": {
            "dates": {
                "date_signed": "2024-02-25T00:00:00Z",
                "period_of_performance_start_date": "2024-03-01 00:00:00.000",
                "current_completion_date": "2025-06-30 00:00:00.000",
                "ultimate_completion_date": "2026-06-30 00:00:00.000",
            },
            "dollars": {"action_obligation": "50000"},
            "total_contract_dollars": {
                "total_base_and_exercised_options_value": "86974480.71",
                "total_base_and_all_options_value": "170000000",
            },
            "awardee_data": {
                "awardee_header": {
                    "awardee_name": "Test Company",
                    "legal_business_name": "Test Company Inc",
                },
                "awardee_uei_information": {
                    "unique_entity_id": "SAMPLEUEI12345",
                },
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Test description\nwith newline"
            },
        },
    }

    result = search.extract_contract_details(award_summary)

    assert result["date"] == "02/25/2024"
    assert result["company"] == "Test Company"
    assert result["unique_entity_id"] == "SAMPLEUEI12345"
    assert result["obligation"] == "$50,000"
    assert result["total_obligated"] == "$86,974,480.71"
    assert result["total_value"] == "$170,000,000"
    assert result["reason"] == "Exercise An Option"
    assert result["desc"] == "Test description\nwith newline"
    assert result["piid"] == "123456789"
    assert result["pop_start"] == "03/01/2024"
    assert result["pop_end_date"] == "06/30/2025"
    assert result["contract_end_date"] == "06/30/2026"


def test_extract_contract_details_fallback_to_awardee_name():
    award_summary = {
        "contract_id": {"reason_for_modification": {}},
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {},
            "total_contract_dollars": {},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Test Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {},
        },
    }

    result = search.extract_contract_details(award_summary)

    assert result["company"] == "Test Company"
    assert result["unique_entity_id"] == ""
    assert result["total_obligated"] == ""
    assert result["pop_start"] == ""
    assert result["pop_end_date"] == ""
    assert result["contract_end_date"] == ""


def test_extract_contract_details_empty_obligation():
    award_summary = {
        "contract_id": {"reason_for_modification": {}},
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": ""},
            "total_contract_dollars": {},
            "awardee_data": {
                "awardee_header": {},
                "awardee_location": {},
            },
            "product_or_service_information": {},
        },
    }

    result = search.extract_contract_details(award_summary)

    assert result["obligation"] == ""
    assert result["total_obligated"] == ""
    assert result["pop_start"] == ""
    assert result["pop_end_date"] == ""
    assert result["contract_end_date"] == ""


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
                    "reason": "Exercise An Option",
                    "obligation": "$50,000",
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

    result = search.format_results(raw_results)

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
    assert "Exercise An Option" in row_text
    assert "$50,000" in row_text
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
            "naics": "541512",
            "agency": "Test Agency",
            "contract_details": [
                {
                    "date": "Feb 25, 2024",
                    "company": "Test Company",
                    "reason": "Exercise An Option",
                    "obligation": "$50,000",
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

    result = search.format_results(raw_results)

    assert len(result) == 4
    heading_text = result[2]["rows"][0]["cells"][0]["items"][0]["text"]
    assert "Test Agency" in heading_text
    assert "541512" in heading_text
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


def test_format_results_multiple_details_single_table():
    detail = {
        "date": "Feb 25, 2024",
        "company": "Test Company",
        "reason": "Exercise An Option",
        "obligation": "$50,000",
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

    result = search.format_results(raw_results)

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


def test_format_results_empty():
    result = search.format_results([])

    assert result == []


def test_build_search_url_contract_no():
    result = search.build_search_url("123456789")

    assert "123456789" in result
    assert "sam.gov" in result


def test_build_entity_url():
    result = search.build_entity_url("SAMPLEUEI12345")

    assert (
        result == "https://sam.gov/entities/view/SAMPLEUEI12345/coreData?status=Active"
    )


def test_search_contracts(mocker, api_client):
    award_summary_dict = {
        "contract_id": {
            "piid": "123456789",
            "reason_for_modification": {"name": "Exercise An Option"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "50000"},
            "total_contract_dollars": {"total_base_and_all_options_value": "100000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Test Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Test desc"
            },
        },
    }

    mocker.patch("search.search", return_value=[award_summary_dict])

    results = search.search_contracts(
        api_client, "test-api-key", "123456789:Test Contract:AWARD", "02/24/2024"
    )

    assert len(results) == 1
    assert results[0]["contract_no"] == "123456789"
    assert results[0]["contract_nm"] == "Test Contract"
    assert len(results[0]["contract_details"]) == 1


def test_search_naics(mocker, api_client):
    award_summary_dict = {
        "contract_id": {
            "piid": "987654321",
            "reason_for_modification": {"name": "New Work"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "100000"},
            "total_contract_dollars": {"total_base_and_all_options_value": "200000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Another Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "NAICS desc"
            },
        },
    }

    mocker.patch("search.search", return_value=[award_summary_dict])

    results = search.search_naics(
        api_client, "test-api-key", "541512:Test+Agency:TA", "02/24/2024"
    )

    assert len(results) == 1
    assert results[0]["naics"] == "541512"
    assert results[0]["agency"] == "TA"
    assert len(results[0]["contract_details"]) == 1


def test_process_search_contract_no(mocker, api_client):
    # Mock API response
    api_response = client.AwardResponse()
    award_summary_dict = {
        "contract_id": {
            "piid": "123456789",
            "reason_for_modification": {"name": "Exercise An Option"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "50000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Test Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Test desc"
            },
        },
    }
    api_response.award_summary = [award_summary_dict]

    mocker.patch("search.search", return_value=[award_summary_dict])

    result = search.process_search(
        api_client, "test-api-key", "123456789:Test Contract:AWARD", ""
    )

    assert len(result) > 0
    assert "Test Contract" in all_text(result)


def test_process_search_naics(mocker, api_client):
    # Mock API response
    award_summary_dict = {
        "contract_id": {
            "piid": "987654321",
            "reason_for_modification": {"name": "New Work"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "100000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Another Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "NAICS desc"
            },
        },
    }

    mocker.patch("search.search", return_value=[award_summary_dict])

    result = search.process_search(
        api_client, "test-api-key", "", "541512:Test+Agency:TA"
    )

    assert len(result) > 0
    assert "TA" in all_text(result)


def test_process_search_idv(mocker, api_client):
    # Mock API responses for both parent IDV and child awards
    parent_summary = {
        "contract_id": {
            "piid": "123456789",
            "modification_number": "P00002",
            "reason_for_modification": {"name": "Exercise An Option"},
        },
        "award_details": {
            "dates": {"date_signed": "2025-06-20T00:00:00Z"},
            "dollars": {"action_obligation": "0"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "INDEV"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Exercise option period 1"
            },
        },
    }

    child_summary = {
        "contract_id": {
            "piid": "987654321",
            "modification_number": "0",
            "reason_for_modification": {},
        },
        "award_details": {
            "dates": {"date_signed": "2026-02-04T00:00:00Z"},
            "dollars": {"action_obligation": "499715.2"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "INDEV"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "O&M for M365 and Salesforce"
            },
        },
    }

    # Mock search to return parent for first call, child for second call
    mocker.patch("search.search", side_effect=[[parent_summary], [child_summary]])

    result = search.process_search(
        api_client, "test-api-key", "123456789:Test Contract:IDV", ""
    )

    assert len(result) > 0
    # Should have both parent and child details
    assert "Test Contract" in all_text(result)


def test_process_search_dedupes_piids(mocker, api_client):
    # Same PIID appearing in a contract search and a NAICS search
    shared_summary = {
        "contract_id": {
            "piid": "DUPLICATE123",
            "reason_for_modification": {"name": "Exercise An Option"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "50000"},
            "total_contract_dollars": {"total_base_and_all_options_value": "100000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Test Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Test desc"
            },
        },
    }

    unique_summary = {
        "contract_id": {
            "piid": "UNIQUE456",
            "reason_for_modification": {"name": "New Work"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "75000"},
            "total_contract_dollars": {"total_base_and_all_options_value": "200000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Another Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Unique desc"
            },
        },
    }

    mocker.patch(
        "search.search",
        side_effect=[[shared_summary], [shared_summary, unique_summary]],
    )

    result = search.process_search(
        api_client,
        "test-api-key",
        "DUPLICATE123:Test Contract:AWARD",
        "541512:Test Agency:TA",
    )

    # Associate each detail table with its header-row heading
    sections: dict[str, list[str]] = {}

    for item in result:
        if item.get("type") == "Table":
            heading = item["rows"][0]["cells"][0]["items"][0]["text"]
            row_text = "\n".join(
                row["cells"][0]["items"][0]["text"] for row in item["rows"][1:]
            )
            sections.setdefault(heading, []).append(row_text)

    naics_headings = [h for h in sections if h and "TA" in h and "NAICS" in h]
    assert len(naics_headings) == 1

    naics_text = "\n".join(sections[naics_headings[0]])
    assert "UNIQUE456" in naics_text
    assert "DUPLICATE123" not in naics_text

    contract_headings = [h for h in sections if "Test Contract" in h]
    assert len(contract_headings) == 1
    assert "DUPLICATE123" in "\n".join(sections[contract_headings[0]])


def test_process_search_no_results(mocker, api_client):
    mocker.patch("search.search", return_value=[])

    result = search.process_search(
        api_client, "test-api-key", "123456789:Test Contract:AWARD", ""
    )

    assert result == []


def test_teams_post(mocker, api_client):
    items = [{"type": "TextBlock", "text": "Test", "wrap": True}]

    mock_teams_post = mocker.patch("search.client.MsApi.teams_post")

    search.teams_post(api_client, items)

    mock_teams_post.assert_called_once()
    call_args = mock_teams_post.call_args[1]
    assert "body" in call_args
    assert call_args["body"]["type"] == "message"


def test_main(mocker, api_client):
    mocker.patch("search.client.ApiClient", return_value=api_client)
    mocker.patch(
        "search.process_search", return_value=[{"type": "TextBlock", "text": "Test"}]
    )
    mock_teams_post = mocker.patch("search.teams_post")

    search.main("test-api-key", "123:Test", "", "https://webhook.example.com")

    mock_teams_post.assert_called_once()


def test_main_no_results(mocker, api_client):
    mocker.patch("search.client.ApiClient", return_value=api_client)
    mocker.patch("search.process_search", return_value=[])
    mock_teams_post = mocker.patch("search.teams_post")

    search.main("test-api-key", "123:Test", "", "https://webhook.example.com")

    mock_teams_post.assert_not_called()
