#!/bin/bash

# Set DOCKER_CONFIG env variable
export DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}

# Create directory for Docker Compose plugin
mkdir -p $DOCKER_CONFIG/cli-plugins

# Download latest Docker Compose binary
LATEST_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -SL https://github.com/docker/compose/releases/download/$LATEST_VERSION/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose

# Apply executable permissions
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Install Docker (Ubuntu method)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add user to docker group
if grep -q docker /etc/group; then
    usermod -aG docker $USER
else
    groupadd docker
    usermod -aG docker $USER
fi

# Start Docker service (without sudo)
if [ -x "$(command -v systemctl)" ]; then
    systemctl --user enable docker
    systemctl --user start docker
else
    service docker start
fi

echo -e "\nDocker and Docker Compose installed successfully."
echo -e "\nYou'll need to:"
echo "1. Log out and back in for group changes to take effect"
echo "2. Run this command to activate the docker group in your current session:"
echo "   newgrp docker"
echo -e "\nVerify installation with:"
echo "docker --version && docker compose version"