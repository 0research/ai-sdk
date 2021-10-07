   
FROM python:3-slim AS builder
ADD . /app
WORKDIR /app

# Install Dependencies & Install git
RUN pip install --target=/app -r requirements.txt
RUN apt-get update && apt-get install -y git

ENV PYTHONPATH /app
CMD ["python", "/app/app.py"]