# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install omagent_core as an editable package
RUN pip install -e omagent-core

# Install all other dependencies
RUN pip install -r requirements.txt

# Expose a port to allow external connections to the container
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]
