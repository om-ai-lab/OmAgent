FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY src/ ./src/
COPY standalone_embed.sh ./
# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "-m", "src.mcp_server_milvus.server", "--sse", "--port", "8000"] 