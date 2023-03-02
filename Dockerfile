FROM python:3.9

WORKDIR /code/app

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
RUN mkdir -p /code/app/replays

CMD ["gunicorn", "--conf", "./gunicorn_conf.py", "--bind", "0.0.0.0:80", "main:app"]
