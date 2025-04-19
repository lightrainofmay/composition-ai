# 保留原有功能，新增多页上传与批量上传接口（同时保留原OCR展示、模型评改、进度反馈功能）
from flask import Flask, request, jsonify, render_template, send_file
import requests
import os
import time
import csv
import re
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
import base64
import urllib.parse
from openai import OpenAI
from google import genai
from datetime import datetime

# ====== 加载环境变量 ======
load_dotenv()
GPT_API_KEY = os.getenv("GPT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")

client_deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ====== CSV 文件结构初始化 ======
FEEDBACK_LOG = "feedback_log.csv"
FIELDNAMES = [
    "id",
    "ocr_text", "ocr_score", "score_ocr",
    "gpt_result", "score_gpt", "gpt_duration",
    "deepseek_result", "score_deepseek", "deepseek_duration",
    "gemini_result", "score_gemini", "gemini_duration",
    "user_comment", "used_time", "timestamp"
]
if not os.path.exists(FEEDBACK_LOG) or os.stat(FEEDBACK_LOG).st_size == 0:
    with open(FEEDBACK_LOG, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

# ====== 工具函数 ======
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_baidu_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

BAIDU_ACCESS_TOKEN = get_baidu_access_token()

def baidu_ocr(image_path):
    with open(image_path, "rb") as f:
        img_data = f.read()
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    img_base64 = urllib.parse.quote_plus(img_base64)

    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token={BAIDU_ACCESS_TOKEN}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = f"image={img_base64}&detect_direction=false&probability=false&detect_alteration=false"

    response = requests.post(ocr_url, headers=headers, data=payload)
    result = response.json()
    words_result = result.get('words_result', [])
    words = [item['words'] for item in words_result]
    total_chars = sum(len(item['words']) for item in words_result)
    score = min(round(total_chars / 10, 1), 10.0)
    raw_text = '\n'.join(words)

    prompt = (
        "请你对以下文字进行排版优化，仅合并错误换行，恢复自然段落\n"
        "注意：不要添加、删除或改写任何句子或词语，只做格式调整。排版请符合中文写作的版式要求，首段应空两个字\n\n"
        f"{raw_text}"
    )
    try:
        gemini_response = client_gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        formatted_text = gemini_response.text
    except Exception as e:
        formatted_text = raw_text + "\n（⚠️ 排版失败，返回原始内容）"

    return formatted_text, score

def generate_common_prompt(text):
    return (
        "你是一位经验丰富的中学语文老师，请根据义务教育《语文课程标准（2022年版）》对7切对 7-9 年级学生写作的要求，全面评改以下学生作文，并提供有针对性的指导建议：\n"
        "1. 请指出作文中存在的字词、标点和语法错误；\n"
        "2. 从以下方面分析作文的优缺点：\n"
        "   - 是否有真情实感，是否表达了作者对生活、社会或自然的真实感受；\n"
        "   - 是否围绕中心有条理地展开，内容是否充实、结构是否合理；\n"
        "   - 是否掌握了所写文体的基本特点（如记叙文的情节描述，议论文的论点和论据等）；\n"
        "   - 是否具备一定的创新性和表达力，语言是否得体、流畅；\n"
        "3. 请根据上述分析，给出详细、具体的修改建议；\n"
        "4. 综合考虑内容、表达、结构和语言使用等方面，为该作文打一个总分（0~100分）；\n"
        "5. 最后，请根据原文内容，写出一篇经过修改和提升的高质量范文，不少于 600 字，符合七至九年级语文作文要求\n\n"
        f"学生作文如下：\n{text}"
    )

def extract_student_name(filename):
    match = re.match(r"^([\u4e00-\u9fa5a-zA-Z0-9]+)[_\-－]?\d*\.(jpg|jpeg|png)$", filename, re.IGNORECASE)
    if match:
        return match.group(1)
    return re.sub(r"\.(jpg|jpeg|png)$", "", filename, flags=re.IGNORECASE)


@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "No file part"}), 400

    all_text = []
    for file in files:
        if file.filename == '' or not allowed_file(file.filename):
            continue
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text, ocr_score = baidu_ocr(filepath)
        all_text.append(text)

    full_text = '\n'.join(all_text)
    return jsonify({"ocr_text": full_text, "ocr_score": ocr_score, "filename": files[0].filename})

@app.route('/analyze_gpt', methods=['POST'])
def analyze_gpt():
    try:
        text = request.json.get("text", "")
        headers = {"Authorization": f"Bearer {GPT_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": generate_common_prompt(text)}]}
        start = time.time()
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        duration = round(time.time() - start, 2)
        result = response.json()
        return jsonify({"result": result["choices"][0]["message"]["content"], "duration": duration})
    except Exception as e:
        return jsonify({"result": f"GPT 调用失败：{e}", "duration": 0})

@app.route('/analyze_gemini', methods=['POST'])
def analyze_gemini():
    try:
        text = request.json.get("text", "")
        start = time.time()
        response = client_gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=generate_common_prompt(text)
        )
        duration = round(time.time() - start, 2)
        return jsonify({"result": response.text, "duration": duration})
    except Exception as e:
        return jsonify({"result": f"Gemini 调用失败：{e}", "duration": 0})

@app.route('/analyze_deepseek', methods=['POST'])
def analyze_deepseek():
    try:
        text = request.json.get("text", "")
        start = time.time()
        response = client_deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": generate_common_prompt(text)}]
        )
        duration = round(time.time() - start, 2)
        return jsonify({"result": response.choices[0].message.content, "duration": duration})
    except Exception as e:
        return jsonify({"result": f"DeepSeek 调用失败：{e}", "duration": 0})

@app.route('/upload_multi_page', methods=['POST'])
def upload_multi_page():
    return upload()

@app.route('/upload_batch_users', methods=['POST'])
def upload_batch_users():
    files = request.files.getlist("files")
    grouped = {}
    for file in files:
        orig_filename = file.filename  # 保留原始中文文件名
        name = extract_student_name(orig_filename)  # 正确识别中文名
        filename = f"{int(time.time()*1000)}_{orig_filename}"  # 防止中文重名
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        grouped.setdefault(name, []).append(filepath)

    results = []
    for student, filepaths in grouped.items():
        all_text = []
        for path in sorted(filepaths):
            text, _ = baidu_ocr(path)
            all_text.append(text)
        full_text = '\n'.join(all_text)
        prompt = generate_common_prompt(full_text)
        response = client_deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        results.append({"student": student, "result": result})

    return jsonify({"results": results})

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/download_feedback')
def download_feedback():
    return send_file(FEEDBACK_LOG, as_attachment=True)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(FEEDBACK_LOG, encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            idx = len(rows)
        row = [
            idx,
            data.get("ocr_text", ""),
            data.get("ocr_score", ""),
            data.get("score_ocr", ""),
            data.get("gpt_4o_feedback", ""),
            data.get("score_gpt", ""),
            data.get("gpt_duration", ""),
            data.get("deepseek_reasoner_feedback", ""),
            data.get("score_deepseek", ""),
            data.get("deepseek_duration", ""),
            data.get("gemini_flash_feedback", ""),
            data.get("score_gemini", ""),
            data.get("gemini_duration", ""),
            data.get("user_comment", ""),
            data.get("used_time", ""),
            now
        ]
        with open(FEEDBACK_LOG, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        return jsonify({"message": "反馈已保存"})
    except Exception as e:
        return jsonify({"error": f"保存失败：{e}"})

if __name__ == '__main__':
    print("✅ Flask 正在启动...")
    app.run(host='0.0.0.0', port=5000, debug=True)
