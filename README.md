# SAM.gov contract awards search and post to MS Teams
[![sam-contract-alerts-build](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-build.yaml/badge.svg)](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-build.yaml) [![sam-contract-alerts-run](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-run.yaml/badge.svg)](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-run.yaml)

Python client to search government contract awards from SAM.gov API for the prior day: https://open.gsa.gov/api/contract-awards/

The [sam-contract-alerts-run](https://github.com/MindPetal/sam-contract-alerts/actions/workflows/sam-contract-alerts-run.yaml) workflow pulls contract updates for specified contracts and NAICS/agencies each day and posts to a designated MS Teams channel. To run this you must obtain and configure as actions repo secrets:

| Name | Value |
| ---- | ----- |
|`SAM_API_KEY`| SAM.gov API key for Contract Awards API access, created and tied to your SAM profile |
|`CONTRACT_LIST`| A comma separated string of contract numbers, contract names, and type (IDV or AWARD). `123456789:My Contract:IDV,098765432:Your Contract:AWARD`. For IDV contracts (BPAs, IDIQs), the search will find both parent IDV updates and child awards. For AWARD contracts, only the specific award will be searched.|
|`NAICS_LIST`| A comma separated string of NAICS, agency names and abbr. `541512:THE+AGENCY+NAME:ABBR`. Use the full contracting subtier name (e.g., U.S.+AGENCY+OF+SOMETHING). |
| `MS_URL`| MS Teams webhook URL for your organization. More info on setting up Teams webhooks: [Create incoming webhooks with Workflows for Microsoft Teams](https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498)|

## Local execution:

Python 3.13+ required. Install:
```bash
pip3 install . --use-pep517
```

Tests:
```bash
pytest test_search.py
```

Execute: pass args:
```bash
python3 search.py 'my-sam-api-key' 'my-contract-list' 'my-naics-list' 'my-ms-webhook-url'
```
