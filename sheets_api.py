import os
import logging
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class SheetsAPI:
    """Manages Google Sheets integration for click logging."""
    
    def __init__(self):
        """Initialize Google Sheets API client."""
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.service = None
        self.token_sheet = 'Tokens'
        self.clicks_sheet = 'Clicks'
        
        # Initialize sheets
        self._authenticate()
        self._initialize_sheets()
    
    def _authenticate(self):
        """
        Authenticate with Google Sheets API.
        """
        try:
            creds = None
            
            # Load existing credentials
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # Refresh or create new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info('Successfully authenticated with Google Sheets API')
        
        except FileNotFoundError:
            logger.error(f'Credentials file not found: {self.credentials_file}')
            raise
        except Exception as e:
            logger.error(f'Authentication error: {str(e)}')
            raise
    
    def _initialize_sheets(self):
        """
        Initialize required sheets and headers.
        """
        try:
            # Get current sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [sheet['properties']['title'] 
                             for sheet in spreadsheet.get('sheets', [])]
            
            # Create Tokens sheet if it doesn't exist
            if self.token_sheet not in existing_sheets:
                self._create_sheet(self.token_sheet)
                self._set_sheet_headers(self.token_sheet, [
                    'Timestamp', 'Token', 'Target URL', 'Email', 'Campaign', 'Status'
                ])
            
            # Create Clicks sheet if it doesn't exist
            if self.clicks_sheet not in existing_sheets:
                self._create_sheet(self.clicks_sheet)
                self._set_sheet_headers(self.clicks_sheet, [
                    'Timestamp', 'Token', 'IP Address', 'User Agent', 'Click Count'
                ])
            
            logger.info('Sheets initialized successfully')
        
        except HttpError as e:
            logger.error(f'Error initializing sheets: {str(e)}')
            raise
    
    def _create_sheet(self, title):
        """
        Create a new sheet in the spreadsheet.
        
        Args:
            title: Sheet title
        """
        try:
            request = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={
                    'requests': [{
                        'addSheet': {'properties': {'title': title}}
                    }]
                }
            )
            request.execute()
            logger.info(f'Created sheet: {title}')
        except Exception as e:
            logger.error(f'Error creating sheet {title}: {str(e)}')
            raise
    
    def _set_sheet_headers(self, sheet_name, headers):
        """
        Set headers for a sheet.
        
        Args:
            sheet_name: Name of the sheet
            headers: List of header strings
        """
        try:
            range_name = f'{sheet_name}!A1:Z1'
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            logger.info(f'Set headers for sheet: {sheet_name}')
        except Exception as e:
            logger.error(f'Error setting headers: {str(e)}')
    
    def log_token_creation(self, token, target_url, email, campaign):
        """
        Log token creation to Tokens sheet.
        
        Args:
            token: Tracking token
            target_url: Target URL
            email: Email address
            campaign: Campaign name
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            values = [[
                timestamp,
                token,
                target_url,
                email or 'N/A',
                campaign,
                'Active'
            ]]
            
            range_name = f'{self.token_sheet}!A:F'
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            
            logger.info(f'Logged token creation: {token}')
        
        except HttpError as e:
            logger.error(f'Error logging token creation: {str(e)}')
    
    def log_click(self, token, ip_address, user_agent, timestamp, target_url):
        """
        Log click to Clicks sheet.
        
        Args:
            token: Tracking token
            ip_address: IP address of clicker
            user_agent: User agent of clicker
            timestamp: Click timestamp
            target_url: Target URL
        """
        try:
            values = [[
                timestamp,
                token,
                ip_address,
                user_agent[:100],  # Truncate for readability
                1
            ]]
            
            range_name = f'{self.clicks_sheet}!A:E'
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            
            logger.info(f'Logged click for token: {token}')
        
        except HttpError as e:
            logger.error(f'Error logging click: {str(e)}')
    
    def get_click_stats(self, token):
        """
        Get click statistics for a token from Clicks sheet.
        
        Args:
            token: Tracking token
        
        Returns:
            Dictionary with statistics or None if token not found
        """
        try:
            # Read all clicks
            range_name = f'{self.clicks_sheet}!A:E'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Skip header and filter by token
            clicks = [row for row in values[1:] if len(row) > 1 and row[1] == token]
            
            if not clicks:
                return None
            
            # Calculate statistics
            total_clicks = len(clicks)
            unique_ips = len(set(click[2] for click in clicks if len(click) > 2))
            
            clicks_by_date = {}
            for click in clicks:
                if len(click) > 0:
                    date = click[0].split('T')[0]
                    clicks_by_date[date] = clicks_by_date.get(date, 0) + 1
            
            clicks_by_user_agent = {}
            for click in clicks:
                if len(click) > 3:
                    ua = click[3][:50]
                    clicks_by_user_agent[ua] = clicks_by_user_agent.get(ua, 0) + 1
            
            return {
                'total_clicks': total_clicks,
                'unique_ips': unique_ips,
                'clicks_by_date': clicks_by_date,
                'clicks_by_user_agent': clicks_by_user_agent
            }
        
        except Exception as e:
            logger.error(f'Error getting click stats: {str(e)}')
            return None
    
    def check_connection(self):
        """
        Check if connection to Google Sheets is active.
        
        Returns:
            True if connected, raises exception otherwise
        """
        try:
            self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f'Connection check failed: {str(e)}')
            raise
