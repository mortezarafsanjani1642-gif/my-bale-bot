import requests
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def get_updates():
    try:
        r = requests.post(f"{API_URL}/getUpdates", json={"timeout": 5}, timeout=10)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"❌ خطا: {e}")
        return {}

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        print(f"📤 پاسخ sendMessage: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ خطا: {e}")

def main():
    print("🔍 دریافت آپدیت‌ها...")
    response = get_updates()
    
    if response.get("status") == "OK":
        data = response.get("data", {})
        updates = data.get("updates", [])
        
        if updates:
            # پیدا کردن آخرین NewMessage
            last_new_message = None
            for upd in reversed(updates):  # از آخر به اول
                if upd.get("type") == "NewMessage":
                    last_new_message = upd
                    break
            
            if last_new_message:
                chat_id = last_new_message.get("chat_id")
                msg = last_new_message.get("new_message", {})
                text = msg.get("text", "")
                sender = msg.get("sender_id")
                
                print(f"📩 آخرین NewMessage:")
                print(f"  chat_id: {chat_id}")
                print(f"  sender: {sender}")
                print(f"  text: {text}")
                
                # ارسال پیام تست
                send_message(chat_id, "سلام! این یک پیام تست از پایتون است.")
            else:
                print("⚠️ هیچ NewMessage در آپدیت‌ها یافت نشد.")
        else:
            print("⚠️ هیچ آپدیتی یافت نشد.")
    else:
        print("❌ خطا در دریافت آپدیت.")

if __name__ == "__main__":
    main()