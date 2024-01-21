# Arduino_gripper_out.inoとセット！！,押し込み表現拡大，ロボtグリッパー掴みから100まで
import csv
import math
import threading
import time

import numpy as np
import serial
from ArmWrapper1000 import ArmWrapper
from xarm.wrapper import XArmAPI


class Text_class:
    def __init__(self):
        # [[2, 2, 2], [4, 2, 1]]
        # self.oshikomi, self.speed = 250, 20
        # self.oshikomi, self.speed =230, 20
        self.oshikomi, self.speed = 200, 1

        # [[1, 1, 2], [1, 4, 2]]
        # self.oshikomi, self.speed =  210 , 10
        # self.oshikomi, self.speed = 190, 40
        # self.oshikomi, self.speed = 230, 40

        # [[2, 2, 2], [2, 1, 4]]
        # self.oshikomi, self.speed =  230 , 20
        # self.oshikomi, self.speed =  210 , 40
        # self.oshikomi, self.speed =  190 , 10

        # [[1, 1, 2], [2, 4, 1]]
        # self.oshikomi, self.speed =  170 , 10
        # self.oshikomi, self.speed =  250 , 40
        # self.oshikomi, self.speed =  150 , 10

        # [[2, 1, 1], [4, 1, 2]]
        # self.oshikomi, self.speed =  250 , 40
        # self.oshikomi, self.speed =  150 , 10
        # self.oshikomi, self.speed =  170 , 10

        # [[2, 1, 1], [1, 2, 4]]
        # self.oshikomi, self.speed =  150 , 10
        # self.oshikomi, self.speed =  170 , 20
        # self.oshikomi, self.speed =  190 , 10

        # [[2, 1, 1], [2, 1, 4]]
        # self.oshikomi, self.speed =  170 , 40
        # self.oshikomi, self.speed =  150 , 10
        # self.oshikomi, self.speed =  190 , 20

        # [[2, 1, 2], [1, 2, 4]]
        # self.oshikomi, self.speed =  150 , 10
        # self.oshikomi, self.speed =  170 , 40
        # self.oshikomi, self.speed =  250 , 40

        # [[2, 2, 2], [4, 2, 1]]
        # self.oshikomi, self.speed =  190 , 20
        # self.oshikomi, self.speed =  230 , 10
        # self.oshikomi, self.speed =  210 , 20

        # [2, 2, 2] [4, 2, 1]
        # [1, 1, 2] [1, 4, 2]
        # [2, 2, 2] [2, 1, 4]
        # [1, 1, 2] [2, 4, 1]
        # [2, 1, 1] [4, 1, 2]
        # [2, 1, 1] [1, 2, 4]
        # [2, 1, 1] [2, 1, 4]
        # [2, 1, 2] [1, 2, 4]
        # [2, 2, 2] [4, 2, 1]

        self.data2 = 400
        self.num = 0
        self.grippos = 0
        self.flag = 0
        self.start_time = time.perf_counter()
        self.e = math.e
        ip = "192.168.1.199"
        arduino_port = "COM8"
        baud_rate = 115200
        self.ser = serial.Serial(arduino_port, baud_rate)
        not_used = self.ser.readline()
        self.arm = XArmAPI(ip)
        self.datal = ArmWrapper(True, ip)
        self.datal.loadcell_int = 127
        time.sleep(0.5)
        if self.arm.warn_code != 0:
            self.arm.clean_warn()
        if self.arm.error_code != 0:
            self.arm.clean_error()
        self.arm.motion_enable(True)
        self.arm.set_mode(0)
        self.arm.set_state(0)

        thr2 = threading.Thread(target=self.sendloop)
        thr2.setDaemon(True)
        thr2.start()
        thr3 = threading.Thread(target=self.moveloop)
        thr3.setDaemon(True)
        thr3.start()

    # グリッパーの値をArduinoへ送る
    def sendloop(self):
        while True:
            # 掴み始め・離し始め
            if self.flag == 0 and self.datal.loadcell_int >= 129:
                self.grippos = self.arm.get_gripper_position()[1]
                self.flag = 1
            elif self.datal.loadcell_int < 129:
                self.grippos = 0
                self.flag = 0
            if self.flag == 0:
                self.num = int(0)
            else:
                self.num = int(
                    (self.grippos - self.arm.get_gripper_position()[1])
                    * (255 - 0)
                    / (self.grippos - 120)  # 止まるところでグリッパー閉じ切る
                )
            if self.num > 255:
                self.num = 255
            elif self.num < 0:
                self.num = 0
            self.ser.write(bytes([self.num]))
            time.sleep(0.01)

    def moveloop(self):
        while True:
            self.data1 = time.perf_counter() - self.start_time
            if self.data1 < 1 / self.speed:
                self.data2 = 400 - (400 - self.oshikomi) / (
                    1 + self.e ** -((self.data1) * self.speed - 10)
                )
            elif self.data1 < 1 / self.speed * 2:
                self.data2 = 400 - (400 - self.oshikomi) / (
                    1 + self.e ** ((self.data1) * self.speed - 30)
                )
            code, ret = self.arm.getset_tgpio_modbus_data(
                self.datal.ConvertToModbusData(self.data2)
            )
            # print(self.data2)
            time.sleep(0.005)


if __name__ == "__main__":
    text_class = Text_class()
    while True:
        try:
            text_class.line = text_class.ser.readline().decode("utf-8").rstrip()
            print(
                # 2200 - int(self.arm.get_gripper_position()[1] / 400 * 2200),
                text_class.datal.loadcell_int,
                int(text_class.arm.get_gripper_position()[1]),
                text_class.line,
            )
            # time.sleep(0.01)
        except KeyboardInterrupt:
            print("KeyboardInterrupt Stop:text")
            break
