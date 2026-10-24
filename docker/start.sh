#!/bin/bash
set -e

# ==============================================================================
# NexusCUH Sandbox Container Entrypoint
# Initializes virtual X11 display, XFCE desktop, VNC server, and noVNC web streaming
# ==============================================================================

DISPLAY_NUM="${DISPLAY:-:99}"
RESOLUTION="${RESOLUTION:-1024x768x24}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

echo "[NexusCUH Sandbox] Starting Xvfb on ${DISPLAY_NUM} with resolution ${RESOLUTION}..."
Xvfb "${DISPLAY_NUM}" -screen 0 "${RESOLUTION}" -ac +extension GLX +render -noreset &
XVFB_PID=$!

export DISPLAY="${DISPLAY_NUM}"
sleep 1

echo "[NexusCUH Sandbox] Starting XFCE4 Window Manager..."
xfce4-session &
XFCE_PID=$!

echo "[NexusCUH Sandbox] Starting x11vnc server on port ${VNC_PORT}..."
x11vnc -display "${DISPLAY_NUM}" -forever -shared -nopw -rfbport "${VNC_PORT}" -bg -o /var/log/x11vnc.log

echo "[NexusCUH Sandbox] Starting noVNC web bridge on port ${NOVNC_PORT}..."
/usr/share/novnc/utils/launch.sh --listen "${NOVNC_PORT}" --vnc "localhost:${VNC_PORT}" > /var/log/novnc.log 2>&1 &

echo "[NexusCUH Sandbox] Desktop sandbox is ready."
echo "[NexusCUH Sandbox] Access live desktop in browser at: http://localhost:${NOVNC_PORT}/vnc.html"

# Trap termination signals
trap "kill -TERM ${XVFB_PID} ${XFCE_PID} 2>/dev/null || true; exit 0" SIGTERM SIGINT

# Keep process alive
tail -f /dev/null
