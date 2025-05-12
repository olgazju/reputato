#!/bin/bash
curl -fsSL https://deb.nodesource.com/setup_23.x | bash -
apt-get install -y nodejs
npm install -g @brightdata/mcp
pip install --upgrade pip
pip install -r requirements.txt
