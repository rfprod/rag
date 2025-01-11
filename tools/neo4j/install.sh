#!/bin/bash

# https://debian.neo4j.com/
sudo apt update
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update

sudo apt install neo4j -y
sudo systemctl enable neo4j.service
sudo systemctl start neo4j.service
sudo systemctl status neo4j.service

neo4j --version
