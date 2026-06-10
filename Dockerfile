# Use an official lightweight Python image
FROM python:3.12-slim

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
