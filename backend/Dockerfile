# Backend Dockerfile - Python 3.12 with NER Support
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set Python path to include /app
ENV PYTHONPATH=/app:$PYTHONPATH

# Install system dependencies including build tools for spaCy
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    libgl1 \
    libglib2.0-0 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
    
# Copy requirements file for Python 3.12
COPY requirements_py312.txt .

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_py312.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs models

# Train NER model if training data exists
RUN if [ -f "train_ner_quick.py" ]; then python train_ner_quick.py; fi

# Expose port (default 8000 if PORT not set)
EXPOSE ${PORT:-8000}

# Run application with main_refactored.py (includes NER)
CMD uvicorn main_refactored:app --host 0.0.0.0 --port ${PORT:-8000}
