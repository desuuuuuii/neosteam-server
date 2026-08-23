FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all

# Install Wine 32-bit + Python + Utilities
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
        net-tools \
        procps \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create Hugging Face user (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Copy server files
COPY --chown=user:user . /home/user/app

# Set execution permissions
USER root
RUN chmod +x /home/user/app/start.sh || true
USER user

EXPOSE 7860

CMD ["bash", "/home/user/app/start.sh"]
