#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste isolado do servomotor MG995 via PCA9685.
Move o servo entre 0, 90 e 180 graus em loop.

Dr. da Robotica - #DaEscolaAIndustria
"""

import time
from adafruit_servokit import ServoKit

# Configuracao
pca = ServoKit(channels=16)

# Largura de pulso para o MG995 (em microssegundos)
MIN_IMP = 500
MAX_IMP = 2500

# Servo conectado ao canal 0 da PCA9685
pca.servo[0].set_pulse_width_range(MIN_IMP, MAX_IMP)


def main():
    print("Testando servo MG995 no canal 0...")
    try:
        while True:
            print("Posicao 0 graus")
            pca.servo[0].angle = 0
            time.sleep(1)

            print("Posicao 90 graus")
            pca.servo[0].angle = 90
            time.sleep(1)

            print("Posicao 180 graus")
            pca.servo[0].angle = 180
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando teste.")


if __name__ == "__main__":
    main()
