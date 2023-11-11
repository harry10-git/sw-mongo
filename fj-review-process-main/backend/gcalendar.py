from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import settings

class CalendarAPI:
    def __init__(self, service_account: dict[str, str]):
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.creds = Credentials.from_service_account_info(service_account, scopes=SCOPES)

    def get_calendar(self, calendar_id: str = 'primary') -> dict:
        """Returns the calendar with the given calendar_id"""
        service = build('calendar', 'v3', credentials=self.creds)
        return service.calendars().get(calendarId=calendar_id).execute()

    def create_event(self, calendar_id: str, event: dict) -> dict:
        """Creates an event in the given calendar"""
        service = build('calendar', 'v3', credentials=self.creds)
        return service.events().insert(calendarId=calendar_id, body=event, conferenceDataVersion=1).execute()

    def create_review_meeting_event(
        self,
        summary: str,
        description: str,
        start_datetime: datetime,
        end_datetime: datetime,
        attendees: list[str],
        meeting_key: str
    ) -> dict:
        """Creates a new event for a review meeting"""
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'attendees': [
                {'email': attendee} for attendee in attendees
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': meeting_key,
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            },
            'guestsCanInviteOthers': True,
            'guestsCanModify': True,
            'guestsCanSeeOtherGuests': True,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        return self.create_event('primary', event)
    
cal = CalendarAPI(service_account=settings.CALENDAR_SERVICE_ACCOUNT)