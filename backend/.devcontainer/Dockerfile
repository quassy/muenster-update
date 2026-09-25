#-------------------------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See https://go.microsoft.com/fwlink/?linkid=2090316 for license information.
#-------------------------------------------------------------------------------------------------------------

# Update the VARIANT arg in compose.yaml to pick a Python version
ARG VARIANT=3.14
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/

# Keep the virtual environment out of the bind-mounted workspace, so it does
# not clash with a .venv created on the host
ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# This image includes a non-root user with sudo access. Use the "remoteUser" 
# property in devcontainer.json to use it. On Linux, update the values below 
# or in compose.yaml to ensure the container user's UID/GID matches your
# local values. See https://aka.ms/vscode-remote/containers/non-root-user for details.
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# [Optional] Update UID/GID if needed
RUN if [ "$USER_GID" != "1000" ] || [ "$USER_UID" != "1000" ]; then \
        groupmod --gid $USER_GID $USERNAME \
        && usermod --uid $USER_UID --gid $USER_GID $USERNAME \
        && chmod -R $USER_UID:$USER_GID /home/$USERNAME; \
    fi

RUN mkdir -p /opt/venv && chown $USER_UID:$USER_GID /opt/venv \
    && echo 'export PATH="/opt/venv/bin:$PATH"' > /etc/profile.d/01-venv.sh


# ** [Optional] Uncomment this section to install additional packages. **
#
# RUN apt-get update \
#     && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>


