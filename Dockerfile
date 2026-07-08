# Use a slim Python image for a smaller footprint
FROM python:3.12-slim

# 💡 關鍵：強制 Python 立即將 stdout/stderr 輸出到終端機，不進行快取快取
ENV PYTHONUNBUFFERED=1

# Set the internal working directory
WORKDIR /app

# Copy requirements and install them first to leverage build caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir jinja2
# Copy main.py, templates, and remaining project files
COPY api/ .

# Start your chatbot application
CMD ["python", "main.py"]
