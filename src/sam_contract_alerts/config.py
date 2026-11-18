"""
Parse run settings and the contract / NAICS input lists.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ContractEntry:
    contract_no: str
    idv_no: str
    name: str
    type: str


@dataclass(frozen=True)
class NaicsEntry:
    agency: str
    abbr: str
    naics_codes: tuple[str, ...]


@dataclass(frozen=True)
class Settings:
    sam_api_key: str
    contracts: tuple[ContractEntry, ...]
    naics: tuple[NaicsEntry, ...]
    ms_webhook_url: str
    days: int = 1
    slack_webhook_url: str = ""

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        """
        Read SAM_API_KEY, CONTRACT_LIST, NAICS_LIST, optional DAYS, and at least
        one of MS_URL / SLACK_URL
        """
        ms_webhook_url, slack_webhook_url = read_webhook_urls(env)

        return cls(
            sam_api_key=env["SAM_API_KEY"],
            contracts=tuple(parse_contract_list(env["CONTRACT_LIST"])),
            naics=tuple(parse_naics_list(env["NAICS_LIST"])),
            ms_webhook_url=ms_webhook_url,
            days=int(env.get("DAYS", "1")),
            slack_webhook_url=slack_webhook_url,
        )


def read_webhook_urls(env: Mapping[str, str]) -> tuple[str, str]:
    """
    Read the MS Teams and Slack webhook URLs. Either may be blank, but not both.
    """
    ms_webhook_url = env.get("MS_URL", "").strip()
    slack_webhook_url = env.get("SLACK_URL", "").strip()

    if not ms_webhook_url and not slack_webhook_url:
        raise ValueError("Set MS_URL, SLACK_URL, or both")

    return ms_webhook_url, slack_webhook_url


def parse_contract_list(contract_list: str) -> list[ContractEntry]:
    """
    Parse 'NO:NAME:TYPE' or 'NO:IDV_NO:NAME:TYPE' entries. IDV no is "" when
    omitted.
    """
    entries = []

    if not contract_list.strip():
        return entries

    for position, entry in enumerate(contract_list.split(","), start=1):
        parts = [part.strip() for part in entry.split(":")]

        if len(parts) == 4:
            contract_no, idv_no, contract_nm, contract_type = parts
        elif len(parts) == 3:
            contract_no, contract_nm, contract_type = parts
            idv_no = ""
        else:
            # Identify the entry by position.
            raise ValueError(
                f"Invalid CONTRACT_LIST entry #{position}: expected "
                "NO:NAME:TYPE or NO:IDV_NO:NAME:TYPE"
            )

        entries.append(ContractEntry(contract_no, idv_no, contract_nm, contract_type))

    return entries


def parse_naics_list(naics_list: str) -> list[NaicsEntry]:
    """
    Parse 'AGENCY NAME:ABBR:[NAICS-NAICS],...' entries
    """
    entries = []

    if not naics_list.strip():
        return entries

    for entry in naics_list.split(","):
        agency, abbr, codes = entry.rsplit(":", 2)
        codes = codes.strip().removeprefix("[").removesuffix("]")
        naics_codes = tuple(code.strip() for code in codes.split("-") if code.strip())
        entries.append(NaicsEntry(agency.strip(), abbr.strip(), naics_codes))

    return entries
