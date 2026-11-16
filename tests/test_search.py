"""
Tests for search.py
"""

from sam_contract_alerts import search
from sam_contract_alerts.config import (
    ContractEntry,
    Settings,
    parse_contract_list,
    parse_naics_list,
)

SAM_SEARCH = "sam_contract_alerts.sam.search"


def award_summary(piid: str, company: str = "Test Company", desc: str = "") -> dict:
    return {
        "contract_id": {
            "piid": piid,
            "reason_for_modification": {"name": "Exercise An Option"},
        },
        "award_details": {
            "dates": {"date_signed": "2024-02-25T00:00:00Z"},
            "dollars": {"action_obligation": "50000"},
            "total_contract_dollars": {"total_base_and_all_options_value": "100000"},
            "awardee_data": {
                "awardee_header": {"awardee_name": company},
                "awardee_location": {},
            },
            "product_or_service_information": {
                "description_of_contract_requirement": desc
            },
        },
    }


def piids(result: dict) -> list[str]:
    return [detail["piid"] for detail in result["contract_details"]]


def test_search_contracts(mocker, api_client):
    mocker.patch(SAM_SEARCH, return_value=[award_summary("123456789")])

    results = search.search_contracts(
        api_client,
        "test-api-key",
        parse_contract_list("123456789:Test Contract:AWARD"),
        "02/24/2024",
    )

    assert len(results) == 1
    assert results[0]["contract_no"] == "123456789"
    assert results[0]["contract_nm"] == "Test Contract"
    assert len(results[0]["contract_details"]) == 1


def test_search_naics(mocker, api_client):
    mock_search = mocker.patch(
        SAM_SEARCH, return_value=[award_summary("987654321", "Another Company")]
    )

    results = search.search_naics(
        api_client,
        "test-api-key",
        parse_naics_list("Test+Agency:TA:[541512-541511]"),
        "02/24/2024",
    )

    # Each NAICS code is searched separately, results combined per agency
    assert [c.args[3] for c in mock_search.call_args_list] == [
        {"naics": "541512", "agency": "Test+Agency"},
        {"naics": "541511", "agency": "Test+Agency"},
    ]
    assert len(results) == 1
    assert "naics" not in results[0]
    assert results[0]["agency"] == "TA"
    assert len(results[0]["contract_details"]) == 2


def test_search_naics_omits_agency_without_updates(mocker, api_client):
    mocker.patch(SAM_SEARCH, return_value=[])

    results = search.search_naics(
        api_client,
        "test-api-key",
        parse_naics_list("Test+Agency:TA:[541512-541511]"),
        "02/24/2024",
    )

    assert results == []


def test_process_search_contract_no(mocker, api_client):
    mocker.patch(SAM_SEARCH, return_value=[award_summary("123456789")])

    result = search.process_search(
        api_client,
        "test-api-key",
        parse_contract_list("123456789:Test Contract:AWARD"),
        [],
    )

    assert len(result) == 1
    assert result[0]["index"] == 1
    assert result[0]["contract_nm"] == "Test Contract"
    assert piids(result[0]) == ["123456789"]


def test_process_search_naics(mocker, api_client):
    mocker.patch(
        SAM_SEARCH, return_value=[award_summary("987654321", "Another Company")]
    )

    result = search.process_search(
        api_client, "test-api-key", [], parse_naics_list("Test+Agency:TA:[541512]")
    )

    assert len(result) == 1
    assert result[0]["agency"] == "TA"
    assert piids(result[0]) == ["987654321"]


def test_process_search_idv(mocker, api_client):
    parent_summary = award_summary("123456789", "INDEV", "Exercise option period 1")
    child_summary = award_summary("987654321", "INDEV", "O&M for M365 and Salesforce")

    # Mock search to return parent for first call, child for second call
    mock_search = mocker.patch(
        SAM_SEARCH, side_effect=[[parent_summary], [child_summary]]
    )

    result = search.process_search(
        api_client,
        "test-api-key",
        parse_contract_list("123456789:Test Contract:IDV"),
        [],
    )

    assert [c.args[3] for c in mock_search.call_args_list] == [
        {"contract_no": "123456789", "idv_no": ""},
        {"parent_contract_no": "123456789"},
    ]
    # Should have both parent and child details under one contract
    assert len(result) == 1
    assert result[0]["contract_nm"] == "Test Contract"
    assert piids(result[0]) == ["123456789", "987654321"]


def test_process_search_dedupes_piids(mocker, api_client):
    # Same PIID appearing in a contract search and a NAICS search
    shared_summary = award_summary("DUPLICATE123")
    unique_summary = award_summary("UNIQUE456", "Another Company")

    mocker.patch(
        SAM_SEARCH,
        side_effect=[[shared_summary], [shared_summary, unique_summary]],
    )

    result = search.process_search(
        api_client,
        "test-api-key",
        parse_contract_list("DUPLICATE123:Test Contract:AWARD"),
        parse_naics_list("Test Agency:TA:[541512]"),
    )

    assert [r.get("contract_nm") or r.get("agency") for r in result] == [
        "Test Contract",
        "TA",
    ]
    assert [r["index"] for r in result] == [1, 2]
    assert piids(result[0]) == ["DUPLICATE123"]
    assert piids(result[1]) == ["UNIQUE456"]


def test_process_search_no_results(mocker, api_client):
    mocker.patch(SAM_SEARCH, return_value=[])

    result = search.process_search(
        api_client,
        "test-api-key",
        parse_contract_list("123456789:Test Contract:AWARD"),
        [],
    )

    assert result == []


def test_process_search_passes_idv_no(mocker, api_client):
    mock_search = mocker.patch(SAM_SEARCH, return_value=[])

    search.process_search(
        api_client,
        "test-api-key",
        [ContractEntry("75N98027F00001", "75N91023A00006", "NIH EAMSS", "AWARD")],
        [],
    )

    criteria = mock_search.call_args.args[3]
    assert criteria == {"contract_no": "75N98027F00001", "idv_no": "75N91023A00006"}


def settings() -> Settings:
    return Settings(
        sam_api_key="test-api-key",
        contracts=(ContractEntry("123", "", "Test", "AWARD"),),
        naics=(),
        ms_webhook_url="https://webhook.example.com",
    )


def test_main(mocker):
    results = [{"index": 1, "contract_no": "123", "contract_details": []}]
    mocker.patch("sam_contract_alerts.search.process_search", return_value=results)
    mock_format = mocker.patch(
        "sam_contract_alerts.teams.format_results",
        return_value=[{"type": "TextBlock", "text": "Test"}],
    )
    mock_post = mocker.patch("sam_contract_alerts.teams.post")

    search.main(settings())

    mock_format.assert_called_once_with(results)
    mock_post.assert_called_once_with(
        "https://webhook.example.com", [{"type": "TextBlock", "text": "Test"}]
    )


def test_main_no_results(mocker):
    mocker.patch("sam_contract_alerts.search.process_search", return_value=[])
    mock_post = mocker.patch("sam_contract_alerts.teams.post")

    search.main(settings())

    mock_post.assert_not_called()
