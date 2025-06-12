FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY mem0/ ./mem0/

# Expose port
EXPOSE 8080

# Run the server
CMD ["python", "mem0/server.py", "--host", "0.0.0.0", "--port", "8080"] 