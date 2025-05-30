FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the VLM source code and server
COPY src/ ./src/
COPY vlm_r1_server.py .

# Create images directory
RUN mkdir -p images

# Expose port
EXPOSE 8009

# Run the server
CMD ["python", "vlm_r1_server.py", "--model-path", "omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321", "--device", "cuda:0"] 