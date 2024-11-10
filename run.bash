#!/bin/bash
# Run below step one by one in terminal
sudo docker rmi -f $(sudo docker images -f "dangling=true" -q)
docker build -t track_my_bills .
docker run --net host --gpus all -it -v /home/$(whoami)/Documents/projects/track_my_bills:/app track_my_bills


