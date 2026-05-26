# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import xacro
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, conditions
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration

import launch.actions
import launch_ros.actions

def to_urdf(xacro_path, urdf_path=None):
    if urdf_path is None:
        urdf_path = os.path.join(
            get_package_share_directory("azure_kinect_ros_driver"),
            "urdf",
            "azure_kinect.urdf")
    doc = xacro.process_file(xacro_path)
    out = xacro.open_output(urdf_path)
    out.write(doc.toprettyxml(indent='  '))
    return urdf_path

def generate_launch_description():
    xacro_file = os.path.join(
            get_package_share_directory("azure_kinect_ros_driver"),
            "urdf",
            "azure_kinect.urdf.xacro")

    urdf_path = to_urdf(xacro_file)
    urdf = open(urdf_path).read()

    azure_description_remappings = [('robot_description', 'azure_description')]

    rviz_config = os.path.join(
        get_package_share_directory('azure_kinect_ros_driver'),
        'rviz',
        'azure_kinect.rviz')

    return LaunchDescription([
    # ── General ────────────────────────────────────────────────────────────
    DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch rviz2 with the default config'),
    DeclareLaunchArgument(
        'tf_prefix',
        default_value='',
        description='Prefix added to TF frame IDs. Typically contains a trailing _ unless empty.'),
    DeclareLaunchArgument(
        'overwrite_robot_description',
        default_value='true',
        description='Publish a standalone azure_description instead of robot_description'),
    # ── Camera parameters ──────────────────────────────────────────────────
    DeclareLaunchArgument(
        'depth_enabled',
        default_value='true',
        description='Enable or disable the depth camera'),
    DeclareLaunchArgument(
        'depth_mode',
        default_value='WFOV_UNBINNED',
        description='Depth camera mode: NFOV_UNBINNED, NFOV_2X2BINNED, WFOV_UNBINNED, WFOV_2X2BINNED, PASSIVE_IR'),
    DeclareLaunchArgument(
        'depth_unit',
        default_value='16UC1',
        description='Depth distance units: "32FC1" (float metre) or "16UC1" (integer millimetre)'),
    DeclareLaunchArgument(
        'color_enabled',
        default_value='true',
        description='Enable or disable the color camera'),
    DeclareLaunchArgument(
        'color_format',
        default_value='bgra',
        description='RGB camera format: bgra, jpeg'),
    DeclareLaunchArgument(
        'color_resolution',
        default_value='1080P',
        description='Color camera resolution: 720P, 1080P, 1440P, 1536P, 2160P, 3072P'),
    DeclareLaunchArgument(
        'fps',
        default_value='15',
        description='Camera FPS: 5, 15, or 30'),
    DeclareLaunchArgument(
        'point_cloud',
        default_value='true',
        description='Generate a point cloud from depth data. Requires depth_enabled'),
    DeclareLaunchArgument(
        'rgb_point_cloud',
        default_value='true',
        description='Colorize the point cloud using the RGB camera. Requires color_enabled and depth_enabled'),
    DeclareLaunchArgument(
        'point_cloud_in_depth_frame',
        default_value='true',
        description='Render RGB point cloud in depth frame (true) or RGB frame (false)'),
    DeclareLaunchArgument(
        'required',
        default_value='false',
        description='Terminate the launch file if the driver node dies'),
    DeclareLaunchArgument(
        'sensor_sn',
        default_value='',
        description='Sensor serial number. If empty, the first detected sensor is used'),
    DeclareLaunchArgument(
        'recording_file',
        default_value='',
        description='Absolute path to a .mkv recording for playback instead of live device'),
    DeclareLaunchArgument(
        'recording_loop_enabled',
        default_value='false',
        description='Loop the recording file from the beginning when it ends'),
    DeclareLaunchArgument(
        'body_tracking_enabled',
        default_value='false',
        description='Publish joint positions as marker arrays'),
    DeclareLaunchArgument(
        'body_tracking_smoothing_factor',
        default_value='0.0',
        description='Body tracking smoothing: 0 (none) to 1 (full)'),
    DeclareLaunchArgument(
        'rescale_ir_to_mono8',
        default_value='false',
        description='Rescale IR image to 8-bit monochrome using ir_mono8_scaling_factor'),
    DeclareLaunchArgument(
        'ir_mono8_scaling_factor',
        default_value='1.0',
        description='Scaling factor for IR to mono8 conversion. Use 0.5-1 for illumination, 10 for passive IR'),
    DeclareLaunchArgument(
        'imu_rate_target',
        default_value='0',
        description='Target IMU output rate in Hz. 0 = full rate (1.6 kHz)'),
    DeclareLaunchArgument(
        'wired_sync_mode',
        default_value='0',
        description='Wired sync mode: 0=OFF, 1=MASTER, 2=SUBORDINATE'),
    DeclareLaunchArgument(
        'subordinate_delay_off_master_usec',
        default_value='0',
        description='Delay subordinate camera off master in microseconds'),
    # ── Topic remap targets ────────────────────────────────────────────────
    DeclareLaunchArgument(
        'rgb_topic',
        default_value='/camera/rgb/image_raw',
        description='Remap target for rgb/image_raw'),
    DeclareLaunchArgument(
        'rgb_camera_info_topic',
        default_value='/camera/rgb/camera_info',
        description='Remap target for rgb/camera_info'),
    DeclareLaunchArgument(
        'aligned_depth_topic',
        default_value='/sierra/depth/image_raw',
        description='Remap target for depth_to_rgb/image_raw'),
    DeclareLaunchArgument(
        'aligned_depth_camera_info_topic',
        default_value='/sierra/depth/camera_info',
        description='Remap target for depth_to_rgb/camera_info'),
    DeclareLaunchArgument(
        'point_cloud_topic',
        default_value='/sierra/point_cloud',
        description='Remap target for points2'),
    # ── Legacy frame alias args ────────────────────────────────────────────
    DeclareLaunchArgument(
        'publish_legacy_frame_aliases',
        default_value='true',
        description='Publish static TF aliases for legacy frame names'),
    DeclareLaunchArgument(
        'legacy_rgb_frame',
        default_value='camera_rgb_frame',
        description='Legacy frame name aliased to rgb_camera_link'),
    DeclareLaunchArgument(
        'legacy_depth_frame',
        default_value='camera_depth_frame',
        description='Legacy frame name aliased to depth_camera_link'),
    # ── Driver node ────────────────────────────────────────────────────────
    launch_ros.actions.Node(
        package='azure_kinect_ros_driver',
        executable='node',
        output='screen',
        parameters=[
            {'depth_enabled':                       LaunchConfiguration('depth_enabled')},
            {'depth_mode':                          LaunchConfiguration('depth_mode')},
            {'depth_unit':                          LaunchConfiguration('depth_unit')},
            {'color_enabled':                       LaunchConfiguration('color_enabled')},
            {'color_format':                        LaunchConfiguration('color_format')},
            {'color_resolution':                    LaunchConfiguration('color_resolution')},
            {'fps':                                 LaunchConfiguration('fps')},
            {'point_cloud':                         LaunchConfiguration('point_cloud')},
            {'rgb_point_cloud':                     LaunchConfiguration('rgb_point_cloud')},
            {'point_cloud_in_depth_frame':          LaunchConfiguration('point_cloud_in_depth_frame')},
            {'sensor_sn':                           LaunchConfiguration('sensor_sn')},
            {'tf_prefix':                           LaunchConfiguration('tf_prefix')},
            {'recording_file':                      LaunchConfiguration('recording_file')},
            {'recording_loop_enabled':              LaunchConfiguration('recording_loop_enabled')},
            {'body_tracking_enabled':               LaunchConfiguration('body_tracking_enabled')},
            {'body_tracking_smoothing_factor':      LaunchConfiguration('body_tracking_smoothing_factor')},
            {'rescale_ir_to_mono8':                 LaunchConfiguration('rescale_ir_to_mono8')},
            {'ir_mono8_scaling_factor':             LaunchConfiguration('ir_mono8_scaling_factor')},
            {'imu_rate_target':                     LaunchConfiguration('imu_rate_target')},
            {'wired_sync_mode':                     LaunchConfiguration('wired_sync_mode')},
            {'subordinate_delay_off_master_usec':   LaunchConfiguration('subordinate_delay_off_master_usec')},
        ],
        remappings=[
            ('rgb/image_raw',           LaunchConfiguration('rgb_topic')),
            ('rgb/camera_info',         LaunchConfiguration('rgb_camera_info_topic')),
            ('depth_to_rgb/image_raw',  LaunchConfiguration('aligned_depth_topic')),
            ('depth_to_rgb/camera_info',LaunchConfiguration('aligned_depth_camera_info_topic')),
            ('points2',                 LaunchConfiguration('point_cloud_topic')),
        ]),
    # ── Robot description (overwrite_robot_description=true) ───────────────
    launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': urdf}],
        condition=conditions.IfCondition(LaunchConfiguration('overwrite_robot_description'))),
    launch_ros.actions.Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        arguments=[urdf_path],
        condition=conditions.IfCondition(LaunchConfiguration('overwrite_robot_description'))),
    # ── Robot description (overwrite_robot_description=false) ──────────────
    launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_azure',
        parameters=[{'robot_description': urdf}],
        remappings=azure_description_remappings,
        condition=conditions.UnlessCondition(LaunchConfiguration('overwrite_robot_description'))),
    launch_ros.actions.Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher_azure',
        arguments=[urdf_path],
        remappings=azure_description_remappings,
        condition=conditions.UnlessCondition(LaunchConfiguration('overwrite_robot_description'))),
    # ── rviz2 ──────────────────────────────────────────────────────────────
    launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        condition=conditions.IfCondition(LaunchConfiguration('use_rviz'))),
    # ── Legacy TF frame aliases ────────────────────────────────────────────
    launch_ros.actions.Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='legacy_depth_frame_alias',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
            '--frame-id', [LaunchConfiguration('tf_prefix'), 'depth_camera_link'],
            '--child-frame-id', LaunchConfiguration('legacy_depth_frame'),
        ],
        condition=conditions.IfCondition(LaunchConfiguration('publish_legacy_frame_aliases'))),
    launch_ros.actions.Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='legacy_rgb_frame_alias',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
            '--frame-id', [LaunchConfiguration('tf_prefix'), 'rgb_camera_link'],
            '--child-frame-id', LaunchConfiguration('legacy_rgb_frame'),
        ],
        condition=conditions.IfCondition(LaunchConfiguration('publish_legacy_frame_aliases'))),
    ])
