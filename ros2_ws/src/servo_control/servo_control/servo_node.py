#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
No ROS 2 que controla o servomotor da garra via PCA9685.
Inscreve-se no topico /servo_angle (std_msgs/Float32) e move o servo.

Dr. da Robotica - #DaEscolaAIndustria
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from adafruit_servokit import ServoKit


class ServoNode(Node):
    def __init__(self):
        super().__init__('servo_node')
        self.kit = ServoKit(channels=16)
        # Largura de pulso do MG995 no canal 0
        self.kit.servo[0].set_pulse_width_range(500, 2500)

        self.subscription = self.create_subscription(
            Float32,
            'servo_angle',
            self.angle_callback,
            10)
        self.get_logger().info('Servo node iniciado! Aguardando comandos...')

    def angle_callback(self, msg):
        angle = float(msg.data)
        # Limita entre 0 e 180 graus por seguranca
        angle = max(0.0, min(180.0, angle))
        self.kit.servo[0].angle = angle
        self.get_logger().info(f'Servo movido para {angle} graus')


def main(args=None):
    rclpy.init(args=args)
    node = ServoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
