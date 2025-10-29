# ---- Base Stage ----
# Start from a lightweight and official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1  # Prevents python from writing .pyc files
ENV PYTHONUNBUFFERED 1         # Ensures logs are sent straight to the terminal

# Set the working directory inside the container
WORKDIR /app

# ---- Dependencies Stage ----
# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies (needed for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# ---- Application Stage ----
# Copy the rest of your application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x ./entrypoint.sh

# Expose the port the app will run on (matches main.py)
EXPOSE 8000

# ---- Run Stage ----
# Set the entrypoint to our script
ENTRYPOINT ["./entrypoint.sh"]

# The command that the entrypoint will run *after* migrations
# This starts Gunicorn with Uvicorn workers for FastAPI
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]
