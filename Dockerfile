FROM python:2.7-slim

RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid 1001 --shell /usr/sbin/nologin app

ENV LANG C.UTF-8

WORKDIR /app

# S3 bucket in Cloud Services prod IAM
ADD https://s3.amazonaws.com/dumb-init-dist/v1.2.0/dumb-init_1.2.0_amd64 /usr/local/bin/dumb-init
RUN chmod +x /usr/local/bin/dumb-init
ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]

COPY ./requirements.txt /app/requirements.txt
COPY ./dev-requirements.txt /app/dev-requirements.txt


# install syncserver dependencies
RUN apt-get -q update \
    && apt-get -q --yes install g++ \
    && pip install --upgrade --no-cache-dir -r requirements.txt \
    && pip install --upgrade --no-cache-dir -r dev-requirements.txt \
    && apt-get -q --yes remove g++ \
    && apt-get -q --yes autoremove \
    && apt-get clean


COPY ./syncserver /app/syncserver
COPY ./setup.py /app
COPY . /app
RUN python ./setup.py develop

# run as non priviledged user
USER app
