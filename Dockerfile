# Use an official lightweight Python image
FROM python:3.12-slim

# 1. Update package lists and install Node.js + npm
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# 2. Globally install the MCP Inspector to prevent runtime downloads
RUN npm install -g @modelcontextprotocol/inspector

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Create a virtual environment and update core packaging tools
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the Neo4j driver (and any future requirements)
RUN pip install --no-cache-dir --upgrade pip

# Copy the requirements file into the container
COPY requirements.txt .

# Install the strictly pinned top-level dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the local application source code into the container
COPY . /app/

# Keep the container alive for execution or default to running the schema setup
CMD ["python", "setup_schema.py"]
