FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

RUN pip install packaging uv -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY vlm_r1.py .
COPY torch-2.1.0+cu121-cp311-cp311-linux_x86_64.whl .
COPY models--omlab--VLM-R1-Qwen2.5VL-3B-OVD-0321 .cache/huggingface/hub/models--omlab--VLM-R1-Qwen2.5VL-3B-OVD-0321/

RUN uv venv
RUN uv pip install --no-cache-dir -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# Copy the VLM source code and server
COPY src/ ./src/
COPY vlm_r1_server.py .

# Create images directory
RUN mkdir -p images

# Expose port
EXPOSE 8009

# Run the server
CMD ["python", "vlm_r1_server.py", "--model-path", "omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321", "--device", "cuda:0"] 