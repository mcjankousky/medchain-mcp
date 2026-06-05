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
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir neo4j>=5.14.0 pydantic==2.6.4 rapidfuzz==3.6.2 google-genai~=0.1.0

#Install requirements for testing
RUN pip install --no-cache-dir pytest==8.1.1

# Copy the local application source code into the container
COPY . /app/

# Keep the container alive for execution or default to running the schema setup
CMD ["python", "setup_schema.py"]
