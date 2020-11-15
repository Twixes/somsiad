FROM python:3.8.6
ENV PYTHONUNBUFFERED 1
ENV TZ Europe/Warsaw
RUN apt-get update && \
    apt-get install -y locales tzdata python3-psycopg2 libffi-dev libnacl-dev libopus-dev libjpeg-dev libpq-dev ffmpeg && \
    apt-get upgrade -y
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata
RUN curl -sL https://sentry.io/get-cli/ | bash && \
    sentry-cli update
RUN sed -i -e "s/# pl_PL.UTF-8 UTF-8/pl_PL.UTF-8 UTF-8/" /etc/locale.gen && \
    locale-gen
WORKDIR /code
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -U pip setuptools wheel
RUN pip3 install --no-cache-dir -U -r requirements.txt
COPY . .
CMD python3 run.py
