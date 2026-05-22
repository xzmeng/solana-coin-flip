FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# uv — system-wide install (no official devcontainer feature exists)
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Solana CLI — no official feature; install to system path via symlinks
RUN sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)" \
    && find /root/.local/share/solana/install/active_release/bin -maxdepth 1 -type f \
       -exec ln -sf {} /usr/local/bin/ \;
