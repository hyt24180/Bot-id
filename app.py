from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import re

app = Flask(__name__)
CORS(app)

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
            if value is not None and value > 1000000:
                return i + 1, length, value
    return None

@app.route('/process_by_name', methods=['POST'])
def process_by_name():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    filename = file.filename
    
    # استخراج الـ ID الجديد من اسم الملف (مثلاً 14580239389.bytes)
    match = re.search(r'(\d+)', filename)
    if not match:
        return "New ID not found in filename", 400
    
    new_uid = int(match.group(1))
    data = bytearray(file.read())
    res = find_uid_data(data)

    if res:
        start, length, old_uid = res
        new_v = encode_varint(new_uid)
        
        # تعديل البيانات
        modified_data = data[:start] + new_v + data[start + length:]
        
        output = io.BytesIO(modified_data)
        # إرسال الملف مع وضع المعرف القديم في الهيدر لكي يقرأه جوجل سكربت
        response = send_file(
            output,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name="ProjectData_slot_1.bytes"
        )
        response.headers['X-Old-UID'] = str(old_uid)
        response.headers['X-New-UID'] = str(new_uid)
        return response
    
    return "UID pattern not found in file", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
