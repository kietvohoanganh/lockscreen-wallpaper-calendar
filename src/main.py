import os
import json
import urllib.request
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image, ImageDraw, ImageFont

# Bảng màu UI chuyên nghiệp
EVENT_COLORS = [
    (74, 144, 226, 255),  # Xanh lam
    (245, 166, 35, 255),  # Vàng cam
    (238, 84, 84, 255),   # Đỏ san hô
    (189, 16, 224, 255)   # Tím nhạt
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
    W, H = base_image.size # Lấy tỷ lệ động của ảnh gốc
    
    # Phủ lớp kính mờ (120/255) để text nổi bật trên nền ảnh
    dark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    base_image = Image.alpha_composite(base_image, dark_overlay)
    draw = ImageDraw.Draw(base_image)
    
    # Tải Font chữ
    font_reg_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
    font_bold_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
    urllib.request.urlretrieve(font_reg_url, "Roboto-Reg.ttf")
    urllib.request.urlretrieve(font_bold_url, "Roboto-Bold.ttf")
    
    # Tính toán kích thước Font động theo chiều rộng ảnh (W)
    size_day = int(W * 0.035)
    size_date = int(W * 0.045)
    size_header = int(W * 0.055)
    size_body = int(W * 0.038)
    
    font_day = ImageFont.truetype("Roboto-Bold.ttf", size_day)
    font_date = ImageFont.truetype("Roboto-Bold.ttf", size_date)
    font_header = ImageFont.truetype("Roboto-Bold.ttf", size_header)
    font_body = ImageFont.truetype("Roboto-Bold.ttf", size_body)
    
    # --- 1. THIẾT KẾ GRID 7 NGÀY ---
    grid_y_start = int(H * 0.38) # Bắt đầu ở mốc 38% chiều cao (ngay dưới đồng hồ)
    margin_x = int(W * 0.06)
    usable_width = W - (margin_x * 2)
    col_w = usable_width / 7
    
    utc_now = datetime.utcnow()
    local_now = utc_now + timedelta(hours=7)
    
    # Map ID sự kiện với màu sắc cố định
    event_color_map = {}
    for i, event in enumerate(events):
        event_color_map[event['id']] = EVENT_COLORS[i % len(EVENT_COLORS)]

    for i in range(7):
        current_day = local_now + timedelta(days=i)
        day_str = current_day.strftime("%a")
        date_str = str(current_day.day)
        
        col_x = margin_x + (i * col_w)
        col_center_x = col_x + (col_w / 2)
        
        text_color = (255, 255, 255, 255) if i == 0 else (180, 180, 180, 255)
        
        day_w = draw.textlength(day_str, font=font_day)
        date_w = draw.textlength(date_str, font=font_date)
        
        # Vẽ Text ngày tháng
        draw.text((col_center_x - day_w/2, grid_y_start), day_str, fill=text_color, font=font_day)
        draw.text((col_center_x - date_w/2, grid_y_start + int(H * 0.022)), date_str, fill=text_color, font=font_date)
        
        # Vẽ Color Blocks
        block_y = grid_y_start + int(H * 0.06)
        events_this_day = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == current_day.strftime("%d")]
        
        for e in events_this_day[:4]:
            color = event_color_map[e['id']]
            draw.rounded_rectangle([col_x + 6, block_y, col_x + col_w - 6, block_y + int(H * 0.012)], radius=4, fill=color)
            block_y += int(H * 0.016)

    # --- 2. THIẾT KẾ AGENDA ---
    agenda_y_start = grid_y_start + int(H * 0.16)
    draw.text((margin_x, agenda_y_start), "Today", fill=(255, 255, 255, 255), font=font_header)
    
    list_y = agenda_y_start + int(H * 0.06)
    events_today = [e for e in events if e['start'].get('dateTime', e['start'].get('date'))[8:10] == local_now.strftime("%d")]
    
    if not events_today:
        draw.text((margin_x, list_y), "No events today", fill=(150, 150, 150, 255), font=font_body)
        
    for event in events_today[:6]:
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        end_raw = event['end'].get('dateTime', event['end'].get('date'))
        
        if 'T' in start_raw:
            time_str = f"{start_raw[11:16]} - {end_raw[11:16]}"
        else:
            time_str = "All day"
            
        summary = event['summary']
        if len(summary) > 22:
            summary = summary[:19] + "..."
            
        color = event_color_map[event['id']]
        draw.text((margin_x, list_y), time_str, fill=(220, 220, 220, 255), font=font_body)
        draw.text((margin_x + int(W * 0.35), list_y), summary, fill=color, font=font_body)
        
        list_y += int(H * 0.038)

    base_image.convert("RGB").save("wallpaper.png")
    print("Responsive Modular UI successfully generated!")

if __name__ == "__main__":
    events = get_calendar_events()
    generate_pro_wallpaper(events)
