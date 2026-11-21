"""
Tests for sam.py
"""

import pytest
import urllib3

import client
from client.rest import ApiException, RESTResponse
from sam_contract_alerts import sam

CRITERIA = {"contract_no": "TEST24F00001", "idv_no": ""}


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
        {"contract_no": "TEST27F00001", "idv_no": "TEST23A00006"},
    )

    kwargs = mock_search.call_args.kwargs
    assert kwargs["piid"] == "TEST27F00001"
    assert kwargs["referenced_idv_piid"] == "TEST23A00006"


def test_search_by_contract_no_without_idv_no(mocker, api_client):
    api_response = client.AwardResponse()
    api_response.award_summary = []

    mock_search = mocker.patch("client.SamApi.search", return_value=api_response)

    sam.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"contract_no": "TEST27F00001", "idv_no": ""},
    )

    kwargs = mock_search.call_args.kwargs
    assert kwargs["piid"] == "TEST27F00001"
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


def http_error(status: int, headers: dict | None = None) -> ApiException:
    response = urllib3.HTTPResponse(
        body=b"error", status=status, headers=headers or {}, preload_content=True
    )
    return ApiException(http_resp=RESTResponse(response))


def empty_response() -> client.AwardResponse:
    api_response = client.AwardResponse()
    api_response.award_summary = []
    return api_response


@pytest.fixture
def mock_sleep(mocker):
    mocker.patch("sam_contract_alerts.sam.random.uniform", return_value=0)
    return mocker.patch("sam_contract_alerts.sam.time.sleep")


def test_search_by_naics_sends_combined_codes(mocker, api_client, mock_sleep):
    mock_search = mocker.patch("client.SamApi.search", return_value=empty_response())

    sam.search(
        api_client,
        "test-api-key",
        "02/24/2024",
        {"naics": "541511~541512", "agency": "Test Agency"},
    )

    kwargs = mock_search.call_args.kwargs
    assert kwargs["naics_code"] == "541511~541512"
    assert kwargs["limit"] == 100
    assert kwargs["_request_timeout"] == sam.REQUEST_TIMEOUT


def test_search_retries_504_then_succeeds(mocker, api_client, mock_sleep):
    mock_search = mocker.patch(
        "client.SamApi.search", side_effect=[http_error(504), empty_response()]
    )

    result = sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert result == []
    assert mock_search.call_count == 2
    # Backoff before the retry, then the usual pause after a successful search
    assert [c.args[0] for c in mock_sleep.call_args_list] == [10, 4]


def test_search_gives_up_after_two_retries(mocker, api_client, mock_sleep):
    mock_search = mocker.patch(
        "client.SamApi.search", side_effect=[http_error(504)] * 3
    )

    with pytest.raises(sam.SamSearchError) as error:
        sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert error.value.status == 504
    # Gateway Timeout is the standard reason, used since the response has none
    assert error.value.reason == "Gateway Timeout"
    assert str(error.value) == (
        "SAM.gov search for contract failed (504), attempt 3 of 3"
    )
    # The original error, which includes the request URL, isn't attached
    assert error.value.__cause__ is None
    assert error.value.__suppress_context__
    assert mock_search.call_count == 3
    assert [c.args[0] for c in mock_sleep.call_args_list] == [10, 30]


@pytest.mark.parametrize("status", [400, 403])
def test_search_does_not_retry_client_errors(mocker, api_client, mock_sleep, status):
    mock_search = mocker.patch("client.SamApi.search", side_effect=http_error(status))

    with pytest.raises(sam.SamSearchError):
        sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert mock_search.call_count == 1
    mock_sleep.assert_not_called()


def test_search_honors_retry_after_on_429(mocker, api_client, mock_sleep):
    mocker.patch(
        "client.SamApi.search",
        side_effect=[http_error(429, {"Retry-After": "45"}), empty_response()],
    )

    sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert mock_sleep.call_args_list[0].args[0] == 45


def test_search_caps_long_retry_after(mocker, api_client, mock_sleep):
    mocker.patch(
        "client.SamApi.search",
        side_effect=[http_error(429, {"Retry-After": "3600"}), empty_response()],
    )

    sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert mock_sleep.call_args_list[0].args[0] == sam.MAX_RETRY_AFTER


@pytest.mark.parametrize(
    "error",
    [
        urllib3.exceptions.ReadTimeoutError(
            urllib3.HTTPSConnectionPool("api.sam.gov"), "/search", "Read timed out"
        ),
        urllib3.exceptions.ProtocolError("Connection aborted"),
    ],
)
def test_search_retries_timeouts_and_connection_errors(
    mocker, api_client, mock_sleep, error
):
    mock_search = mocker.patch(
        "client.SamApi.search", side_effect=[error, empty_response()]
    )

    sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert mock_search.call_count == 2


def test_search_rejects_unknown_criteria(api_client, mock_sleep):
    with pytest.raises(ValueError):
        sam.search(api_client, "test-api-key", "02/24/2024", {"unknown": "x"})


def test_search_error_keeps_http_reason(mocker, api_client, mock_sleep):
    error = ApiException(status=403, reason="Forbidden")
    mocker.patch("client.SamApi.search", side_effect=error)

    with pytest.raises(sam.SamSearchError) as raised:
        sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert (raised.value.status, raised.value.reason) == (403, "Forbidden")


def test_search_error_has_no_reason_without_http_response(
    mocker, api_client, mock_sleep
):
    timeout = urllib3.exceptions.ReadTimeoutError(
        urllib3.HTTPSConnectionPool("api.sam.gov"), "/search", "Read timed out"
    )
    mocker.patch("client.SamApi.search", side_effect=[timeout] * 3)

    with pytest.raises(sam.SamSearchError) as raised:
        sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert raised.value.status == "ReadTimeoutError"
    assert raised.value.reason is None


def test_describe_leaves_out_identifiers():
    assert sam.describe(CRITERIA) == "contract"
    assert sam.describe({"parent_contract_no": "IDV1"}) == "IDV child awards"
    assert sam.describe({"naics": "541511~541512", "agency": "TA"}) == "NAICS"


def test_retry_logs_leave_out_contract_numbers(mocker, api_client, mock_sleep, caplog):
    mocker.patch("client.SamApi.search", side_effect=[http_error(504)] * 3)

    with caplog.at_level("INFO"), pytest.raises(sam.SamSearchError):
        sam.search(api_client, "test-api-key", "02/24/2024", CRITERIA)

    assert caplog.messages[0] == (
        "SAM.gov search for contract failed (504), attempt 1 of 3. Retrying in 10s"
    )
    assert not any("TEST24F00001" in message for message in caplog.messages)
