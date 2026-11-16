"""
Tests for config.py
"""

import pytest

from sam_contract_alerts import config
from sam_contract_alerts.config import ContractEntry, NaicsEntry, Settings


def test_parse_contract_list():
    result = config.parse_contract_list(
        "123456789:My Contract:IDV,"
        " 75N98027F00001 : 75N91023A00006 : NIH EAMSS (Unissant) : AWARD,"
        "098765432::Empty IDV:AWARD"
    )

    assert result == [
        ContractEntry("123456789", "", "My Contract", "IDV"),
        ContractEntry(
            "75N98027F00001", "75N91023A00006", "NIH EAMSS (Unissant)", "AWARD"
        ),
        ContractEntry("098765432", "", "Empty IDV", "AWARD"),
    ]


def test_parse_contract_list_invalid():
    with pytest.raises(ValueError):
        config.parse_contract_list("123456789:AWARD")


def test_parse_contract_list_empty():
    assert config.parse_contract_list("") == []
    assert config.parse_contract_list("  ") == []


def test_parse_naics_list():
    entries = config.parse_naics_list(
        "Test Agency:TA:[541512-541511], Other Agency : OA : [ 541512 ]"
    )

    assert entries == [
        NaicsEntry("Test Agency", "TA", ("541512", "541511")),
        NaicsEntry("Other Agency", "OA", ("541512",)),
    ]


def test_parse_naics_list_empty():
    assert config.parse_naics_list("") == []


def test_settings_from_env():
    settings = Settings.from_env(
        {
            "SAM_API_KEY": "key",
            "CONTRACT_LIST": "75N98027F00001:75N91023A00006:NIH EAMSS:AWARD",
            "NAICS_LIST": "Test Agency:TA:[541512]",
            "MS_URL": "https://webhook.example.com",
            "DAYS": "3",
        }
    )

    assert settings == Settings(
        sam_api_key="key",
        contracts=(
            ContractEntry("75N98027F00001", "75N91023A00006", "NIH EAMSS", "AWARD"),
        ),
        naics=(NaicsEntry("Test Agency", "TA", ("541512",)),),
        ms_webhook_url="https://webhook.example.com",
        days=3,
    )


def test_settings_from_env_defaults():
    settings = Settings.from_env(
        {
            "SAM_API_KEY": "key",
            "CONTRACT_LIST": "",
            "NAICS_LIST": "",
            "MS_URL": "https://webhook.example.com",
        }
    )

    assert settings.contracts == ()
    assert settings.naics == ()
    assert settings.days == 1


def test_settings_from_env_rejects_bad_contract_entry():
    with pytest.raises(ValueError):
        Settings.from_env(
            {
                "SAM_API_KEY": "key",
                "CONTRACT_LIST": "123456789:AWARD",
                "NAICS_LIST": "",
                "MS_URL": "https://webhook.example.com",
            }
        )
