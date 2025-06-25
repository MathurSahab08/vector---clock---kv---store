# Dockerfile
FROM python:3.12.2
WORKDIR /app
COPY src/ .
RUN pip install flask requests
CMD ["python3", "node.py"]
