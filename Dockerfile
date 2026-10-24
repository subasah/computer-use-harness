# ==============================================================================
# NexusCUH Production Sandbox Container
# Isolated execution environment with Xvfb, XFCE4, xdotool, VNC & noVNC
# ==============================================================================

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install base utilities, virtual X11 display, desktop environment, and automation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    git \
    jq \
    ca-certificates \
    sudo \
    python3 \
    python3-pip \
    python3-venv \
    xvfb \
    xfce4 \
    xfce4-terminal \
    xdotool \
    scrot \
    imagemagick \
    x11vnc \
    novnc \
    websockify \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged sandbox user
RUN useradd -m -s /bin/bash -u 1000 sandboxuser && \
    echo "sandboxuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create workspace and log directories
RUN mkdir -p /home/sandboxuser/workspace /var/log && \
    chown -R sandboxuser:sandboxuser /home/sandboxuser /var/log

# Copy entrypoint script
COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Environment variables
ENV DISPLAY=:99
ENV RESOLUTION=1024x768x24
ENV HOME=/home/sandboxuser

USER sandboxuser
WORKDIR /home/sandboxuser/workspace

EXPOSE 5900 6080

ENTRYPOINT ["/usr/local/bin/start.sh"]
