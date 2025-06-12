FROM python:3.11-slim

# Install system dependencies for OpenCV
# 使用国内镜像源解决 apt-get 问题
RUN apt-get update --allow-insecure-repositories && apt-get install -y --allow-unauthenticated \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# Copy the server code
COPY ut_dog_server.py .

# Expose port
EXPOSE 3000

# Run the server
CMD ["python", "ut_dog_server.py"] 