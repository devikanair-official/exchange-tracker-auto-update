import os
import sys
from dotenv import load_dotenv

load_dotenv()

def validate_env():
    """Check all required environment variables are set before running."""
    required = {
        "OPENAI_API_KEY":      "OpenAI API key for the AI agents",
        "JIRA_SERVER":         "Your Jira server URL (e.g. https://company.atlassian.net)",
        "JIRA_EMAIL":          "Your Jira account email",
        "JIRA_API_TOKEN":      "Your Jira API token",
        "MS_GRAPH_TOKEN":      "Microsoft Graph bearer token for SharePoint upload",
        "SHAREPOINT_SITE_ID":  "SharePoint site ID",
        "SHAREPOINT_DRIVE_ID": "SharePoint drive ID",
        "TRACKER_PATH":        "Local path to the Excel tracker file",
        "JIRA_PROJECT_KEY":    "Jira project key for migration tickets",
    }

    missing = []
    for var, description in required.items():
        if not os.getenv(var):
            missing.append(f"  ❌  {var:<30} — {description}")

    if missing:
        print("\n⚠️  Missing required environment variables:\n")
        print("\n".join(missing))
        print("\n👉  Copy .env.example to .env and fill in the values, then try again.\n")
        sys.exit(1)

    print("✅  All environment variables validated.\n")


def main():
    print("═" * 60)
    print("   Exchange Migration Tracker — Auto-Update Crew")
    print("═" * 60)

    validate_env()

    from crew import crew

    inputs = {
        "tracker_path":          os.getenv("TRACKER_PATH"),
        "sharepoint_folder_url": os.getenv("SHAREPOINT_FILE_PATH"),
        "jira_project_key":      os.getenv("JIRA_PROJECT_KEY"),
    }

    print("🚀  Starting crew with inputs:")
    for k, v in inputs.items():
        print(f"    {k}: {v}")
    print()

    result = crew.kickoff(inputs=inputs)

    print("\n" + "═" * 60)
    print("   FINAL REPORT")
    print("═" * 60)
    print(result)


if __name__ == "__main__":
    main()
