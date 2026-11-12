#  This is a moveit + gazebo test launch
#
# This traces the "moveit.launch.py" file implementation from franka_ros2/franka_fr3_moveit_config
# Some values have been hardcoded and the code made more minimal

import os
from ament_index_python.packages import get_package_share_directory
import xacro
from launch_ros.actions import Node
from launch.actions import Shutdown, DeclareLaunchArgument, RegisterEventHandler, IncludeLaunchDescription, ExecuteProcess
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch import LaunchDescription
import yaml
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


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
    load_gripper = 'true'
    franka_hand = 'franka_hand'
    namespace = ''  # defaults to root
    use_fake_hardware = 'true'  # fake hardware for simulating, can add argument for toggling once working with real robots
    fake_sensor_commands = 'true'   # same deal as fake hardware
    controller_name = ''  # used in gazebo

    # robot ip and fake args are from solo moveit franka_ros launch, may be deprecated
    robot_ip_str = 'robot_ip'   # has to be declared as an argument ?
    robot_ip = LaunchConfiguration(robot_ip_str)

    # Only using gazebo xacro since it points to the same urdf.xacro anyways
    fr3_xacro_file = os.path.join(
        get_package_share_directory('fr3dualarm_workcell'),
        'urdf',
        'fr3dual.gazebo.xacro'   # FR3 xacro file from franka_ros2
    )
    gz_world_file = os.path.join(
        get_package_share_directory('fr3dualarm_workcell'),
        'worlds',
        'workcell.sdf'
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

    fr3_desc_config = xacro.process_file(
        fr3_xacro_file,
        mappings={
            'robot_type': robot_type,
            'hand': load_gripper,
            'ee_id': franka_hand,
            'gazebo_effort': 'true'
        }
    )
    fr3_desc = {'robot_description': fr3_desc_config.toxml()}

    fr3_semantic_xacro_file = os.path.join(
        get_package_share_directory('fr3dualarm_workcell'),
        'urdf',
        'fr3dual.srdf.xacro'
    )
    fr3_semantic_desc_config = xacro.process_file(
        fr3_semantic_xacro_file,
        mappings={
            'hand': load_gripper,
            'ee_id': franka_hand,
        }
    )
    fr3_desc_semantic = {'robot_description_semantic': fr3_semantic_desc_config.toxml()}

    # dual .yaml configs are the same as single arm franka_ros2 except with separate left/right definitions
    kinematics_yaml = load_yaml('fr3dualarm_workcell', 'config/fr3dual_kinematics.yaml')
    kinematics_config = {
        'robot_description_kinematics': kinematics_yaml
    }

    joint_limits_yaml = load_yaml('fr3dualarm_workcell', 'config/fr3dual_jointlimits.yaml')
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
    ompl_planning_yaml = load_yaml('franka_fr3_moveit_config', 'config/ompl_planning.yaml')
    ompl_planning_pipeline_config['move_group'].update(ompl_planning_yaml)


    # own rviz file for a couple of small changes just in case
    rviz_path = os.path.join(
        get_package_share_directory('fr3dualarm_workcell'),
        'rviz',
        'fr3dual_moveit.rviz'
    )
    rviz_node = Node(
        package = 'rviz2',
        executable = 'rviz2',
        name = 'rviz2',
        output = 'log',
        arguments = ['-d', rviz_path],
        parameters = [fr3_desc, fr3_desc_semantic, ompl_planning_pipeline_config, kinematics_config,
        {'use_sim_time': True}],
    )

    # placeholder solution for arm controller
    arm_controller = os.path.join(
        get_package_share_directory('fr3dualarm_workcell'),
        'config',
        'fr3dual_controllers.yaml'
    )

    load_controllers = [
        ExecuteProcess(
            cmd = [
                'ros2', 'run', 'controller_manager', 'spawner', 'joint_state_broadcaster',
                '--controller-manager-timeout', '60'
            ],
            output = 'screen'
        ),
        ExecuteProcess(
            # direct ros2 cmd didn't work for setting the param manually, not ideal
            cmd = [
                'bash', '-c',
                'until ros2 param set /controller_manager fr3_arm_controller.type '
                'joint_trajectory_controller/JointTrajectoryController; do sleep 1; done && '
                f'ros2 run controller_manager spawner fr3_arm_controller '
                f'--param-file {arm_controller} --controller-manager-timeout 60'
            ],
            output = 'screen'
        ),
    ]


    gz_spawn = Node(
        package = 'ros_gz_sim',
        executable = 'create',
        namespace = '',
        arguments = ['-topic', '/robot_description',
                    '-x', '0.0', '-y', '0.0', '-z', '1.0',],     # dual arms base coordinates
        output = 'screen'
    )
    rosgz_bridge = Node(
        package = 'ros_gz_bridge',
        executable = 'parameter_bridge',
        arguments = ['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],  # add more topics to bridge here if needed
        output = 'screen'
    )

    robot_state_publisher = Node(
        package = 'robot_state_publisher',
        executable = 'robot_state_publisher',
        name = 'robot_state_publisher',
        output = 'both',
        parameters = [fr3_desc, {'use_sim_time': True}],
    )

    trajectory = {'moveit_manage_controllers': True, 'trajectory_execution.allowed_execution_duration_scaling': 1.2,
                'trajectory_execution.allowed_goal_duration_margin': 0.5, 'trajectory_execution.allowed_start_tolerance': 0.01,}
    planning_scene_monitor_params = {'publish_planning_scene': True, 'publish_geometry_updates': True, 'publish_state_updates': True,
                                    'publish_transforms_updates': True,}

    # currently using basic fr3 control, change yaml file to something else later
    moveit_yaml = load_yaml('franka_fr3_moveit_config', 'config/fr3_controllers.yaml')
    moveit_controllers = {'moveit_simple_controller_manager': moveit_yaml,
                        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',}

    # one node will create two move groups for separate planning between arms
    move_group_node = Node(
        package = 'moveit_ros_move_group',
        executable = 'move_group',
        namespace = namespace,
        output = 'screen',
        parameters = [fr3_desc, fr3_desc_semantic, kinematics_config, joint_limits_config,
                    ompl_planning_pipeline_config, trajectory, moveit_controllers, planning_scene_monitor_params,
                    {'use_sim_time': True}]
    )


    # ARGUMENT DECLARATIONS
    # robot ips unused, may need to be used for real-world cell
    robot_ip_arg = DeclareLaunchArgument(
        robot_ip_str,
        default_value = 'dont-care',     # dont-care works for simulation
        description='IP address')

    return LaunchDescription([
        robot_ip_arg,

        robot_state_publisher,
        gz_world,
        gz_spawn,
        rosgz_bridge,

        move_group_node,
        rviz_node,

        RegisterEventHandler(
            event_handler = OnProcessExit(
                target_action = gz_spawn,
                on_exit = load_controllers
            )
        ),

    ])