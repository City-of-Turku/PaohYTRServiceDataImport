FROM tiangolo/uvicorn-gunicorn:python3.8-slim

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 80

CMD ["python3", "/app/main.py"]


