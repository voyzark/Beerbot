FROM python:latest

WORKDIR /build
COPY requirements.txt /build
RUN pip install -r requirements.txt
RUN rm -r /build

WORKDIR /app
COPY src/*.py /app/

CMD ["python", "main.py"]