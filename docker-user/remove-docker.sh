#!/bin/bash

source set-env.sh

docker stop ${container_name}
docker rm ${container_name}

if [ $# -ne 0 ]; then
    docker rmi ${image_name}:${image_tag}
fi
