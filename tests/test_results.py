"""
Tests for results.py
"""

from datetime import date, datetime

import pytest

from sam_contract_alerts import results


def test_format_competition_sole_source():
    result = results.format_competition("1", "NOT COMPETED", "NO SET ASIDE USED")

    assert result == "1 offer received. Not competed, no set aside used."


def test_format_competition_multiple_offers():
    result = results.format_competition(
        "5", "FULL AND OPEN COMPETITION", "SMALL BUSINESS SET ASIDE - TOTAL"
    )

    assert result == "5 offers received. Small business set aside - total."


def test_format_competition_omits_extent_unless_not_competed():
    result = results.format_competition(
        "5", "COMPETED UNDER SAP", "SMALL BUSINESS SET ASIDE - TOTAL"
    )

    assert result == "5 offers received. Small business set aside - total."


def test_format_competition_empty():
    assert results.format_competition("", "", "") == ""


def test_format_competition_offers_only():
    assert results.format_competition("3", "", "") == "3 offers received."


def test_format_competition_non_numeric_offers():
    result = results.format_competition("N/A", "NOT COMPETED", "NO SET ASIDE USED")

    assert result == "Not competed, no set aside used."


def test_format_competition_strips_trailing_period_in_source():
    result = results.format_competition("1", "NOT COMPETED", "NO SET ASIDE USED.")

    assert result == "1 offer received. Not competed, no set aside used."


def test_format_award_type():
    assert results.format_award_type("DELIVERY ORDER") == "delivery order"
    assert results.format_award_type("BPA CALL") == "BPA call"
    assert results.format_award_type("") == ""


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
            "competition_information": {
                "number_of_offers_received": "5",
            },
        },
        "core_data": {
            "award_or_idv_type": {"name": "DELIVERY ORDER"},
            "competition_information": {
                "extent_competed": {"name": "FULL AND OPEN COMPETITION"},
                "type_of_set_aside": {"name": "SMALL BUSINESS SET ASIDE - TOTAL"},
            },
        },
    }

    result = results.extract_contract_details(award_summary, now=datetime(2024, 2, 25))

    assert result["date"] == "02/25/2024"
    assert result["company"] == "Test Company"
    assert result["unique_entity_id"] == "SAMPLEUEI12345"
    assert result["obligation"] == "$50,000"
    assert result["total_obligated"] == "$86,974,480.71"
    assert result["total_value"] == "$170,000,000"
    assert result["reason"] == "Exercise an option"
    assert result["action"] == "Exercise an option: $50,000 delivery order"
    assert result["desc"] == "Test description\nwith newline"
    assert result["piid"] == "123456789"
    assert result["pop_start"] == "03/01/2024"
    assert result["pop_end_date"] == "06/30/2025"
    assert result["contract_end_date"] == "06/30/2026"
    assert (
        result["competition"] == "5 offers received. Small business set aside - total."
    )


def test_extract_contract_details_space_separated_date_signed():

    award_summary = {
        "contract_id": {"reason_for_modification": {}},
        "award_details": {
            "dates": {"date_signed": "2026-09-30 00:00:00"},
            "dollars": {},
            "total_contract_dollars": {},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Test Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {},
        },
    }

    result = results.extract_contract_details(award_summary)

    assert result["date"] == "09/30/2026"


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

    result = results.extract_contract_details(award_summary)

    assert result["company"] == "Test Company"
    assert result["unique_entity_id"] == ""
    assert result["total_obligated"] == ""
    assert result["pop_start"] == ""
    assert result["pop_end_date"] == ""
    assert result["contract_end_date"] == ""
    assert result["competition"] == ""


def test_extract_contract_details_omits_competition_for_existing_award():
    award_summary = {
        "contract_id": {"reason_for_modification": {}},
        "award_details": {
            "dates": {
                "date_signed": "2026-09-25T00:00:00Z",
                "period_of_performance_start_date": "2024-03-01 00:00:00.000",
            },
            "dollars": {},
            "total_contract_dollars": {},
            "awardee_data": {
                "awardee_header": {"awardee_name": "Test Company"},
                "awardee_location": {},
            },
            "product_or_service_information": {},
            "competition_information": {"number_of_offers_received": "5"},
        },
        "core_data": {
            "competition_information": {
                "extent_competed": {"name": "FULL AND OPEN COMPETITION"},
                "type_of_set_aside": {"name": "SMALL BUSINESS SET ASIDE - TOTAL"},
            },
        },
    }

    # Period of performance started more than a month ago, so this is an
    # update to an existing award and competition details are omitted.
    result = results.extract_contract_details(award_summary, now=datetime(2026, 9, 25))

    assert result["competition"] == ""


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

    result = results.extract_contract_details(award_summary)

    assert result["obligation"] == ""
    assert result["action"] == ""
    assert result["total_obligated"] == ""
    assert result["pop_start"] == ""
    assert result["pop_end_date"] == ""
    assert result["contract_end_date"] == ""


