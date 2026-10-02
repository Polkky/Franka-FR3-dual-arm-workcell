FROM osrf/ros:jazzy-desktop-full

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
    python3-pip \
    python3-venv \
    curl \
    lsb-release \
    gnupg && \
    curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null && \
    sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list' && \
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add - && \
    apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y gz-harmonic ros-jazzy-ros-gz && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

ENV GZ_VERSION=fortress

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
RUN mkdir -p /up/ros2env/src/
WORKDIR /up/ros2env