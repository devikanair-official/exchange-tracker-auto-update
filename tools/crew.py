import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import JinaReaderTool, FileReadTool
from tools import ExcelWritebackTool, SharePointUploadTool
from dotenv import load_dotenv

load_dotenv()

# ── Tools ─────────────────────────────────────────────────────────────────────
jina_tool         = JinaReaderTool()
file_read_tool    = FileReadTool()
excel_tool        = ExcelWritebackTool()
sharepoint_tool   = SharePointUploadTool()

# ── Agents ────────────────────────────────────────────────────────────────────
volume_fetcher = Agent(
    role="Exchange Volume & ADV Data Specialist",
    goal=(
        "Fetch current Platform ADV and Our Volume ($M/day) for all exchanges "
        "in the tracker using public APIs such as CoinGecko and Binance."
    ),
    backstory=(
        "You are an expert in cryptocurrency market data. You know exactly which "
        "public API endpoints to call for each major exchange to get accurate, "
        "up-to-date volume and ADV figures. You always return clean, structured JSON."
    ),
    tools=[jina_tool],
    verbose=True,
)

jira_fetcher = Agent(
    role="Jira Project Tracker Specialist",
    goal=(
        "Query the Jira project {jira_project_key} to retrieve the latest "
        "migration status and ETA for each exchange."
    ),
    backstory=(
        "You are a project management expert with deep experience in Jira. "
        "You write precise JQL queries to extract migration ticket data and "
        "always return structured, clean JSON output per exchange."
    ),
    tools=[],  # Jira tools added via CrewAI Studio integration
    verbose=True,
)

reconciler = Agent(
    role="Data Reconciliation & Change Detection Analyst",
    goal=(
        "Compare fresh API and Jira data against the current tracker at {tracker_path}, "
        "identify all changed fields, and flag exchanges where volume shifted >15%."
    ),
    backstory=(
        "You are a meticulous data analyst who excels at diffing datasets. "
        "You read the existing tracker, compare it field-by-field against new data, "
        "and produce a precise update payload — never including unchanged values."
    ),
    tools=[file_read_tool],
    verbose=True,
)

writeback_agent = Agent(
    role="Excel & SharePoint Update Specialist",
    goal=(
        "Apply reconciled updates to the local Excel tracker at {tracker_path} "
        "and sync the file to SharePoint at {sharepoint_folder_url}."
    ),
    backstory=(
        "You are an automation engineer specialising in Excel and SharePoint. "
        "You apply only the approved auto-safe fields and never touch human-owned "
        "columns such as Risk Notes, Priority Tier, or Notes/Actions."
    ),
    tools=[excel_tool, sharepoint_tool],
    verbose=True,
)

# ── Tasks ─────────────────────────────────────────────────────────────────────
fetch_volume_task = Task(
    name="Fetch Volume & ADV Data",
    description=(
        "Call the CoinGecko /exchanges endpoint (https://api.coingecko.com/api/v3/exchanges) "
        "and Binance ticker API (https://api.binance.com/api/v3/ticker/24hr) to retrieve "
        "Platform ADV and Our Volume ($M/day) for all exchanges in the tracker. "
        "Return a JSON list with fields: exchange_name, platform_adv_usd_m, our_volume_usd_m_day."
    ),
    expected_output=(
        "A JSON list of objects, one per exchange, each containing: "
        "exchange_name (string), platform_adv_usd_m (float), our_volume_usd_m_day (float)."
    ),
    agent=volume_fetcher,
)

fetch_jira_task = Task(
    name="Fetch Jira Migration Status",
    description=(
        "Use JQL to query all issues in Jira project {jira_project_key}. "
        "For each exchange, extract: exchange_name, migration_status "
        "(one of: Scoping / In Planning / Planned / Complete), and eta_date (YYYY-MM-DD). "
        "Return a structured JSON list."
    ),
    expected_output=(
        "A JSON list of objects, one per exchange, each containing: "
        "exchange_name (string), migration_status (string), eta_date (string YYYY-MM-DD or null)."
    ),
    agent=jira_fetcher,
)

reconcile_task = Task(
    name="Reconcile & Detect Changes",
    description=(
        "Read the current tracker file at {tracker_path} using the file read tool. "
        "Compare existing values against the new volume/ADV and Jira status data. "
        "Produce a JSON update payload containing ONLY changed fields. "
        "Flag any exchange where volume changed by more than 15% as a significant alert."
    ),
    expected_output=(
        "A JSON object with two keys:\n"
        "  'updates': list of {exchange, field, value} objects for changed fields only.\n"
        "  'alerts': list of exchange names where volume shifted >15%, with old and new values."
    ),
    agent=reconciler,
    context=[fetch_volume_task, fetch_jira_task],
)

writeback_task = Task(
    name="Write Updates to Tracker",
    description=(
        "Using the reconciled update payload, apply all changes to the Excel tracker at {tracker_path}. "
        "Only update these auto-safe fields: Platform ADV, Our Volume, Migration Status, ETA. "
        "NEVER modify: Risk Notes, Priority Tier, Notes/Actions. "
        "After saving locally, upload the updated file to SharePoint at {sharepoint_folder_url}. "
        "Produce a final summary report of all fields updated, alerts raised, and upload status."
    ),
    expected_output=(
        "A markdown summary report containing:\n"
        "1. List of all fields updated (exchange → field → new value)\n"
        "2. List of volume alerts (>15% change)\n"
        "3. SharePoint upload confirmation or error message."
    ),
    agent=writeback_agent,
    context=[reconcile_task],
)

# ── Crew ──────────────────────────────────────────────────────────────────────
crew = Crew(
    agents=[volume_fetcher, jira_fetcher, reconciler, writeback_agent],
    tasks=[fetch_volume_task, fetch_jira_task, reconcile_task, writeback_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    result = crew.kickoff(inputs={
        "tracker_path":         os.getenv("TRACKER_PATH", "data/Exchange_Migration_Tracker.xlsx"),
        "sharepoint_folder_url": os.getenv("SHAREPOINT_FILE_PATH", "/ExchangeTracker/"),
        "jira_project_key":     os.getenv("JIRA_PROJECT_KEY", "MIGR"),
    })
    print("\n\n════════════════ FINAL REPORT ════════════════")
    print(result)
