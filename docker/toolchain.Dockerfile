FROM ubuntu@sha256:186072bba1b2f436cbb91ef2567abca677337cfc786c86e107d25b7072feef0c

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       binutils-arm-none-eabi \
       ca-certificates \
       gcc \
       gcc-arm-none-eabi \
       libc6-dev \
       make \
       python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
CMD ["make"]
