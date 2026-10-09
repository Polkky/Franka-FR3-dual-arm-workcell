FROM osrf/ros:jazzy-desktop-full

RUN apt update && apt-get install -y \
    bash-completion \
    gdb \
    git \
    nano \
    iputils-ping \
    openssh-client \
    ros-dev-tools \
    python3-pip \
    python3-venv \
    python3-colcon-argcomplete \
    python3-colcon-common-extensions \
    sudo \
    vim \
    libgtest-dev \
    libgmock-dev \
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

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc \
    && echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> /home/$USERNAME/.bashrc

# franka_ros2 dependencies not found in full jazzy
RUN sudo apt-get update \
    && sudo apt-get install -y --no-install-recommends \
        ros-jazzy-joint-state-publisher-gui \
        ros-jazzy-ros2controlcli \
        ros-jazzy-controller-interface \
        ros-jazzy-hardware-interface-testing \
        ros-jazzy-ament-cmake-clang-format \
        ros-jazzy-ament-cmake-clang-tidy \
        ros-jazzy-controller-manager \
        ros-jazzy-ros2-control-cmake \
        ros-jazzy-control-msgs \
        ros-jazzy-backward-ros \
        ros-jazzy-generate-parameter-library \
        ros-jazzy-realtime-tools \
        ros-jazzy-joint-state-publisher \
        ros-jazzy-joint-state-broadcaster \
        ros-jazzy-moveit-ros-move-group \
        ros-jazzy-moveit-kinematics \
        ros-jazzy-moveit-planners-ompl \
        ros-jazzy-moveit-ros-visualization \
        ros-jazzy-joint-trajectory-controller \
        ros-jazzy-moveit-simple-controller-manager \
    && sudo apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/*

RUN mkdir -p /ros2ws/src
WORKDIR /ros2ws
COPY . /ros2ws/src