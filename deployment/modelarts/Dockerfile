FROM python:3.11-slim

LABEL maintainer="jarvis-team@example.com"

WORKDIR /workspace

# Install minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy repository requirements if present; you can customize for your env
COPY backend/requirements.txt /workspace/backend-requirements.txt
RUN pip install --upgrade pip setuptools && \
    pip install -r /workspace/backend-requirements.txt

# TODO: Add MindSpore wheel installation steps for Ascend/MindSpore here.
# MindSpore wheels are platform and device specific. Installing for Ascend 910
# requires matching driver and runtime. Keep the heavy-install step commented
# out in this repo; instead create a custom image for Ascend CI.

COPY . /workspace

ENTRYPOINT ["python", "-m", "deployment.modelarts.deploy_model"]
