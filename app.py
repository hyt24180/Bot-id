import telebot
import io
import re
from flask import Flask, request

app = Flask(__name__)
TOKEN = "8488650962:AAHbiv5ErWNooKDD36wAeGm0gDpRbbUHirQ"
bot = telebot.TeleBot(TOKEN)

def process_file_logic(data, new_uid_int):
    # تحويل الآيدي الجديد إلى Bytes
    new_uid_bytes = new_uid_int.to_bytes(4, byteorder='little')
    
    # محاولة إيجاد الآيدي القديم:
    # معظم ملفات .bytes تضع الآيدي بعد علامة معينة أو في مكان يتراوح بين 48 و 60
    # سنقوم هنا بفحص الإزاحة الأكثر شيوعاً 0x38 (56)
    offset = 56 
    old_uid_int = int.from_bytes(data[offset:offset+4], byteorder='little')
    
    # إذا كان الرقم الذي قرأناه يبدو غير منطقي، سنبحث في أماكن قريبة
    if old_uid_int == 1816593930 or old_uid_int == 0:
        # فحص إزاحة أخرى مشهورة 0x30 (48)
        offset = 48
        old_uid_int = int.from_bytes(data[offset:offset+4], byteorder='little')

    new_data = bytearray(data)
    new_data[offset:offset+4] = new_uid_bytes
    return bytes(new_data), old_uid_int

@app.route('/process_by_name', methods=['POST'])
def handle_process():
    try:
        file = request.files.get('file')
        chat_id = request.form.get('chat_id')
        
        # استخراج الآيدي الجديد من اسم الملف
        new_uid = int(re.search(r'(\d+)', file.filename).group(1))
        file_content = file.read()

        modified_data, old_uid = process_file_logic(file_content, new_uid)

        output = io.BytesIO(modified_data)
        output.name = "ProjectData_slot_1.bytes"
        
        # رسالة احترافية بدون ذكر Vercel
        caption = (f"✅ **تمت العملية بنجاح**\n\n"
                   f"🆔 المعرف القديم: `{old_uid}`\n"
                   f"🆕 المعرف الجديد: `{new_uid}`")
        
        bot.send_document(chat_id, output, caption=caption, parse_mode='Markdown')
        return "OK", 200
    except Exception as e:
        return str(e), 500
