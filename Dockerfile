FROM python:2.7-alpine

RUN addgroup -g 1001 app \
    && adduser -u 1001 -S -D -G app -s /usr/sbin/nologin app

ENV LANG C.UTF-8

WORKDIR /app

# install syncserver dependencies
COPY ./requirements.txt /app/requirements.txt
COPY ./dev-requirements.txt /app/dev-requirements.txt
# install the base set of libraries if they're not present.
# NOTE: please update the README to include any changes.
RUN apk --no-cache update \
    && apk add bash dumb-init gcc libstdc++ libffi-dev make mysql-dev musl-dev ncurses-dev openssl-dev g++ \
    && pip install --upgrade pip \
    && pip install --upgrade --no-cache-dir -r requirements.txt \
    && pip install --upgrade --no-cache-dir -r dev-requirements.txt \
    && apk del g++

COPY . /app
RUN python ./setup.py develop

# run as non priviledged user
USER app

# run the server by default
ENTRYPOINT ["/usr/bin/dumb-init", "/app/docker-entrypoint.sh"]
CMD ["server"]
