import requests
import os
import time
import random

BASE_URL = "http://localhost:5000"  # 修改为你的服务地址
IMAGE_FOLDER = r"C:\Users\Administrator\Desktop\temp\楚师学报\默认班级-主题：“换位人生”——用不同主体讲述同一事件(word)\all_images_only"

def evaluate_one_image(image_path):
    print(f"\n📤 上传图片：{image_path}")
    
    with open(image_path, 'rb') as f:
        upload_res = requests.post(f"{BASE_URL}/upload", files={"file": f})
    upload_data = upload_res.json()

    if "ocr_text" not in upload_data:
        print("❌ OCR 失败：", upload_data.get("error"))
        return

    ocr_text = upload_data["ocr_text"]
    ocr_score = upload_data["ocr_score"]

    print("🧠 GPT-4o 分析中...")
    gpt_res = requests.post(f"{BASE_URL}/analyze_gpt", json={"text": ocr_text}).json()
    gpt_feedback = gpt_res.get("result", "")
    gpt_duration = gpt_res.get("duration", 0)

    print("🌈 Gemini 分析中...")
    gemini_res = requests.post(f"{BASE_URL}/analyze_gemini", json={"text": ocr_text}).json()
    gemini_feedback = gemini_res.get("result", "")
    gemini_duration = gemini_res.get("duration", 0)

    print("🔍 DeepSeek 分析中...")
    deep_res = requests.post(f"{BASE_URL}/analyze_deepseek", json={"text": ocr_text}).json()
    deep_feedback = deep_res.get("result", "")
    deep_duration = deep_res.get("duration", 0)

    # ✅ 生成随机评分（7 到 10 分之间）
    score_ocr = round(random.uniform(7.0, 10.0), 1)
    score_gpt = round(random.uniform(7.0, 10.0), 1)
    score_gemini = round(random.uniform(7.0, 10.0), 1)
    score_deepseek = round(random.uniform(7.0, 10.0), 1)

    feedback_data = {
        "ocr_text": ocr_text,
        "ocr_score": ocr_score,
        "score_ocr": score_ocr,
        "gpt_4o_feedback": gpt_feedback,
        "score_gpt": score_gpt,
        "gpt_duration": gpt_duration,
        "deepseek_reasoner_feedback": deep_feedback,
        "score_deepseek": score_deepseek,
        "deepseek_duration": deep_duration,
        "gemini_flash_feedback": gemini_feedback,
        "score_gemini": score_gemini,
        "gemini_duration": gemini_duration,
        "user_comment": "",
        "used_time": 0
    }

    feedback_res = requests.post(f"{BASE_URL}/submit_feedback", json=feedback_data)
    if feedback_res.ok:
        print(f"✅ 提交成功 | GPT: {score_gpt}, Gemini: {score_gemini}, DeepSeek: {score_deepseek}")
    else:
        print("❌ 提交失败：", feedback_res.text)

if __name__ == "__main__":
    image_files = sorted([f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    print(f"共准备 {len(image_files)} 张图片进行评测...")

    for img_file in image_files:
        img_path = os.path.join(IMAGE_FOLDER, img_file)
        evaluate_one_image(img_path)
        time.sleep(2)  # 可调节间隔时间
