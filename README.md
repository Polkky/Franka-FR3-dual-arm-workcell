# Franka-FR3-dual-arm-workcell
Dual arm workcell for the Franka FR3

**WSL2, Ubuntu-24.04 (Noble), ROS2 Jazzy**

**_WORK IN PROGRESS_**

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

```bash
source install/setup.bash
```

Test that franka_ros2 works
```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```

