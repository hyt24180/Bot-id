from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io

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
    except IndexError:
        return None, 0

def encode_varint(num):
    if num == 0: return b'\x00'
    out = []
    while num > 0x7F:
        out.append((num & 0x7F) | 0x80)
        num >>= 7
    out.append(num)
    return bytes(out)

def find_uid(data):
    for i in range(len(data) - 6):
        if data[i] == 0x38:
            value, length = decode_varint(data, i + 1)
            if value is not None:
                if i + 1 + length < len(data) and data[i + 1 + length] == 0x42:
                    return i + 1, length, value # أضفنا القيمة هنا
    return None

@app.route('/')
def home():
    return {"status": "online"}

# نقطة اتصال جديدة لمعرفة الـ UID القديم فقط قبل التعديل
@app.route('/get_info', methods=['POST'])
def get_info():
    if 'file' not in request.files: return {"error": "No file"}, 400
    data = bytearray(request.files['file'].read())
    res = find_uid(data)
    if res:
        return jsonify({"old_uid": str(res[2])})
    return jsonify({"error": "UID not found"}), 404

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files: return {"error": "No file"}, 400
    
    file = request.files['file']
    new_uid = int(request.form.get('uid', 0))
    data = bytearray(file.read())
    res = find_uid(data)

    if res:
        start, length, _ = res
        modified_data = data[:start] + encode_varint(new_uid) + data[start + length:]
        output = io.BytesIO(modified_data)
        
        # هنا قمنا بتثبيت الاسم كما طلبت
        return send_file(
            output,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name="ProjectData_slot_1.bytes" 
        )
    
    return {"error": "UID not found"}, 404

if __name__ == "__main__":
    app.run()
