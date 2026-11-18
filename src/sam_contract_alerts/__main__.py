"""
Entry point: read settings from the environment and run the search.
"""

import logging

from sam_contract_alerts import search
from sam_contract_alerts.config import Settings


def run() -> None:
    logging.basicConfig(level=logging.INFO)

    for name in ("urllib3.connectionpool", "urllib3.poolmanager", "urllib3.util"):
        logging.getLogger(name).setLevel(logging.ERROR)
    search.main(Settings.from_env())


if __name__ == "__main__":
    run()
