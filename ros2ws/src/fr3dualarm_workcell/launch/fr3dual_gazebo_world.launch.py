# This is a gazebo world test launch
#
# This traces the "gazebo_franka_arm_example_controller.launch.py" file implementation from franka_ros2
# Many values have been changed to being hardcoded

import os
from ament_index_python.packages import get_package_share_directory
import xacro
from launch_ros.actions import Node
from launch import LaunchDescription, LaunchContext
from launch.actions import OpaqueFunction, DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    robot_type = 'fr3'
    load_gripper = 'false'
    franka_hand = 'franka_hand'
    namespace = ''  # defaults to root
    # change controller_name if needed, found in franka_ros2/franka_example_controllers
    controller_name = ''
    rviz = 'true'

    fr3_xacro_file = os.path.join(
        get_package_share_directory('franka_gazebo_bringup'),
        'urdf',
        'franka_arm.gazebo.xacro'   # FR3 xacro file from franka_ros2
    )
    fr3_desc_config = xacro.process_file(
        fr3_xacro_file,
        mappings={
            'robot_type': robot_type,
            'hand': load_gripper,
            'ee_id': franka_hand,
            'gazebo_effort': 'true',
        }
    )
    gz_world_file = os.path.join(
        get_package_share_directory('fr3dualarm_workcell'),
        'worlds',
        'workcell.sdf'
    )
    robot_state_publisher = Node(
        package = 'robot_state_publisher',
        executable = 'robot_state_publisher',
        name = 'robot_state_publisher',
        output = 'both',
        parameters = [{'robot_description': fr3_desc_config.toxml()}]
    )

    os.environ['GZ_SIM_RESOURCE_PATH'] = os.path.dirname(
        get_package_share_directory('franka_description'))
    gz_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        launch_arguments = {'gz_args': f'-r {gz_world_file}'}.items(),
    )

    launch_controller = Node(
        package = 'controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            controller_name,
            '--controller-manager-timeout', '30',
        ],
        parameters=[PathJoinSubstitution([
            FindPackageShare('franka_gazebo_bringup'),
            'config',
            'franka_gazebo_controllers.yaml'
        ])],
        output='screen'
    )

    spawn = Node(
        package = 'ros_gz_sim',
        executable = 'create',
        namespace = '',
        arguments = ['-topic', '/robot_description',
                    '-x', '0.0', '-y', '0.5', '-z', '1.0',],     # adjust x,y,z values as needed
        output = 'screen'
    )

    bridge = Node(
        package = 'ros_gz_bridge',
        executable = 'parameter_bridge',
        arguments = ['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],  # add more topics to bridge here if needed
        output = 'screen'
    )

    # may need RViz for MoveIt compatibility later, unless MoveIt is handled separately

    return LaunchDescription([
        robot_state_publisher,
        gz_world,
        bridge,
        spawn,

        RegisterEventHandler(
            event_handler = OnProcessExit(
                target_action = spawn,
                on_exit = [launch_controller],
            )
        ),
    ])

