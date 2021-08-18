FROM python:3.9
ENV PYTHONUNBUFFERED 1
ENV LC_ALL pl_PL.UTF-8
ENV TZ Europe/Warsaw

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install --no-install-recommends -y locales tzdata python3-psycopg2 libffi-dev libnacl-dev libopus-dev libjpeg-dev libpq-dev ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata
RUN curl -sL https://sentry.io/get-cli/ | bash && \
    sentry-cli update
RUN sed -i -e "s/# $LC_ALL UTF-8/$LC_ALL UTF-8/" /etc/locale.gen && \
    locale-gen

WORKDIR /code/

COPY requirements.txt ./
RUN pip install --no-cache-dir -U -r requirements.txt

COPY . .

CMD ["python", "run.py"]
