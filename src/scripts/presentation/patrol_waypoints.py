#!/usr/bin/env python3
"""Drive the robot through a list of world-frame waypoints on /cmd_vel.

Kept deliberately simple and open loop in the map sense: it steers on the wheel
odometry published by the omni drive controller, which is the only pose source
that exists before SLAM or AMCL is running.  That makes it usable as a patrol
driver in every scenario level, including the degraded ones.

Parameters
    waypoints  "x1,y1;x2,y2;..."   world-frame waypoints (metres)
    speed      m/s                 forward speed cap
    tolerance  m                   waypoint acceptance radius
    origin_x, origin_y, origin_yaw the spawn pose, i.e. where odom is (0,0,0)
    loop       bool                start over when the list is exhausted
    hold       s                   time to sit still before moving at all
"""
import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class Patrol(Node):

    def __init__(self):
        super().__init__('patrol_waypoints')
        self.declare_parameter('waypoints', '')
        self.declare_parameter('speed', 0.35)
        self.declare_parameter('tolerance', 0.30)
        self.declare_parameter('origin_x', 8.0727)
        self.declare_parameter('origin_y', 7.5312)
        self.declare_parameter('origin_yaw', -1.5708)
        self.declare_parameter('loop', False)
        self.declare_parameter('hold', 12.0)
        # /odom does not exist in this stack.  The omni wheel drive controller
        # publishes its wheel odometry on /omni_drive_controller/odom, and
        # subscribing to the wrong name is what silently kept this node from
        # ever commanding a velocity (it had no pose, so it published zeros).
        self.declare_parameter('odom_topic', '/omni_drive_controller/odom')

        raw = str(self.get_parameter('waypoints').value).strip()
        self.waypoints = []
        for chunk in raw.split(';'):
            chunk = chunk.strip()
            if not chunk:
                continue
            x, y = chunk.split(',')
            self.waypoints.append((float(x), float(y)))
        if not self.waypoints:
            raise RuntimeError('no waypoints given')

        speed = float(self.get_parameter('speed').value)
        self.speed = speed
        self.tol = float(self.get_parameter('tolerance').value)
        self.loop = bool(self.get_parameter('loop').value)
        self.hold = float(self.get_parameter('hold').value)
        self.origin = (float(self.get_parameter('origin_x').value),
                       float(self.get_parameter('origin_y').value),
                       float(self.get_parameter('origin_yaw').value))

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        odom_topic = str(self.get_parameter('odom_topic').value)
        self.create_subscription(Odometry, odom_topic, self.on_odom,
                                 qos_profile_sensor_data)
        self.pose = None
        self.index = 0
        self.started = None
        self.finished = False
        self.timer = self.create_timer(0.05, self.step)
        self.get_logger().info(
            f'patrol: {len(self.waypoints)} waypoints, speed {self.speed} m/s, '
            f'origin {self.origin}, hold {self.hold}s, odom {odom_topic}')

    def on_odom(self, msg):
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, yaw_of(msg.pose.pose.orientation))
        if self.started is None:
            self.started = self.get_clock().now()

    def to_odom_frame(self, wx, wy):
        """World point -> odom frame, using the known spawn pose."""
        ox, oy, oyaw = self.origin
        dx, dy = wx - ox, wy - oy
        c, s = math.cos(-oyaw), math.sin(-oyaw)
        return c * dx - s * dy, s * dx + c * dy

    def step(self):
        cmd = Twist()
        if self.pose is None or self.finished:
            self.pub.publish(cmd)
            return
        elapsed = (self.get_clock().now() - self.started).nanoseconds * 1e-9
        if elapsed < self.hold:
            self.pub.publish(cmd)
            return

        px, py, pyaw = self.pose
        target = self.to_odom_frame(*self.waypoints[self.index])
        dx, dy = target[0] - px, target[1] - py
        dist = math.hypot(dx, dy)
        if dist < self.tol:
            self.get_logger().info(
                f'reached waypoint {self.index + 1}/{len(self.waypoints)} '
                f'{self.waypoints[self.index]} (odom {px:.2f},{py:.2f})')
            self.index += 1
            if self.index >= len(self.waypoints):
                if not self.loop:
                    self.finished = True
                    self.pub.publish(Twist())
                    self.get_logger().info('ROUTE_COMPLETE')
                    return
                self.index = 0
            target = self.to_odom_frame(*self.waypoints[self.index])
            dx, dy = target[0] - px, target[1] - py
            dist = math.hypot(dx, dy)

        heading_err = math.atan2(dy, dx) - pyaw
        heading_err = math.atan2(math.sin(heading_err), math.cos(heading_err))
        cmd.angular.z = max(-1.2, min(1.2, 1.8 * heading_err))
        # Only drive forward once roughly aimed, and ease off near the target.
        align = math.cos(heading_err)
        gain = 1.0 if dist > 1.0 else max(0.25, dist)
        cmd.linear.x = self.speed * max(0.0, align) * gain \
            if abs(heading_err) < 1.0 else 0.0
        self.pub.publish(cmd)


def main():
    rclpy.init()
    node = Patrol()
    try:
        rclpy.spin(node)
    finally:
        node.pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
