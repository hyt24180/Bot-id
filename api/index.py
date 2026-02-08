from flask import Flask, request, send_file
import io

app = Flask(__name__)

# [span_1](start_span)دالة فك تشفير Varint كما في منطق الموقع[span_1](end_span)
def decode_varint(data, start):
    value, shift, pos = 0, 0, start
    while True:
        b = data[pos]
        value |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
        pos += 1
    return value, pos - start + 1

# [span_2](start_span)دالة تشفير Varint لإعادة كتابة الـ UID[span_2](end_span)
def encode_varint(num):
    out = []
    while num > 0x7F:
        out.append((num & 0x7F) | 0x80)
        num >>= 7
    out.append(num)
    return bytes(out)

# [span_3](start_span)البحث عن موقع الـ UID في ملف الـ bytes[span_3](end_span)
def find_uid(data):
    for i in range(len(data) - 6):
        [span_4](start_span)if data[i] == 0x38: # العلامة الاستدلالية من الكود المصدري[span_4](end_span)
            try:
                value, length = decode_varint(data, i + 1)
                if data[i + 1 + length] == 0x42:
                    return i + 1, length
            except: pass
    return None

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return "Missing file", 400
    
    file = request.files['file']
    new_uid = int(request.form.get('uid', 0))
    data = bytearray(file.read())
    
    res = find_uid(data)
    if res:
        start, length = res
        new_var = encode_varint(new_uid)
        # [span_5](start_span)تعديل البيانات في الذاكرة[span_5](end_span)
        modified_data = data[:start] + new_var + data[start + length:]
        
        output = io.BytesIO(modified_data)
        return send_file(output, 
                         mimetype='application/octet-stream',
                         as_attachment=True, 
                         download_name="Craftland_Modified.bytes")
    
    return "UID not found in file", 404

# ضروري لعمل Flask على Vercel
def handler(event, context):
    return app(event, context)
              
