import os
import json
import urllib.request
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont

# Bảng màu UI chuyên nghiệp (Xanh lam, Vàng cam, Đỏ san hô, Tím nhạt)
EVENT_COLORS = [
    (74, 144, 226, 255),  
    (245, 166, 35, 255),  
    (238, 84, 84, 255),   
    (189, 16, 224, 255)   
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
    # Làm tối toàn bộ ảnh nền một chút để chữ nổi bật hơn (giống ảnh mẫu)
    dark_overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 100))
    base_image = Image.alpha_composite(base_image, dark_overlay)
    
    draw = ImageDraw.Draw(base_image)
    
    # Tải Font chữ
    font_reg_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
    font_bold_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
    urllib.request.urlretrieve(font_reg_url, "Roboto-Reg.ttf")
    urllib.request.urlretrieve(font_bold_url, "Roboto-Bold.ttf")
    
    font_day = ImageFont.truetype("Roboto-Bold.ttf", 35)
    font_date = ImageFont.truetype("Roboto-Bold.ttf", 40)
    font_header = ImageFont.truetype("Roboto-Bold.ttf", 55)
    font_time = ImageFont.truetype("Roboto-Bold.ttf", 45)
    font_event = ImageFont.truetype("Roboto-Bold.ttf", 45)
    
    # --- 1. THIẾT KẾ GRID 7 NGÀY (MODULAR BLOCKS) ---
    grid_y_start = 850  # Bắt đầu ngay dưới cụm đồng hồ iOS
    margin_x = 80
    usable_width = base_image.width - (margin_x * 2)
    col_w = usable_width / 7
    
    utc_now = datetime.utcnow()
    local_now = utc_now + timedelta(hours=7)
    
    # Gán màu cố định cho mỗi sự kiện để đồng bộ giữa Grid và Agenda
    event_color_map = {}
    for i, event in enumerate(events):
        event_color_map[event['id']] = EVENT_COLORS[i % len(EVENT_COLORS)]

    for i in range(7):
        current_day = local_now + timedelta(days=i)
        day_str = current_day.strftime("%a")
        date_str = str(current_day.day)
        
        col_x = margin_x + (i * col_w)
        col_center_x = col_x + (col_w / 2)
        
        # Vẽ thứ và ngày
        text_color = (255, 255, 255, 255) if i == 0 else (180, 180, 180, 255)
        day_w = draw.textlength(day_str, font=font_day)
        date_w = draw.textlength(date_str, font=font_date)
        
        draw.text((col_center_x - day_w/2, grid_y_start), day_str, fill=text_color, font=font_day)
        draw.text((col_center_x - date_w/2, grid_y_start + 45), date_str, fill=text_color, font=font_date)
        
        # Vẽ các block sự kiện cho ngày hôm đó
        block_y = grid_y_start + 110
        events_this_day = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == current_day.strftime("%d")]
        
        for e in events_this_day[:4]: # Hiển thị tối đa 4 block mỗi cột
            color = event_color_map[e['id']]
            draw.rectangle([col_x + 5, block_y, col_x + col_w - 5, block_y + 15], fill=color)
            block_y += 22

    # --- 2. THIẾT KẾ AGENDA HÔM NAY (TYPOGRAPHY) ---
    agenda_y_start = grid_y_start + 280
    draw.text((margin_x, agenda_y_start), "Today", fill=(255, 255, 255, 255), font=font_header)
    
    list_y = agenda_y_start + 90
    events_today = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == local_now.strftime("%d")]
    
    if not events_today:
        draw.text((margin_x, list_y), "No events today", fill=(150, 150, 150, 255), font=font_time)
        
    for event in events_today[:6]:
        start_time_raw = event['start'].get('dateTime', event['start'].get('date'))
        end_time_raw = event['end'].get('dateTime', event['end'].get('date'))
        
        if 'T' in start_time_raw:
            time_str = f"{start_time_raw[11:16]}-{end_time_raw[11:16]}"
        else:
            time_str = "All day"
            
        summary = event['summary']
        if len(summary) > 20:
            summary = summary[:17] + "..."
            
        color = event_color_map[event['id']]
        
        # Cột thời gian (Màu trắng mờ)
        draw.text((margin_x, list_y), time_str, fill=(200, 200, 200, 255), font=font_time)
        # Cột Tên sự kiện (Màu sắc tương ứng với block ở trên)
        draw.text((margin_x + 350, list_y), summary, fill=color, font=font_event)
        
        list_y += 75

    base_image.convert("RGB").save("wallpaper.png")
    print("Professional Modular UI generated!")

if __name__ == "__main__":
    events = get_calendar_events()
    generate_pro_wallpaper(events)