def award_with_pop_start(pop_start: str | None) -> dict:
    dates = {"date_signed": "2026-11-16T00:00:00Z"}
    if pop_start:
        dates["period_of_performance_start_date"] = f"{pop_start} 00:00:00.000"

    return {
        "contract_id": {"reason_for_modification": {}},
        "award_details": {
            "dates": dates,
            "dollars": {},
            "total_contract_dollars": {},
            "awardee_data": {"awardee_header": {"awardee_name": "Test Company"}},
            "product_or_service_information": {},
            "competition_information": {"number_of_offers_received": "2"},
        },
    }


@pytest.mark.parametrize(
    ("now", "pop_start", "shown"),
    [
        # One month back from 11/17/2026 is 10/17/2026
        (datetime(2026, 11, 17, 9, 30), "2026-10-17", True),
        (datetime(2026, 11, 17, 9, 30), "2026-10-16", False),
        (datetime(2026, 11, 17, 9, 30), "2026-11-16", True),
        # Future start dates are new awards
        (datetime(2026, 11, 17, 9, 30), "2027-01-01", True),
        # Unknown start date still shows competition
        (datetime(2026, 11, 17, 9, 30), None, True),
        # Calendar months: one month back from 03/31 is 02/28
        (datetime(2026, 3, 31), "2026-02-28", True),
        (datetime(2026, 3, 31), "2026-02-27", False),
    ],
)
def test_extract_contract_details_competition_window(now, pop_start, shown):
    result = results.extract_contract_details(award_with_pop_start(pop_start), now=now)

    assert result["competition"] == ("2 offers received." if shown else "")


DETAIL = {
    "date": "02/25/2024",
    "company": "TEST COMPANY LLC",
    "unique_entity_id": "TESTUEI00001",
    "action": "$50,000 delivery order",
    "total_obligated": "$86,974,480.71",
    "total_value": "$170,000,000",
    "desc": "Test description\nwith newline",
    "piid": "TEST24F00001",
    "pop_start": "03/01/2024",
    "pop_end_date": "06/30/2025",
    "contract_end_date": "06/30/2026",
    "competition": "1 offer received. Not competed, no set aside used.",
}


def test_build_detail_lines():
    lines = results.build_detail_lines(DETAIL)

    entity_url = results.build_entity_url("TESTUEI00001")
    search_url = results.build_search_url("TEST24F00001")
    assert lines == [
        f"[TEST COMPANY LLC]({entity_url}) | 02/25/2024 | [TEST24F00001]({search_url})",
        "$50,000 delivery order | **To Date:** $86,974,480.71 | **TCV:** $170,000,000",
        "**Contract Start:** 03/01/2024 | **PoP End:** 06/30/2025"
        " | **Contract End:** 06/30/2026",
        "Test description with newline",
        "1 offer received. Not competed, no set aside used.",
    ]


def test_build_detail_lines_skips_blank_parts_and_lines():
    detail = {
        **DETAIL,
        "unique_entity_id": "",
        "action": "",
        "desc": "  ",
        "competition": "",
    }

    lines = results.build_detail_lines(detail)

    assert lines[0].startswith("TEST COMPANY LLC | 02/25/2024 | [TEST24F00001](")
    assert lines[1] == "**To Date:** $86,974,480.71 | **TCV:** $170,000,000"
    assert lines[2].startswith("**Contract Start:** 03/01/2024")
    # No description or competition line
    assert len(lines) == 3


def test_build_detail_content_joins_lines():
    assert results.build_detail_content(DETAIL) == "\n".join(
        results.build_detail_lines(DETAIL)
    )


def test_build_search_url_contract_no():
    result = results.build_search_url("123456789")

    assert "123456789" in result
    assert "sam.gov" in result


def test_build_entity_url():
    result = results.build_entity_url("SAMPLEUEI12345")

    assert (
        result == "https://sam.gov/entities/view/SAMPLEUEI12345/coreData?status=Active"
    )


def test_header_text():
    today = date.today().strftime("%A, %m/%d/%Y")

    assert results.header_text() == f"**{today}.** Contract updates."


def test_result_heading():
    assert (
        results.result_heading({"contract_no": "123", "contract_nm": "My Contract"})
        == "**My Contract** - 123:"
    )
    assert results.result_heading({"agency": "TA"}) == "**TA** updates:"
