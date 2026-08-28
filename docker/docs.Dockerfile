FROM ubuntu@sha256:186072bba1b2f436cbb91ef2567abca677337cfc786c86e107d25b7072feef0c

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       binutils-arm-none-eabi \
       ca-certificates \
       doxygen \
       gcc \
       gcc-arm-none-eabi \
       git \
       libc6-dev \
       make \
       python3 \
       python3-pip \
       python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY docs/requirements.txt /tmp/libwipi-docs-requirements.txt
RUN python3 -m venv /opt/libwipi-docs \
    && /opt/libwipi-docs/bin/pip install --no-cache-dir \
       -r /tmp/libwipi-docs-requirements.txt

ENV PATH="/opt/libwipi-docs/bin:${PATH}"
WORKDIR /work
CMD ["python", "tools/build_docs.py"]
