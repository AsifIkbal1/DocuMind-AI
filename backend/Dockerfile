FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR & image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/backend/
ENV PYTHONPATH=/app
ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

