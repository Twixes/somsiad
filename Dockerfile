FROM python:3.11
ENV PYTHONUNBUFFERED 1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        locales tzdata python3-psycopg2 libffi-dev libssl-dev libsodium-dev libnacl-dev libopus-dev libjpeg-dev \
        libpq-dev ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-pol \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# tiktoken needs Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH /root/.cargo/bin:$PATH
ENV LC_ALL pl_PL.UTF-8
ENV TZ Europe/Warsaw
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata
RUN curl -sL https://sentry.io/get-cli/ | bash && \
    sentry-cli update
RUN sed -i -e "s/# $LC_ALL UTF-8/$LC_ALL UTF-8/" /etc/locale.gen && \
    locale-gen
RUN pip install uv

WORKDIR /code/

COPY pyproject.toml uv.lock ./

RUN SODIUM_INSTALL=system uv sync --no-dev --compile-bytecode --locked
COPY . .

CMD ["python", "run.py"]
