FROM python:3.11-bullseye

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir app
COPY app/ app/

CMD ["bokeh", "serve", "app", "--port", "8080"]
