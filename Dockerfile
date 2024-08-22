FROM ubuntu:20.04


ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y locales git vim wget unzip gdb build-essential
RUN apt-get install -y python3 python3-dev python3-pip
RUN apt-get install -y m4 scons zlib1g zlib1g-dev libprotobuf-dev \
                       protobuf-compiler libprotoc-dev libgoogle-perftools-dev \
                       libboost-all-dev
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set encoding
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8
RUN locale-gen en_US.UTF-8

# Set timezone
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install pypi packages
ENV PATH="/root/.local/bin:${PATH}"
RUN python3 -m pip install -U pip
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

WORKDIR /workspace

RUN echo "export LC_ALL=en_US.UTF-8" >> ~/.bashrc
RUN echo "export TERM=xterm-256color" >> ~/.bashrc
RUN echo "export PATH=/home/docker/.local/bin:$PATH" >> ~/.bashrc
