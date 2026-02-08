from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import re

app = Flask(__name__)
# تفعيل CORS للسماح للموقع بقراءة البيانات من السيرفر
CORS(app, expose_headers=['X-Old-UID', 'X-New-UID'])

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
    except: return None, 0

def encode_varint(num):
    if num == 0: return b'\x00'
    out = []
    while num > 0x7F:
        out.append((num & 0x7F) | 0x80)
        num >>= 7
    out.append(num)
    return bytes(out)

def find_uid_data(data):
    for i in range(len(data) - 10):
        if data[i] == 0x38:
            value, length = decode_varint(data, i + 1)
            # التأكد أن الـ ID أكبر من مليون لضمان الدقة
            if value is not None and value > 1000000:
                return i + 1, length, value
    return None

@app.route('/process_by_name', methods=['POST'])
def process_by_name():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    filename = file.filename
    
    # استخراج الـ ID الجديد من اسم الملف
    match = re.search(r'(\d+)', filename)
    if not match:
        return "New ID not found in filename. Rename file to '12345.bytes'", 400
    
    new_uid = int(match.group(1))
    data = bytearray(file.read())
    res = find_uid_data(data)

    if res:
        start, length, old_uid = res
        new_v = encode_varint(new_uid)
        
        # استبدال المعرف القديم بالجديد
        modified_data = data[:start] + new_v + data[start + length:]
        
        output = io.BytesIO(modified_data)
        response = send_file(
            output,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name="ProjectData_slot_1.bytes"
        )
        
        # إضافة البيانات في الهيدرز ليقرأها الموقع
        response.headers['X-Old-UID'] = str(old_uid)
        response.headers['X-New-UID'] = str(new_uid)
        # تصريح للمتصفح بقراءة هذه الهيدرز
        response.headers['Access-Control-Expose-Headers'] = 'X-Old-UID, X-New-UID'
        return response
    
    return "UID pattern (0x38) not found in file", 404

@app.route('/')
def home():
    return "API is Online and ready for website requests."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
