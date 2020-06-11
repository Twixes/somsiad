FROM python:3.7.7
ENV PYTHONUNBUFFERED 1
RUN apt-get update && \
    apt-get install -y locales python3-psycopg2 libffi-dev libnacl-dev libopus-dev libjpeg-dev libpq-dev ffmpeg
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# pl_PL.UTF-8 UTF-8/pl_PL.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
WORKDIR /code
COPY requirements.txt ./
RUN pip3.7 install --no-cache-dir -U -r requirements.txt
COPY . .
CMD python3.7 core.py
