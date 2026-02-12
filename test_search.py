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
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "50000"},
            "total_contract_dollars": {"total_base_and_all_options_value": "170000000"},
            "awardee_data": {
                "awardee_header": {
                    "awardee_name": "Test Company",
                    "legal_business_name": "Test Company Inc",
                },
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": "Test description\nwith newline"
            },
        },
    }

    result = search.extract_contract_details(award_summary)

    assert result["date"] == "February 25, 2024"
    assert result["company"] == "Test Company"
    assert result["obligation"] == "$50,000"
    assert result["total_value"] == "$170,000,000"
    assert result["reason"] == "Exercise An Option"
    assert result["desc"] == "Test description\nwith newline"
    assert result["piid"] == "123456789"


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


def test_format_results_with_contract_no():
    raw_results = [
        {
            "index": 1,
            "contract_no": "123456789",
            "contract_nm": "Test Contract",
            "contract_details": [
                {
                    "date": "February 25, 2024",
                    "company": "Test Company",
                    "reason": "Exercise An Option",
                    "obligation": "$50,000",
                    "total_value": "$170,000,000",
                    "desc": "Test description",
                    "piid": "123456789",
                }
            ],
        }
    ]

    result = search.format_results(raw_results)

    assert len(result) == 4
    assert (
        result[0]["text"]
        == f'**{date.today().strftime("%A, %m/%d/%Y")}.** Contract updates.'
    )
    assert "Test Contract" in result[2]["text"]
    assert "123456789" in result[2]["text"]
    assert "**Contract:** [123456789]" in result[2]["text"]
    assert "sam.gov" in result[2]["text"]
    assert "Test Company" in result[2]["text"]
    assert "Exercise An Option" in result[2]["text"]
    assert "$50,000" in result[2]["text"]
    assert "$170,000,000" in result[2]["text"]
    assert "Test description" in result[2]["text"]


def test_format_results_with_naics():
    raw_results = [
        {
            "index": 1,
            "naics": "541512",
            "agency": "Test Agency",
            "contract_details": [
                {
                    "date": "February 25, 2024",
                    "company": "Test Company",
                    "reason": "Exercise An Option",
                    "obligation": "$50,000",
                    "total_value": "$170,000,000",
                    "desc": "Test description",
                    "piid": "987654321",
                }
            ],
        }
    ]

    result = search.format_results(raw_results)

    assert len(result) == 4
    assert "Test Agency" in result[2]["text"]
    assert "541512" in result[2]["text"]
    assert "**Contract:** [987654321]" in result[2]["text"]


def test_format_results_empty():
    result = search.format_results([])

    assert result == []


def test_build_search_url_contract_no():
    result = search.build_search_url("123456789")

    assert "123456789" in result
    assert "sam.gov" in result


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
    assert any("Test Contract" in item.get("text", "") for item in result)


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
    assert any("TA" in item.get("text", "") for item in result)


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
    assert any("Test Contract" in item.get("text", "") for item in result)


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
