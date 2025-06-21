#!/bin/bash

# === FusionFX VPS Bootstrap Script ===

echo "🚀 Initializing Hetzner VPS for FusionFX..."

# Update & install dependencies
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip docker.io docker-compose git ufw

# Create project structure
mkdir -p ~/fusionfx-forever
cd ~/fusionfx-forever

# Clone your repo (replace with your actual repo)
git clone https://github.com/Tarra732/fusionfx-forever.git .

# Install Python deps
pip3 install -r requirements.txt

# Enable firewall (optional)
sudo ufw allow ssh
sudo ufw allow 5000:6000/tcp
sudo ufw enable

echo "✅ VPS setup complete. Run 'docker-compose up --detach' to start FusionFX."