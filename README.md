# Franka-FR3-dual-arm-workcell
Dual arm workcell for the Franka FR3

**WSL2, Ubuntu-24.04 (Noble), ROS2 Jazzy**

**_WORK IN PROGRESS_**


Installation:
```bash
git clone https://github.com/Polkky/Franka-FR3-dual-arm-workcell.git
```

```bash
cd Franka-FR3-dual-arm-workcell
```

```bash
docker compose build
```

```bash
docker compose up
```

In another terminal
```bash
sudo docker exec -it FRDualArm bash
```

Installing franka_ros2 (https://github.com/frankarobotics/franka_ros2/blob/jazzy/README.md)
```bash
git clone --branch jazzy https://github.com/frankarobotics/franka_ros2.git src/franka_ros2
```

```bash
vcs import src/franka_ros2 < src/franka_ros2/dependency.repos --recursive --skip-existing
```

```bash
sudo apt-get update
```

```bash
rosdep update
```

```bash
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y --skip-keys=zed_wrapper
```

```bash
colcon build --symlink-install
```

```bash
source install/setup.bash
```

To test that franka_ros2 works:
```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```

