#!/bin/bash

source set-env.sh

sudo docker ps -aqf name=${container_name} | grep -q .

if [ $? -ne 0 ]; then
    echo "Container not exists"
    sudo docker images -aq ${image_name}:${image_tag} | grep -q .
    if [ $? -ne 0 ]; then
        echo "Image not exists"
        sudo docker build \
                -f Dockerfile \
                --build-arg UID=$(id -u) \
                --build-arg GID=$(id -g) \
                -t ${image_name}:${image_tag} \
                .
    fi
    sudo docker run -it \
               --name ${container_name} \
               --env-file .env \
               -v $HOST_MOUNT_POINT:/workspace \
               ${image_name}:${image_tag} \
               bash
else
    sudo docker ps -qf name=${container_name} | grep -q .
    if [ $? -ne 0 ]; then
        echo "Container is not running"
        sudo docker start ${container_name}
    fi
    # Attatch to the container
    sudo docker exec -it ${container_name} bash
fi
