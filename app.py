from flask import Flask, request, send_file
from flask_cors import CORS  # مكتبة حل مشكلة فشل الاتصال من المتصفح
import io

app = Flask(__name__)
CORS(app) # تفعيل السماح بالاتصال من أي مصدر (حل مشكلة فشل الاتصال)

# 1. دالة فك تشفير Varint لقراءة الـ UID القديم
def decode_varint(data, start):
    value, shift, pos = 0, 0, start
    try:
        while True:
            b = data[pos]
            value |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
            pos += 1
        return value, pos - start + 1
    except IndexError:
        return None, 0

# 2. دالة تشفير Varint لكتابة الـ UID الجديد
def encode_varint(num):
    if num == 0:
        return b'\x00'
    out = []
    while num > 0x7F:
        out.append((num & 0x7F) | 0x80)
        num >>= 7
    out.append(num)
    return bytes(out)

# 3. البحث عن موقع الـ UID (بناءً على النمط 0x38 و 0x42)
def find_uid(data):
    for i in range(len(data) - 6):
        # البحث عن العلامة الاستدلالية 0x38
        if data[i] == 0x38:
            value, length = decode_varint(data, i + 1)
            if value is not None:
                # التأكد من وجود العلامة الختامية 0x42 بعد القيمة
                if i + 1 + length < len(data) and data[i + 1 + length] == 0x42:
                    return i + 1, length
    return None

@app.route('/')
def home():
    return {"status": "online", "message": "API is Running! Use /process for requests."}

@app.route('/process', methods=['POST'])
def process_file():
    # التحقق من وجود ملف في الطلب
    if 'file' not in request.files:
        return {"error": "Missing file part"}, 400
    
    file = request.files['file']
    uid_str = request.form.get('uid', '0')
    
    try:
        new_uid = int(uid_str)
    except ValueError:
        return {"error": "Invalid UID format"}, 400

    if file.filename == '':
        return {"error": "No selected file"}, 400

    # قراءة بيانات الملف ومعالجتها
    data = bytearray(file.read())
    res = find_uid(data)

    if res:
        start, length = res
        new_var = encode_varint(new_uid)
        
        # استبدال البايتات القديمة بالجديدة (تعديل الـ UID)
        modified_data = data[:start] + new_var + data[start + length:]
        
        output = io.BytesIO(modified_data)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name="Craftland_Modified.bytes"
        )
    
    return {"error": "UID pattern not found in the file"}, 404

# التشغيل
if __name__ == "__main__":
    app.run(debug=True)
