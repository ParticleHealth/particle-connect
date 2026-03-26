FROM python:3.12-slim

WORKDIR /app

# requirements.txt is at project root, backend code is in backend/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Create data dir for SQLite
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
