FROM python:3.12

WORKDIR /cron

COPY requirements.txt /cron/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /cron/

CMD ["python3", "price_updater.py"]
