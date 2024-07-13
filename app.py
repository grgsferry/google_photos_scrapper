import os
import pickle
import logging
import signal
import sys
import csv
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

# Function to handle termination signals
def signal_handler(sig, frame):
    logger.info('Exiting gracefully...')
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def authenticate():
    """Handles authentication and returns credentials."""
    creds = None
    token_path = 'token.pickle'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=55240)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def list_google_photos_files(output_csv):
    """Lists the filenames in Google Photos and saves them to a CSV file."""
    creds = authenticate()
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

    try:
        all_items = []
        next_page_token = None

        while True:
            # Request to fetch media items
            request = service.mediaItems().list(pageSize=100, pageToken=next_page_token)
            response = request.execute()

            # Append current page of items to the list
            items = response.get('mediaItems', [])
            all_items.extend(items)

            # Check if there is another page to fetch
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break  # No more pages to fetch

        if not all_items:
            logger.info('No media items found.')
        else:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(['Filename'])  # Write header

                for item in all_items:
                    csv_writer.writerow([item['filename']])
                    logger.info(f"Saved filename: {item['filename']}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    try:
        output_csv_file = 'google_photos_filenames.csv'
        list_google_photos_files(output_csv_file)
    except KeyboardInterrupt:
        logger.info('Interrupted by user, exiting...')
        sys.exit(0)