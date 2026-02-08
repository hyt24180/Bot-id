from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

# دالة لفك تشفير أرقام الـ Varint (التي تستخدمها ملفات الألعاب)
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
    except:
        return None, 0

# دالة لتحويل الرقم الجديد إلى صيغة Varint
def encode_varint(num):
    if num == 0: return b'\x00'
    out = []
    while num > 0x7F:
        out.append((num & 0x7F) | 0x80)
        num >>= 7
    out.append(num)
    return bytes(out)

# دالة للبحث عن الـ UID الحقيقي داخل الملف
def find_uid_data(data):
    # نبحث عن النمط المشهور للـ UID في ملفات bytes (يبدأ عادة بـ 0x38)
    for i in range(len(data) - 10):
        if data[i] == 0x38:
            value, length = decode_varint(data, i + 1)
            if value is not None and value > 1000000: # الـ ID الحقيقي دائماً رقم كبير
                return i + 1, length, value
    return None

# المسار الأول: استخراج المعلومات فقط
@app.route('/get_info', methods=['POST'])
def get_info():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400
    
    file_bytes = request.files['file'].read()
    res = find_uid_data(bytearray(file_bytes))
    
    if res:
        return jsonify({"success": True, "uid": str(res[2])})
    return jsonify({"success": False, "error": "UID not found"}), 404

# المسار الثاني: تعديل الملف وإعادته
@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files or 'uid' not in request.form:
        return "Missing data", 400
    
    new_uid = int(request.form['uid'])
    data = bytearray(request.files['file'].read())
    
    res = find_uid_data(data)
    if res:
        start, length, _ = res
        new_v = encode_varint(new_uid)
        
        # استبدال الـ ID القديم بالجديد
        modified_data = data[:start] + new_v + data[start + length:]
        
        output = io.BytesIO(modified_data)
        return send_file(
            output, 
            mimetype='application/octet-stream', 
            as_attachment=True, 
            download_name="ProjectData_slot_1.bytes"
        )
    
    return "UID not found in file", 404

@app.route('/')
def home():
    return "API is Online"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
