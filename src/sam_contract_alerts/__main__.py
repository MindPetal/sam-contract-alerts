"""
Entry point: read settings from the environment and run the search.
"""

import logging

from sam_contract_alerts import search
from sam_contract_alerts.config import Settings


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    search.main(Settings.from_env())


if __name__ == "__main__":
    run()
