FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /RequestBot

WORKDIR /RequestBot

COPY web/requirements.txt /RequestBot/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /RequestBot/

CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "RequestBot.wsgi:application"]
