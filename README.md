# SAM.gov contract awards search and post to a chat channel
[![sam-contract-alerts-build](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-build.yaml/badge.svg)](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-build.yaml) [![sam-contract-alerts-run](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-run.yaml/badge.svg)](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-run.yaml)

GitHub Actions workflows and Python client to search government contract awards from SAM.gov API for the prior day: https://open.gsa.gov/api/contract-awards. 

[sam-contract-alerts-run](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-run.yaml) pulls contract updates for specified contracts and NAICS/agencies each day and posts them to MS Teams, Slack, or both. To run this you must obtain and configure as actions repo secrets:

| Name | Value |
| ---- | ----- |
|`SAM_API_KEY`| SAM.gov API key for Contract Awards API access, created and tied to your SAM profile |
|`CONTRACT_LIST`| A comma separated string of contract numbers, an optional parent IDV number, contract names, and type (IDV or AWARD).<br><br> `123456789:My Contract:IDV,098765432:Your Contract:AWARD,9732497839:9275982759823:Their Contract:AWARD`<br><br>For IDV contracts (BPAs, IDIQs), the search will find both parent IDV updates and child awards. For AWARD contracts, only the specific award will be searched. Order numbers are only unique within their parent IDV, so the same number can match unrelated orders. Include the parent IDV number to limit the search to orders under that IDV.|
|`NAICS_LIST`| A comma separated string of agency names, abbr, and a bracketed, dash separated list of NAICS codes.<br><br>`THE AGENCY NAME:ABBR:[541511-541512],OTHER AGENCY NAME:ABBR2:[541512]`<br><br>Use the full contracting subtier name (e.g., U.S. AGENCY OF SOMETHING). Each NAICS code is searched separately and results are combined into one table per agency. |
| `MS_URL`| MS Teams webhook URL. More info on setting up Teams webhooks: [Create incoming webhooks with Workflows for Microsoft Teams](https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498)|
| `SLACK_URL`| Slack incoming webhook URL. Create a new app and webhook at [api.slack.com/apps](https://api.slack.com/apps).|

Set `MS_URL`, `SLACK_URL`, or both. Results are posted to every channel that has a URL, and the run fails at startup if neither is set.

> [!CAUTION]
> `SAM_API_KEY`, `MS_URL` and `SLACK_URL` are sensitive values. Store them only as GitHub Actions repository secrets. Never commit them, paste them into issues, pull requests, logs, etc. Secrets are not copied when the repo is forked or cloned. Each organization must create its own key and webhooks. If any of them is exposed, rotate it right away. 

## Chat channels:
Posting is handled by one module per chat tool, each called from `main` in [search.py](src/sam_contract_alerts/search.py):
- [teams.py](src/sam_contract_alerts/teams.py) builds an MS Teams Adaptive Card.
- [slack.py](src/sam_contract_alerts/slack.py) posts the same content as Slack `table` blocks.

## Sample output:
```
COMPANY NAME | 09/15/2026 | Contract no.
$100,000.00 delivery order | To Date: $100,000.00 | TCV: $100,000.00
Contract Start: 09/15/2026 | PoP End: 10/30/2026 | Contract End: 10/30/2026
DESCRIPTION.
1 offer received. Small business set aside - total.
```
The company name and contract number link to SAM.gov.

## Local execution:

Python 3.13+ required. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (`brew install uv`) and sync dependencies:
```bash
uv sync --dev
```

Lint:
```bash
uv run ruff check .
uv run ruff format --check .
```

Git hook (auto-formats Python files on commit):
```bash
git config core.hooksPath hooks
```

Type check:
```bash
uv run ty check
```

Tests:
```bash
uv run pytest
```

Execute (put the settings in a gitignored `.env` file so secrets stay out of your shell history):
```bash
# .env
SAM_API_KEY='my-sam-api-key'
CONTRACT_LIST='my-contract-list'
NAICS_LIST='my-naics-list'
MS_URL='my-ms-webhook-url'
SLACK_URL='my-slack-webhook-url'
```
```bash
uv run --env-file .env sam-contract-alerts
```
