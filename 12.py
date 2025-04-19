import csv
import os
from google import genai
import pandas as pd

# 设置 API 密钥
os.environ['GEMINI_API_KEY'] = 'AIzaSyDHc8OiZIFvegbLyweud1NJbf6LIcDZDbQI'
model = genai.GenerativeModel('gemini-2.0-flash')

# 分析函数
def analyze_text(text):
    result = {}

    # 关键词
    prompt_keywords = f"""你是一位文本分析专家。请你从以下文本中提取 10 个最具代表性的关键词，用中文输出列表格式：
    要求：不使用英文、不扩展含义、不添加注释。仅输出关键词列表。
    文本如下：
    {text}"""
    result["keywords"] = model.generate_content(prompt_keywords).text.strip()

    # 主题建模
    prompt_topics = f"""你是一位主题建模专家。请你模拟 LDA 主题建模，对以下中文文本提取 3 个潜在主题。
    输出要求：
    - 每个主题给出一个清晰的主题标签（5个字以内）
    - 每个主题列出3~5个关键词
    - 使用 Markdown 格式输出（标题+关键词）
    文本如下：
    {text}"""
    result["topics"] = model.generate_content(prompt_topics).text.strip()

    # 情感分析
    prompt_sentiment = f"""请你对下面的中文文本进行情感倾向分析，判断其总体情绪是正面、中性还是负面，并简要说明理由（不超过50字）。
    文本如下：
    {text}"""
    result["sentiment"] = model.generate_content(prompt_sentiment).text.strip()

    return result

# 批量处理 CSV 中 E、H、K 三列（索引4, 7, 10）
csv_path = r"C:\composition ai\feedback_log.csv"
results = []

with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    headers = next(reader)
    for i, row in enumerate(reader, start=1):
        for label, idx in [('GPT-4o', 4), ('DeepSeek', 7), ('Gemini', 10)]:
            if idx < len(row) and row[idx].strip():
                text = row[idx].strip()
                print(f"分析第 {i} 行 {label} 内容中...")
                res = analyze_text(text)
                res.update({
                    "row": i,
                    "model": label,
                    "text": text
                })
                results.append(res)

# 输出结果为 CSV
df = pd.DataFrame(results)
df.to_csv(r"C:\composition ai\model_feedback_analysis.csv", encoding="utf-8-sig", index=False)
print("✅ 分析完成，结果已保存")
