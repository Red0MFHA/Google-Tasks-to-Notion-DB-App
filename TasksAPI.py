import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configurable variables
CLIENT_SECRET_FILE = "client_secret_file.json"
API_NAME = "tasks"
API_VERSION = "v1"
SCOPES = ["https://www.googleapis.com/auth/tasks"]

def create_service():
    """Handles Google OAuth2 and returns an authorized service object."""
    creds = None

    # Load saved token if it exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid credentials, request login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save for future runs
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Build and return the Google Tasks service
    return build(API_NAME, API_VERSION, credentials=creds)

# If you run this file directly, it will test the auth
if __name__ == "__main__":
    service = create_service()
    print("✅ Service created successfully")
