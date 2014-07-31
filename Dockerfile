##########################################################
#                  /!\ WARNING /!\                       #
# This is completely experimental. Use at your own risk. #
#             Also, learn you some docker:               #
#           http://docker.io/gettingstarted              #
##########################################################

FROM debian:7.4
MAINTAINER Dan Callahan <dan.callahan@gmail.com>

# Base system setup

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && apt-get install --no-install-recommends -y \
    vim locales \
    && apt-get clean

RUN locale-gen C.UTF-8 && LANG=C.UTF-8 /usr/sbin/update-locale

ENV LANG C.UTF-8

RUN useradd --create-home app

# Build the Sync server

RUN DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    ca-certificates \
    build-essential \
    libzmq-dev \
    python-dev \
    python-virtualenv \
    && apt-get clean

USER app

RUN mkdir -p /home/app/syncserver
ADD ./ /home/app/syncserver
WORKDIR /home/app/syncserver

RUN make build

# Run the Sync server

EXPOSE 5000

ENTRYPOINT ["/usr/bin/make"]
CMD ["serve"]
