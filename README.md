# Exchange Migration Tracker — Auto-Update Crew

An AI-powered nightly automation that:
- Fetches live volume & ADV data from public exchange APIs (CoinGecko, Binance)
- Pulls migration status & ETA from your Jira project
- Detects changes vs. the current tracker (flags >15% volume swings)
- Writes updates back to the local Excel file and syncs to SharePoint/OneDrive

> ⚠️ Only **auto-safe fields** are ever written: `Platform ADV`, `Our Volume`, `Migration Status`, `ETA`.  
> Human-owned columns (`Risk Notes`, `Priority Tier`, `Notes/Actions`) are **never touched**.

---

## 📋 Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | [Download](https://www.python.org/downloads/) |
| OpenAI API key | [Get one](https://platform.openai.com/api-keys) |
| Jira API token | [Generate here](https://id.atlassian.com/manage-profile/security/api-tokens) |
| Microsoft Graph token | For SharePoint upload — see setup below |
| Excel tracker file | Place in `data/` folder |

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/devikanair-official/exchange-tracker-auto-update.git
cd exchange-tracker-auto-update
2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables
cp .env.example .env
Open .env and fill in all values (see table below).

5. Place your tracker file
mkdir -p data
cp /path/to/Exchange_Migration_Tracker.xlsx data/
🔑 Environment Variables
Variable	Description
OPENAI_API_KEY	OpenAI API key
JIRA_SERVER	e.g. https://company.atlassian.net
JIRA_EMAIL	Your Jira account email
JIRA_API_TOKEN	Your Jira API token
MS_GRAPH_TOKEN	Microsoft Graph bearer token
SHAREPOINT_SITE_ID	SharePoint site ID
SHAREPOINT_DRIVE_ID	SharePoint drive ID
SHAREPOINT_FILE_PATH	Remote path e.g. /ExchangeTracker/Exchange_Migration_Tracker.xlsx
TRACKER_PATH	Local path e.g. data/Exchange_Migration_Tracker.xlsx
JIRA_PROJECT_KEY	Jira project key e.g. MIGR
Getting your Microsoft Graph token
Go to Graph Explorer
Sign in with your Microsoft account
Copy the Access Token from the top right
Paste it as MS_GRAPH_TOKEN in your .env
Note: Graph Explorer tokens expire after 1 hour. For production, set up an Azure App Registration with Files.ReadWrite permission for a long-lived token.

▶️ Running the Crew
python main.py
The crew will validate your environment variables, then run all 4 agents sequentially and print a final markdown report.

⏰ Nightly Schedule (GitHub Actions)
To run automatically every night at 2:00 AM UTC:

Go to your repo → Settings → Secrets and variables → Actions
Add each variable from the table above as a Repository Secret
Create .github/workflows/nightly.yml:
name: Nightly Tracker Update

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  update-tracker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          OPENAI_API_KEY:      ${{ secrets.OPENAI_API_KEY }}
          JIRA_SERVER:         ${{ secrets.JIRA_SERVER }}
          JIRA_EMAIL:          ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN:      ${{ secrets.JIRA_API_TOKEN }}
          MS_GRAPH_TOKEN:      ${{ secrets.MS_GRAPH_TOKEN }}
          SHAREPOINT_SITE_ID:  ${{ secrets.SHAREPOINT_SITE_ID }}
          SHAREPOINT_DRIVE_ID: ${{ secrets.SHAREPOINT_DRIVE_ID }}
          SHAREPOINT_FILE_PATH: ${{ secrets.SHAREPOINT_FILE_PATH }}
          TRACKER_PATH:        data/Exchange_Migration_Tracker.xlsx
          JIRA_PROJECT_KEY:    ${{ secrets.JIRA_PROJECT_KEY }}
