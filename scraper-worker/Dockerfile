FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Workers don't need exposed ports, they just run continuously
CMD ["python", "-u", "worker.py"]