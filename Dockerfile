FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-psutil \
        curl \
        wget \
        tar \
        net-tools \
        procps \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

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
