FROM python:3.11-slim

# Install system dependencies including X11 libraries for AI2Thor
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    libx11-6 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglu1-mesa \
    libegl1-mesa \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY ai2thor/ ./ai2thor/

# Set display for headless operation
ENV DISPLAY=:99

# Create logs directory
RUN mkdir -p envs/thor_env/logs

# Expose port
EXPOSE 3001

# Start Xvfb and run the server
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset & python ai2thor/thor_mcp_server.py"] 