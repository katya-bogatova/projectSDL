FROM python:3.11-slim

RUN pip install psycopg2-binary

WORKDIR /app
COPY app.py .

CMD ["python", "app.py"]