FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wine32 \
        wine64 \
        python3 \
        python3-pip \
        python3-psutil \
        curl \
        wget \
        unzip \
        file \
        net-tools \
        procps \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install official Playit Agent directly into system PATH
RUN curl -SsL "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-linux-amd64" -o /usr/local/bin/playit && \
    chmod +x /usr/local/bin/playit

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

COPY --chown=user:user . /home/user/app

USER root
RUN chmod +x /home/user/app/start.sh || true
USER user

EXPOSE 10000 7860

CMD ["bash", "/home/user/app/start.sh"]
