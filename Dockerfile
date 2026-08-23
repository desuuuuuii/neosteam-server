FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all
ENV WINEDLLOVERRIDES="mscoree,mshtml="
ENV WINEPREFIX=/home/user/.wine
ENV DISPLAY=:99

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wine \
        wine32:i386 \
        wine64 \
        libodbc2:i386 \
        odbcinst1debian2:i386 \
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

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Pre-initialize Wine prefix during build so runtime boot is instant (0.1s)
RUN Xvfb :99 -screen 0 1024x768x16 -nolisten unix -nolisten tcp & \
    sleep 1 && \
    wineboot --init && \
    wineserver -w && \
    pkill -9 -f Xvfb || true

WORKDIR /home/user/app

COPY --chown=user:user . /home/user/app

# Extract authentic server engine during build
RUN if [ -f "/home/user/app/microserver.zip" ]; then \
        unzip -q /home/user/app/microserver.zip -d /home/user/app/MicroServer && \
        rm /home/user/app/microserver.zip ; \
    fi

USER root
RUN chmod +x /home/user/app/start.sh || true
USER user

EXPOSE 10000 7860

CMD ["bash", "/home/user/app/start.sh"]
