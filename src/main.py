import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont

# 1. Authenticate with Google Calendar
def get_calendar_events():
    # In GitHub Actions, we will load this from an environment variable
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict)
    else:
        # Fallback for local testing on your Mac
        creds = service_account.Credentials.from_service_account_file('credentials.json')
    
    service = build('calendar', 'v3', credentials=creds)
    
    now = datetime.utcnow().isoformat() + 'Z'
    # Get events for the next 7 days
    end_of_week = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
    
    # Replace 'primary' with your specific Calendar ID if needed
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          timeMax=end_of_week, singleEvents=True,
                                          orderBy='startTime').execute()
    return events_result.get('items', [])

# 2. Draw the Image
def generate_wallpaper(events):
    base_image = Image.open("src/background.png").convert("RGBA")
    draw = ImageDraw.Draw(base_image)
    
    # For a polished look, you can download a custom .ttf font and load it here
    font_large = ImageFont.load_default() 
    font_small = ImageFont.load_default()
    
    # Draw a dark overlay for readability
    draw.rounded_rectangle([100, 600, 1190, 1600], radius=40, fill=(30, 30, 30, 180))
    
    # Draw Agenda
    y_position = 650
    draw.text((150, y_position), "This Week's Agenda:", fill=(255, 255, 255), font=font_large)
    y_position += 80
    
    for event in events[:10]: # Limit to 10 events so it fits
        start = event['start'].get('dateTime', event['start'].get('date'))
        # Basic parsing (you can refine the date formatting later)
        time_str = start[:10] 
        summary = event['summary']
        draw.text((150, y_position), f"- {time_str}: {summary}", fill=(200, 200, 200), font=font_small)
        y_position += 60

    base_image.convert("RGB").save("wallpaper.png")
    print("Wallpaper generated!")

if __name__ == "__main__":
    events = get_calendar_events()
    generate_wallpaper(events)