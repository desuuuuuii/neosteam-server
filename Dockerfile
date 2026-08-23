FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all
ENV DISPLAY=:99

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wine \
        wine32:i386 \
        wine64 \
        xvfb \
        xauth \
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

# Fix /tmp permissions for non-root Wine & Xvfb sockets
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp /tmp/.X11-unix

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    XDG_RUNTIME_DIR=/tmp

WORKDIR /home/user/app

COPY --chown=user:user . /home/user/app

# Extract authentic server engine
RUN if [ -f "/home/user/app/microserver.zip" ]; then \
        unzip -q /home/user/app/microserver.zip -d /home/user/app/MicroServer && \
        rm /home/user/app/microserver.zip ; \
    fi

USER root
RUN chmod +x /home/user/app/start.sh || true
USER user

EXPOSE 10000 7860

CMD ["bash", "/home/user/app/start.sh"]
