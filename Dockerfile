# 使用完整版 Python 镜像（非 slim）
FROM python:3.10

# 设置工作目录
WORKDIR /app

# 拷贝代码
COPY . /app

# 升级 pip
RUN pip install --upgrade pip

# 安装依赖
RUN pip install -r requirements.txt

# 暴露 Flask 默认端口
EXPOSE 5000

# 启动服务
CMD ["python", "app.py"]
