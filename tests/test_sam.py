"""
Tests for sam.py
"""

import client
from sam_contract_alerts import sam


def test_search_by_contract_no(mocker, api_client):
    # Mock API response
    api_response = client.AwardResponse()
    award_summary = client.AwardSummary()
    award_summary.contract_id = client.ContractId()
    award_summary.award_details = client.AwardDetails(
        total_contract_dollars=client.TotalContractDollars()
    )
    api_response.award_summary = [award_summary]

    mocker.patch("client.SamApi.search", return_value=api_response)

    result = sam.search(
        api_client, "test-api-key", "02/24/2024", {"contract_no": "123456789"}
    )

    assert result == api_response.to_dict().get("award_summary", [])


def test_search_by_contract_no_with_idv_no(mocker, api_client):
    api_response = client.AwardResponse()
    api_response.award_summary = []

    mock_search = mocker.patch("client.SamApi.search", return_value=api_response)

    sam.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"contract_no": "75N98027F00001", "idv_no": "75N91023A00006"},
    )

    kwargs = mock_search.call_args.kwargs
    assert kwargs["piid"] == "75N98027F00001"
    assert kwargs["referenced_idv_piid"] == "75N91023A00006"


def test_search_by_contract_no_without_idv_no(mocker, api_client):
    api_response = client.AwardResponse()
    api_response.award_summary = []

    mock_search = mocker.patch("client.SamApi.search", return_value=api_response)

    sam.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"contract_no": "75N98027F00001", "idv_no": ""},
    )

    kwargs = mock_search.call_args.kwargs
    assert kwargs["piid"] == "75N98027F00001"
    assert "referenced_idv_piid" not in kwargs


def test_search_by_naics(mocker, api_client):
    # Mock API response
    api_response = client.AwardResponse()
    award_summary = client.AwardSummary()
    award_summary.contract_id = client.ContractId()
    award_summary.award_details = client.AwardDetails(
        total_contract_dollars=client.TotalContractDollars()
    )
    api_response.award_summary = [award_summary]

    mocker.patch("client.SamApi.search", return_value=api_response)

    result = sam.search(
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

    mocker.patch("client.SamApi.search", return_value=api_response)

    result = sam.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"parent_contract_no": "123456789"},
    )

    assert result == api_response.to_dict().get("award_summary", [])
