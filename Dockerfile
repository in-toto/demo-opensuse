FROM opensuse/tumbleweed
LABEL org.opencontainers.image.authors="root@shikherverma.com"

RUN zypper --non-interactive install git in-toto python38-pip obs-service-download_files osc rpm-build sudo tree vim

WORKDIR /home
RUN git clone https://github.com/shikherverma/connman.git

RUN mkdir /home/demo-opensuse
WORKDIR /home/demo-opensuse
