#!/bin/bash

yum update -y

yum install docker git -y

systemctl enable docker
systemctl start docker

curl -SL https://github.com/docker/compose/releases/download/v2.39.1/docker-compose-linux-x86_64 \
-o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose

usermod -aG docker ec2-user

cd /home/ec2-user

git clone https://github.com/Apurvbajpai2531/Stockloom.git

cd Stockloom

docker-compose up -d