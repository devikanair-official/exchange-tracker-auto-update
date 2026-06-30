import os
import requests
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SharePointUploadInput(BaseModel):
    tracker_path: str = Field(..., description="Local path to the updated Excel tracker file.")


class SharePointUploadTool(BaseTool):
    name: str = "SharePoint Upload Tool"
    description: str = (
        "Uploads the updated Excel tracker file to SharePoint/OneDrive "
        "using the Microsoft Graph API. Requires MS_GRAPH_TOKEN, "
        "SHAREPOINT_SITE_ID, SHAREPOINT_DRIVE_ID, and SHAREPOINT_FILE_PATH "
        "environment variables to be set."
    )
    args_schema: type[BaseModel] = SharePointUploadInput

    def _run(self, tracker_path: str) -> str:
        token       = os.getenv("MS_GRAPH_TOKEN")
        site_id     = os.getenv("SHAREPOINT_SITE_ID")
        drive_id    = os.getenv("SHAREPOINT_DRIVE_ID")
        remote_path = os.getenv("SHAREPOINT_FILE_PATH", "/ExchangeTracker/Exchange_Migration_Tracker.xlsx")

        if not all([token, site_id, drive_id]):
            return (
                "ERROR: Missing one or more environment variables: "
                "MS_GRAPH_TOKEN, SHAREPOINT_SITE_ID, SHAREPOINT_DRIVE_ID"
            )

        path = Path(tracker_path)
        if not path.exists():
            return f"ERROR: File not found at '{tracker_path}'"

        url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}"
            f"/drives/{drive_id}/root:{remote_path}:/content"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        with open(path, "rb") as f:
            response = requests.put(url, headers=headers, data=f)

        if response.status_code in (200, 201):
            return f"SUCCESS: Tracker uploaded to SharePoint at '{remote_path}'"
        else:
            return (
                f"ERROR: Upload failed — HTTP {response.status_code}\n"
                f"{response.text}"
            )
