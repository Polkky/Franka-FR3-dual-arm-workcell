#  This is a moveit + gazebo test launch
#
# This traces the "moveit.launch.py" file implementation from franka_ros2/franka_fr3_moveit_config
# Some values have been hardcoded and the code made more minimal

import os
from ament_index_python.packages import get_package_share_directory
import xacro
from launch_ros.actions import Node
from launch.actions import Shutdown, DeclareLaunchArgument
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch import LaunchDescription
import yaml


# load_yaml function from moveit.launch.py (franka_ros2/franka_fr3_moveit_config)
# needed to utilize yaml configs correctly
def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None

def generate_launch_description():
    robot_type = 'fr3'
    load_gripper = 'false'
    franka_hand = 'franka_hand'
    namespace = ''  # defaults to root
    use_fake_hardware = 'true'  # this can be changed to false once testing with real robots
    use_fake_hardware = 'true'  # fake hardware for simulating, can add argument for toggling later
    fake_sensor_commands = 'true'   # same deal as fake hardware

    robot_ip_str = 'robot_ip'   # has to be declared as an argument ?
    robot_ip = LaunchConfiguration('robot_ip_str')

    fr3_xacro_file = os.path.join(
        get_package_share_directory('franka_bringup'),
        'urdf',
        'franka_arm.urdf.xacro'   # FR3 xacro file from franka_ros2
    )
    fr3_semantic_xacro_file = os.path.join(
        get_package_share_directory('franka_description'),
        'robots', 'fr3', 'fr3.srdf.xacro'   # FR3 semantic xacro file from franka_ros2
    )

    fr3_desc_config = xacro.process_file(
        fr3_xacro_file,
        mappings={
            'robot_type': robot_type,
            'hand': load_gripper,
            'ee_id': franka_hand,
            'robot_ip': robot_ip,
            'use_fake_hardware': use_fake_hardware,
            'fake_sensor_commands': fake_sensor_commands 
        }
    )
    fr3_desc = {'robot_description': fr3_desc_config.toxml()}

    fr3_semantic_desc_config = xacro.process_file(
        fr3_semantic_xacro_file,
        mappings={
            'hand': load_gripper,
            'ee_id': franka_hand,
        }
    )
    fr3_desc_semantic = {'robot_description_semantic': fr3_semantic_desc_config.toxml()}

    kinematics_yaml = load_yaml('franka_fr3_moveit_config', 'config/kinematics.yaml')
    kinematics_config = {
        'robot_description_kinematics': kinematics_yaml
    }

    joint_limits_yaml = load_yaml('franka_fr3_moveit_config', 'config/fr3_joint_limits.yaml')
    joint_limits_config = {
        'robot_description_planning': joint_limits_yaml
    }

    ompl_planning_pipeline_config = {
        'move_group': {
            'planning_plugins': ['ompl_interface/OMPLPlanner'],
            'request_adapters': [
                'default_planning_request_adapters/ResolveConstraintFrames',
                'default_planning_request_adapters/ValidateWorkspaceBounds',
                'default_planning_request_adapters/CheckStartStateBounds',
                'default_planning_request_adapters/CheckStartStateCollision',
            ],
            'response_adapters': [
                'default_planning_response_adapters/AddTimeOptimalParameterization',
                'default_planning_response_adapters/ValidateSolution',
                'default_planning_response_adapters/DisplayMotionPath',
            ],
            'start_state_max_bounds_error': 0.1,
        }
    }
    ompl_planning_yaml = controllers_yaml = load_yaml('franka_fr3_moveit_config', 'config/ompl_planning.yaml')
    ompl_planning_pipeline_config['move_group'].update(ompl_planning_yaml)


    rviz_path = os.path.join(
        get_package_share_directory('franka_fr3_moveit_config'),
        'rviz',
        'moveit.rviz'
    )
    rviz_node = Node(
        package = 'rviz2',
        executable = 'rviz2',
        name = 'rviz2',
        output = 'log',
        arguments = ['-d', rviz_path],
        parameters = [fr3_desc, fr3_desc_semantic, ompl_planning_pipeline_config, kinematics_config],
    )

    control_path = os.path.join(
        get_package_share_directory('franka_fr3_moveit_config'),
        'config',
        'fr3_ros_controllers.yaml'
    )
    control_node = Node(
        package = 'controller_manager',
        executable = 'ros2_control_node',
        namespace = namespace,
        parameters = [fr3_desc, control_path],
        remappings = [('joint_states', 'franka/joint_states')],
        output = {'stdout': 'screen', 'stderr': 'screen'},
        on_exit = Shutdown()
    )

    arm_controller_node = Node(
        package = 'controller_manager',
        executable = 'spawner',
        namespace = namespace,
        arguments = ['fr3_arm_controller', '--controller-manager-timeout', '60', '--controller-manager',
        PathJoinSubstitution([namespace, 'controller_manager'])],
        output = 'screen'
    )
    joint_state_broadcaster = Node(
        package = 'controller_manager',
        executable = 'spawner',
        namespace = namespace,
        arguments = ['joint_state_broadcaster', '--controller-manager-timeout', '60', '--controller-manager',
        PathJoinSubstitution([namespace, 'controller_manager'])],
        output = 'screen'
    )
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        namespace = namespace,
        parameters = [{'source_list': ['franka/joint_states', 'franka_gripper/joint_states'], 'rate': 30}]
    )
    # Unused for simulation:
    #franka_robot_state_broadcaster = Node(
    #    package = 'controller_manager',
    #    executable = 'spawner',
    #    namespace = namespace,
    #    arguments = ['franka_robot_state_broadcaster'],
    #)
    # May also need IP address (?) when moving to real

    robot_state_publisher = Node(
        package = 'robot_state_publisher',
        executable = 'robot_state_publisher',
        name = 'robot_state_publisher',
        namespace = namespace,
        output = 'both',
        parameters = [fr3_desc],
    )

    trajectory = {'moveit_manage_controllers': True, 'trajectory_execution.allowed_execution_duration_scaling': 1.2,
                'trajectory_execution.allowed_goal_duration_margin': 0.5, 'trajectory_execution.allowed_start_tolerance': 0.01,}
    planning_scene_monitor_params = {'publish_planning_scene': True, 'publish_geometry_updates': True, 'publish_state_updates': True,
                                    'publish_transforms_updates': True,}

    moveit_yaml = controllers_yaml = load_yaml('franka_fr3_moveit_config', 'config/fr3_controllers.yaml')
    moveit_controllers = {'moveit_simple_controller_manager': moveit_yaml,
                        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',}

    move_group_node = Node(
        package = 'moveit_ros_move_group',
        executable = 'move_group',
        namespace = namespace,
        output = 'screen',
        parameters = [fr3_desc, fr3_desc_semantic, kinematics_config, joint_limits_config,
                    ompl_planning_pipeline_config, trajectory, moveit_controllers, planning_scene_monitor_params]
    )


    # ARGUMENT DECLARATIONS
    robot_ip_arg = DeclareLaunchArgument(
        robot_ip_str,
        default_value = 'dont-care',     # dont-care works for simulation
        description='IP address')

    return LaunchDescription([
        # Nodes:
        rviz_node,
        control_node,
        arm_controller_node,
        joint_state_broadcaster,
        joint_state_publisher,
        robot_state_publisher,
        move_group_node,
        # Arguments:
        robot_ip_arg,
    ])


# TODO: ip, fake hardware, sensor thing