# ✍️ 中小学作文识别与智能评改系统 V1.0

本项目是一个基于 Flask、OCR、和多种大语言模型（LLM）的中文作文识别与智能评改系统，支持自动识别手写作文、调用 GPT-4o、Gemini Flash、DeepSeek Reasoner 等模型进行个性化评语生成，并支持结果反馈记录和导出。适用于教师辅助批改、学生作文练习和 AI 教育应用研究。

![界面截图](https://your-screenshot-url) <!-- 可上传截图到 GitHub Issues 或其他图床后粘贴链接 -->

---

## 🚀 核心功能

- 📷 **OCR 自动识别手写作文图片（百度手写 OCR）**
- 🤖 **GPT-4o 智能分析与修改建议**
- 🌈 **Gemini Flash 中文写作智能评分与建议**
- 🧠 **DeepSeek Reasoner 作文结构与逻辑分析**
- 📥 **导出 CSV 反馈结果，含评分与建议**
- 🌐 **支持通过 Cloudflare Tunnel 映射公网访问**
- 🐳 **可使用 Docker 镜像快速部署**

---

## 🛠️ 使用技术

- 后端框架：Flask
- 前端：原生 HTML + JS + marked.js
- OCR：百度智能云 手写文字识别 API
- 大模型支持：
  - OpenAI GPT-4o
  - Gemini Flash (google-generativeai)
  - DeepSeek Reasoner V3
- 数据导出：CSV
- 部署方式：Docker + Cloudflare Tunnel

---

## 📦 部署方式（推荐）

### ✅ 使用 Docker 启动

1. **构建镜像：**

   ```bash
   docker build -t composition-ai .
   ```

2. **运行容器：**

   ```bash
   docker run -d \
     --name composition-ai \
     --env-file .env \
     --restart unless-stopped \
     -p 5050:5000 \
     yourdockerhub/composition-ai
   ```

---

### 🌍 开放公网访问（Cloudflare Tunnel）

1. 安装 cloudflared：
   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install/

2. 创建并配置 tunnel：

   ```bash
   cloudflared tunnel create my-composition-tunnel
   ```

3. 编辑 `config.yml`：

   ```yaml
   tunnel: a6460e8e-xxxx-yyyy-zzzz-xxxx
   credentials-file: C:\Users\xxx\.cloudflared\a6460e8e-xxx.json

   ingress:
     - hostname: composition.xiaoyu-zhou.xyz
       service: http://localhost:5000
     - service: http_status:404
   ```

4. 启动 tunnel：

   ```bash
   cloudflared tunnel --config "C:\your_path\config.yml" run my-composition-tunnel
   ```

---

## 🧪 使用说明

1. 上传手写作文图片（支持 JPG、PNG）
2. 系统自动进行 OCR 并调用三个大模型分析
3. 显示每个模型的建议与评分
4. 用户可以自定义评分与评价
5. 点击“提交反馈”即可保存至 CSV
6. 可点击“下载反馈数据”导出所有历史反馈

---

## 📁 项目结构

```
├── app.py                 # Flask 主程序
├── templates/
│   └── index.html         # 前端页面
├── Dockerfile             # 构建镜像所需 Dockerfile
├── .env                   # API 密钥配置（不上传 GitHub）
├── requirements.txt       # Python 依赖
├── feedback_log.csv       # 反馈数据自动生成
├── README.md              # 项目说明
```

---

## 🔒 环境变量配置（`.env`）

你需要在 `.env` 文件中配置以下内容：

```env
GPT_API_KEY=sk-xxx
GEMINI_API_KEY=your_google_genai_key
DEEPSEEK_API_KEY=your_deepseek_key
BAIDU_API_KEY=your_baidu_key
BAIDU_SECRET_KEY=your_baidu_secret
```

---

## 📤 Docker Hub 镜像

> 镜像地址：[https://hub.docker.com/r/yourusername/composition-ai](https://hub.docker.com/r/lightrainofmay/composition-ai)

---

## 📬 联系方式与贡献

欢迎教育工作者与开发者共同优化本项目。如有建议或合作意向，请通过 GitHub Issues 联系或发起 PR。

---

## 📝 License

本项目采用 [MIT License](LICENSE) 许可协议开源。

---

✉️ Powered by AI + 教育创新  
