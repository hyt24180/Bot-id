from flask import Flask, request, jsonify
import telebot
import io
import re

app = Flask(__name__)

# إعدادات البوت
TOKEN = "8488650962:AAHbiv5ErWNooKDD36wAeGm0gDpRbbUHirQ"
bot = telebot.TeleBot(TOKEN)

def change_uid(data, new_uid_int):
    # تحويل الآيدي الجديد إلى Bytes (Little Endian - 4 bytes)
    new_uid_bytes = new_uid_int.to_bytes(4, byteorder='little')
    
    # البحث عن المعرف القديم عند الأوفست 0x38 (حسب ملفات .bytes المشهورة)
    # إذا كان موقع الآيدي مختلفاً في ملفك، يجب تعديل الرقم 56 (0x38)
    offset = 56 
    old_uid_int = int.from_bytes(data[offset:offset+4], byteorder='little')
    
    # تبديل الآيدي
    new_data = bytearray(data)
    new_data[offset:offset+4] = new_uid_bytes
    
    return bytes(new_data), old_uid_int

@app.route('/process_by_name', methods=['POST'])
def process_file():
    try:
        # 1. استقبال الملف و chat_id
        file = request.files.get('file')
        chat_id = request.form.get('chat_id')
        
        if not file or not chat_id:
            return "Missing data", 400

        # 2. قراءة اسم الملف لاستخراج الآيدي الجديد
        file_name = file.filename
        match = re.search(r'(\d+)', file_name)
        if not match:
            return "No ID in filename", 400
        
        new_uid = int(match.group(1))
        file_content = file.read()

        # 3. معالجة الملف وتغيير الآيدي
        modified_data, old_uid = change_uid(file_content, new_uid)

        # 4. إرسال الملف المعدل مباشرة من Vercel إلى تليجرام
        output = io.BytesIO(modified_data)
        output.name = "ProjectData_slot_1.bytes"
        
        caption = (f"✅ **تم التعديل بواسطة Vercel**\n\n"
                   f"🆔 المعرف القديم: `{old_uid}`\n"
                   f"🆕 المعرف الجديد: `{new_uid}`")
        
        bot.send_document(chat_id, output, caption=caption, parse_mode='Markdown')

        return "Success", 200

    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
