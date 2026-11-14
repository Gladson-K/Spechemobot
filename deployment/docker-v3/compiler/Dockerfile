ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION}

ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build git curl wget python3 python3-pip python3-dev \
    clang clangd lldb llvm llvm-dev lld libclang-dev libtinfo-dev zlib1g-dev \
    libxml2-dev libzstd-dev libedit-dev pkg-config ccache gdb \
    ruby-full ruby-dev bundler \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    if ! getent group "${USER_GID}" >/dev/null; then groupadd -g "${USER_GID}" dev; fi; \
    if ! getent passwd "${USER_UID}" >/dev/null; then useradd -m -u "${USER_UID}" -g "${USER_GID}" -s /bin/bash dev; fi; \
    user_name="$(getent passwd "${USER_UID}" | cut -d: -f1)"; \
    install -d -m 0755 -o "${USER_UID}" -g "${USER_GID}" /home/dev; \
    if getent group video >/dev/null; then usermod -aG video "${user_name}" || true; fi; \
    chown -R "${USER_UID}:${USER_GID}" /home/dev

ENV HOME=/home/dev

USER ${USER_UID}:${USER_GID}
WORKDIR /workspace/Spechemobot
CMD ["bash"]
