FROM python:3.9-slim
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . ./
EXPOSE 8050
CMD gunicorn --bind 0.0.0.0:8050 index:server
