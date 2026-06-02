#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor TCP que recebe comandos de angulo do UR7e e publica
no topico ROS 2 /servo_angle (std_msgs/Float32).

O UR7e conecta via socket na porta 5000, envia o angulo como
texto seguido de '\\n' (socket_send_line) e fecha a conexao.

Dr. da Robotica - #DaEscolaAIndustria
"""

import socket
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

HOST = '0.0.0.0'   # escuta em todas as interfaces
PORT = 5000


class TCPServoServer(Node):
    def __init__(self):
        super().__init__('tcp_servo_server')
        self.publisher = self.create_publisher(Float32, 'servo_angle', 10)

        # Configura o servidor TCP
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(1)
        self.get_logger().info(
            f'Servidor TCP aguardando conexao na porta {PORT}...')

        self.accept_connection()

    def accept_connection(self):
        while rclpy.ok():
            self.get_logger().info('Aguardando UR7e conectar...')
            conn, addr = self.server.accept()
            self.get_logger().info(f'UR7e conectado: {addr}')
            self.handle_client(conn)

    def handle_client(self, conn):
        while rclpy.ok():
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    break
                angle = float(data)
                angle = max(0.0, min(180.0, angle))
                msg = Float32()
                msg.data = angle
                self.publisher.publish(msg)
                self.get_logger().info(
                    f'Angulo recebido do UR7e: {angle} graus')
                conn.send(b'OK\n')
            except Exception as e:
                self.get_logger().error(f'Erro: {e}')
                break
        conn.close()
        self.get_logger().info('UR7e desconectado')


def main(args=None):
    rclpy.init(args=args)
    node = TCPServoServer()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
