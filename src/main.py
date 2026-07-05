import os
import json
import urllib.request
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont

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

def generate_wallpaper(events):
    base_image = Image.open("src/background.png").convert("RGBA")
    overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Download modern fonts (Roboto Regular and Medium)
    font_url_reg = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
    font_url_med = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf"
    urllib.request.urlretrieve(font_url_reg, "Roboto-Reg.ttf")
    urllib.request.urlretrieve(font_url_med, "Roboto-Med.ttf")
    
    font_day = ImageFont.truetype("Roboto-Reg.ttf", 35)
    font_date = ImageFont.truetype("Roboto-Med.ttf", 45)
    font_agenda_title = ImageFont.truetype("Roboto-Med.ttf", 45)
    font_agenda_time = ImageFont.truetype("Roboto-Med.ttf", 40)
    font_agenda_item = ImageFont.truetype("Roboto-Reg.ttf", 40)
    
    # Layout Coordinates (Moved up to sit directly under the clock)
    box_x1, box_y1 = 80, 750
    box_x2, box_y2 = 1204, 1600
    box_w = box_x2 - box_x1
    
    # Draw the main glassmorphism container
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=60, fill=(20, 20, 25, 210))
    
    # --- 1. TOP SECTION: 7-DAY TIMELINE GRID ---
    col_w = box_w / 7
    utc_now = datetime.utcnow()
    local_now = utc_now + timedelta(hours=7) # Ensures the calendar aligns with your local timezone
    
    grid_y_start = box_y1 + 50
    accent_color = (210, 130, 60, 255) # Sleek orange/brown accent matching your reference
    
    for i in range(7):
        current_day = local_now + timedelta(days=i)
        day_str = current_day.strftime("%a") # e.g., Mon, Tue
        date_str = current_day.strftime("%d") # e.g., 01, 15
        
        col_center_x = box_x1 + (i * col_w) + (col_w / 2)
        
        # Highlight "Today" (i == 0)
        if i == 0:
            draw.rounded_rectangle(
                [box_x1 + (i * col_w) + 15, grid_y_start - 15, 
                 box_x1 + ((i+1) * col_w) - 15, grid_y_start + 130], 
                radius=30, fill=(210, 130, 60, 90) # Semi-transparent highlight block
            )
            text_color = accent_color
            date_color = (255, 255, 255, 255)
        else:
            text_color = (140, 140, 150, 255)
            date_color = (200, 200, 210, 255)
        
        # Center the text dynamically based on string width
        day_w = draw.textlength(day_str, font=font_day)
        date_w = draw.textlength(date_str, font=font_date)
        
        draw.text((col_center_x - day_w/2, grid_y_start), day_str, fill=text_color, font=font_day)
        draw.text((col_center_x - date_w/2, grid_y_start + 60), date_str, fill=date_color, font=font_date)
        
    # Separator Line between the grid and the agenda
    sep_y = grid_y_start + 170
    draw.line([(box_x1 + 60, sep_y), (box_x2 - 60, sep_y)], fill=(80, 80, 90, 150), width=3)
    
    # --- 2. BOTTOM SECTION: AGENDA ---
    agenda_y = sep_y + 50
    draw.text((box_x1 + 60, agenda_y), "Upcoming Agenda", fill=accent_color, font=font_agenda_title)
    agenda_y += 90
    
    if not events:
        draw.text((box_x1 + 60, agenda_y), "No events scheduled.", fill=(150, 150, 160, 255), font=font_agenda_item)
    
    for event in events[:5]: # Display the next 5 events neatly
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event['summary']
        
        # Format the time beautifully (e.g., "07/05  |  17:00")
        if 'T' in start:
            time_str = start[11:16]
            date_label = f"{start[8:10]}/{start[5:7]}"
            display_time = f"{date_label}  |  {time_str}"
        else:
            display_time = f"{start[8:10]}/{start[5:7]}  |  All Day"
            
        if len(summary) > 22:
            summary = summary[:19] + "..."
            
        # Draw columns: [Time column] and [Event Name column]
        draw.text((box_x1 + 60, agenda_y), display_time, fill=(255, 255, 255, 255), font=font_agenda_time)
        draw.text((box_x1 + 420, agenda_y), summary, fill=(200, 200, 210, 255), font=font_agenda_item)
        
        agenda_y += 75

    # Merge layers and save
    final_image = Image.alpha_composite(base_image, overlay)
    final_image.convert("RGB").save("wallpaper.png")
    print("Sleek wallpaper generated successfully!")

if __name__ == "__main__":
    events = get_calendar_events()
    generate_wallpaper(events)
