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

# Install system dependencies (needed if you use packages like psycopg2 for PostgreSQL)
# RUN apt-get update && apt-get install -y some-package && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application Stage ----
# Copy the rest of your application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x ./entrypoint.sh

# Expose the port the app will run on (for Gunicorn)
EXPOSE 5000

# ---- Run Stage ----
# Set the entrypoint to our script
ENTRYPOINT ["./entrypoint.sh"]

# The command that the entrypoint will run *after* migrations
# This starts the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
