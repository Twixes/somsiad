FROM python:3.8.6
ENV PYTHONUNBUFFERED 1
ENV LC_ALL pl_PL.UTF-8
ENV TZ Europe/Warsaw
ENV FLASK_RUN_HOST=0.0.0.0

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install --no-install-recommends -y locales tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata
RUN sed -i -e "s/# $LC_ALL UTF-8/$LC_ALL UTF-8/" /etc/locale.gen && \
    locale-gen

WORKDIR /code/

COPY requirements.txt ./
RUN pip install --no-cache-dir -U -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app"]
