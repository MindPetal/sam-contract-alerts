# SAM.gov Contract Awards search and post to MS Teams
Python client to search government contract awards from SAM.gov API for the prior day.

The workflow pulls contract updates for specified contracts and NAICS/agencies each day and posts to a designated MS Teams channel. To run this you must obtain and configure as actions repo secrets:
- SAM_API_KEY: SAM.gov API key for Contract Awards API access
- CONTRACT_LIST: A comma separated string of contract numbers, contract names, and type (IDV or AWARD)
```
   123456789:My Contract:IDV,098765432:Your Contract:AWARD
```
  For IDV contracts (BPAs, IDIQs), the search will find both parent IDV updates and child awards.
  For AWARD contracts, only the specific award will be searched.
- NAICS_LIST: A comma separated string of NAICS, agency names and abbr
```
   541512:THE+AGENCY+NAME:ABBR
```
  Note: Use the full contracting subtier name (e.g., "U.S. CITIZENSHIP AND IMMIGRATION SERVICES"), not the department name.
- MS_URL: MS Teams webhook URL for your organization.

More info on setting up Teams webhooks: [Create incoming webhooks with Workflows for Microsoft Teams](https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498)

## SAM.gov API Access

Register for a SAM.gov API key at: https://open.gsa.gov/api/contract-awards/

## Local execution:

- Python 3.13+ required.
- Install:

```sh
pip3 install . --use-pep517
```

- Tests:

```sh
pytest test_search.py
```

- Execute: pass SAM API key, contract list, naics list, ms teams webhook url:

```sh
python3 search.py my-sam-api-key my-contract-list my-naics-list my-ms-webhook-url
```
