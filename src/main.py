import os
import json
import urllib.request
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont

# Professional UI Palette
EVENT_COLORS = [
    (74, 144, 226, 255),   # Blue
    (245, 166, 35, 255),   # Orange
    (238, 84, 84, 255),    # Coral Red
    (189, 16, 224, 255)    # Purple
]

def get_calendar_events():
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict)
    else:
        creds = service_account.Credentials.from_service_account_file('credentials.json')
    
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.utcnow()
    now_str = now.isoformat() + 'Z'
    end_of_week = (now + timedelta(days=7)).isoformat() + 'Z'
    
    events_result = service.events().list(calendarId='primary', timeMin=now_str,
                                          timeMax=end_of_week, singleEvents=True,
                                          orderBy='startTime').execute()
    return events_result.get('items', [])

def generate_pro_wallpaper(events):
    base_image = Image.open("src/background.png").convert("RGBA")
    draw = ImageDraw.Draw(base_image)
    
    # Download Web Fonts
    font_reg_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
    font_bold_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
    urllib.request.urlretrieve(font_reg_url, "Roboto-Reg.ttf")
    urllib.request.urlretrieve(font_bold_url, "Roboto-Bold.ttf")
    
    font_day = ImageFont.truetype("Roboto-Reg.ttf", 35)
    font_date = ImageFont.truetype("Roboto-Bold.ttf", 45)
    font_header = ImageFont.truetype("Roboto-Bold.ttf", 55)
    font_time = ImageFont.truetype("Roboto-Reg.ttf", 45)
    font_event = ImageFont.truetype("Roboto-Bold.ttf", 45)
    
    # --- UX FIX 1: SAFE ZONE PLACEMENT ---
    # Shift UI down to Y=1750 (the dark background area) to preserve the main subject.
    grid_y_start = 1750  
    margin_x = 100
    usable_width = base_image.width - (margin_x * 2)
    col_w = usable_width / 7
    
    local_now = datetime.utcnow() + timedelta(hours=7)
    
    event_color_map = {}
    for i, event in enumerate(events):
        event_color_map[event['id']] = EVENT_COLORS[i % len(EVENT_COLORS)]

    # --- UX FIX 2: PRECISION GRID ALIGNMENT ---
    for i in range(7):
        current_day = local_now + timedelta(days=i)
        day_str = current_day.strftime("%a")
        date_str = str(current_day.day)
        
        col_x = margin_x + (i * col_w)
        col_center_x = col_x + (col_w / 2)
        
        text_color = (255, 255, 255, 255) if i == 0 else (160, 160, 160, 255)
        
        day_w = draw.textlength(day_str, font=font_day)
        date_w = draw.textlength(date_str, font=font_date)
        
        draw.text((col_center_x - day_w/2, grid_y_start), day_str, fill=text_color, font=font_day)
        draw.text((col_center_x - date_w/2, grid_y_start + 50), date_str, fill=text_color, font=font_date)
        
        # Color Blocks
        block_y = grid_y_start + 120
        events_this_day = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == current_day.strftime("%d")]
        
        for e in events_this_day[:4]:
            color = event_color_map[e['id']]
            block_w = 40
            draw.rounded_rectangle([col_center_x - block_w/2, block_y, col_center_x + block_w/2, block_y + 12], radius=6, fill=color)
            block_y += 20

    # --- UX FIX 3: CONTEXTUAL EMPTY STATE ---
    agenda_y_start = grid_y_start + 260
    events_today = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == local_now.strftime("%d")]
    
    display_events = events_today
    header_text = "Today"
    
    # If today is over/empty, smartly switch to Tomorrow or Upcoming
    if not events_today:
        tomorrow = local_now + timedelta(days=1)
        display_events = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == tomorrow.strftime("%d")]
        header_text = "Tomorrow" if display_events else "Upcoming"
        if not display_events:
            display_events = events[:5] 

    draw.text((margin_x, agenda_y_start), header_text, fill=(255, 255, 255, 255), font=font_header)
    
    list_y = agenda_y_start + 90
    
    if not display_events:
        draw.text((margin_x, list_y), "Enjoy your free time!", fill=(150, 150, 150, 255), font=font_time)
        
    for event in display_events[:5]:
        start_time_raw = event['start'].get('dateTime', event['start'].get('date'))
        
        if 'T' in start_time_raw:
            time_str = f"{start_time_raw[11:16]}"
        else:
            time_str = "All day"
            
        summary = event['summary']
        if len(summary) > 22:
            summary = summary[:19] + "..."
            
        color = event_color_map[event['id']]
        
        draw.text((margin_x, list_y), time_str, fill=(180, 180, 180, 255), font=font_time)
        draw.text((margin_x + 250, list_y), summary, fill=color, font=font_event)
        
        list_y += 75

    base_image.convert("RGB").save("wallpaper.png")
    print("Pro UX UI generated successfully!")

if __name__ == "__main__":
    events = get_calendar_events()
    generate_pro_wallpaper(events)
