import telebot
import io
import re
from flask import Flask, request

app = Flask(__name__)
TOKEN = "8488650962:AAHbiv5ErWNooKDD36wAeGm0gDpRbbUHirQ"
bot = telebot.TeleBot(TOKEN)

# دالة فك تشفير Varint (كما في ملف index.html)
def decode_varint(data, start):
    v = 0
    shift = 0
    i = start
    while True:
        b = data[i]
        v |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
        i += 1
    return v, i - start + 1

# دالة تشفير Varint للآيدي الجديد
def encode_varint(n):
    out = bytearray()
    while n > 0x7F:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return out

def process_craftland_file(data, new_uid_int):
    # البحث عن العلامة 0x38 التي تسبق الآيدي
    for i in range(len(data) - 5):
        if data[i] == 0x38:
            try:
                # قراءة الآيدي القديم بصيغة Varint
                old_uid, length = decode_varint(data, i + 1)
                
                # التأكد من أنه الآيدي الصحيح (يكون متبوعاً بـ 0x42 وآيدي كبير)
                if data[i + 1 + length] == 0x42 and old_uid > 100000:
                    
                    # تشفير الآيدي الجديد
                    new_uid_bytes = encode_varint(new_uid_int)
                    
                    # بناء الملف الجديد (استبدال الجزء القديم بالجديد)
                    new_data = data[:i+1] + new_uid_bytes + data[i+1+length:]
                    
                    return new_data, old_uid
            except:
                continue
    return data, "غير موجود"

@app.route('/process_by_name', methods=['POST'])
def handle_process():
    try:
        file = request.files.get('file')
        chat_id = request.form.get('chat_id')
        new_uid = int(re.search(r'(\d+)', file.filename).group(1))
        file_content = file.read()

        modified_data, old_uid = process_craftland_file(file_content, new_uid)

        output = io.BytesIO(modified_data)
        output.name = "ProjectData_slot_1.bytes"
        
        caption = (f"✅ **تمت المعالجة بنجاح**\n\n"
                   f"🆔 المعرف القديم: `{old_uid}`\n"
                   f"🆕 المعرف الجديد: `{new_uid}`")
        
        bot.send_document(chat_id, output, caption=caption, parse_mode='Markdown')
        return "OK", 200
    except Exception as e:
        return str(e), 500
