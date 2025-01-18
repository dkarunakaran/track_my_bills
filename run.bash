#!/bin/bash
# Run below step one by one in terminal
sudo docker rmi -f $(sudo docker images -f "dangling=true" -q)
docker build -t track_my_bills .

# Get the current username
username=$(whoami)
if [ "$username" == "beastan" ]; then
    echo "We are running the docker container on $username's computer."
    docker run --net host --gpus all -it -v /media/$username/projects/track_my_bills:/app track_my_bills
elif [ "$username" == "dhanoop" ]; then
    echo "We are running the docker container on $username's computer."
    docker run --net host --gpus all -it -v /home/$username/Documents/projects/track_my_bills:/app track_my_bills
elif [ "$username" == "codespace" ]; then
    echo "We are running the docker container on $username's computer."
    docker run --net host -it -v /home/$username/projects/track_my_bills:/app track_my_bills
else
    echo "Wrong system to run this script."
fi

