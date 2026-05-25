# Use official lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose port (FastAPI will read from PORT env, default to 8000)
EXPOSE 8000

# Run the app via backend/main.py script to handle PORT env properly
CMD ["python", "backend/main.py"]
