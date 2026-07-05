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
    now = datetime.utcnow().isoformat() + 'Z'
    end_of_week = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
    
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          timeMax=end_of_week, singleEvents=True,
                                          orderBy='startTime').execute()
    return events_result.get('items', [])

def generate_wallpaper(events):
    # 1. Mở ảnh gốc
    base_image = Image.open("src/background.png").convert("RGBA")
    
    # 2. Tạo một lớp trong suốt (Overlay) để vẽ khung mờ giúp không làm hỏng ảnh gốc
    overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 3. Tải Font chữ Roboto hiện đại trực tiếp từ Google Fonts
    font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf"
    urllib.request.urlretrieve(font_url, "Roboto.ttf")
    font_title = ImageFont.truetype("Roboto.ttf", 65)
    font_event = ImageFont.truetype("Roboto.ttf", 45)
    
    # 4. Vẽ khung lịch trình ở vị trí thấp hơn (Y từ 1400 đến 2200)
    # Tọa độ: [X_trái, Y_trên, X_phải, Y_dưới]
    draw.rounded_rectangle([80, 1400, 1210, 2200], radius=50, fill=(20, 20, 20, 160))
    
    # 5. Viết tiêu đề
    y_pos = 1460
    draw.text((140, y_pos), "Lịch trình 7 ngày tới:", fill=(255, 255, 255, 255), font=font_title)
    y_pos += 110
    
    # 6. Viết các sự kiện
    if not events:
        draw.text((140, y_pos), "Không có sự kiện nào!", fill=(200, 200, 200, 255), font=font_event)
        
    for event in events[:8]: # Hiển thị tối đa 8 sự kiện
        start = event['start'].get('dateTime', event['start'].get('date'))
        
        # Xử lý chuỗi thời gian cho gọn (ví dụ: 06/07 09:00)
        if 'T' in start:
            time_str = f"{start[8:10]}/{start[5:7]} - {start[11:16]}"
        else:
            time_str = f"{start[8:10]}/{start[5:7]} - Cả ngày"
            
        summary = event['summary']
        if len(summary) > 23: # Rút gọn nếu tên sự kiện quá dài
            summary = summary[:20] + "..."
            
        draw.text((140, y_pos), f"• {time_str} : {summary}", fill=(230, 230, 230, 255), font=font_event)
        y_pos += 75

    # 7. Hợp nhất lớp trong suốt vào ảnh gốc và lưu lại
    final_image = Image.alpha_composite(base_image, overlay)
    final_image.convert("RGB").save("wallpaper.png")
    print("Wallpaper generated!")

if __name__ == "__main__":
    events = get_calendar_events()
    generate_wallpaper(events)
