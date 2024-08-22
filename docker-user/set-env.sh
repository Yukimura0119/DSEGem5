#!/bin/bash

# Define the Docker image name and tag
export image_name="dse_gem5"
export image_tag="$USER"
export container_name="${image_name}-${image_tag}"
export HOST_MOUNT_POINT=~/Lab447-Simulator
