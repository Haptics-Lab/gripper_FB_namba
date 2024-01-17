# Arduino_gripper_out.inoとセット！！
import csv  # 記録用
import sys
import threading
import time

import numpy as np
import serial
from ArmWrapper1000 import ArmWrapper
from xarm.wrapper import XArmAPI


class Text_class:
    def __init__(self):
        self.bendingValue2 = 0
        self.grippos = 0
        self.flag = 0
        self.loadcell_int = 127
        ip = "192.168.1.199"
        arduino_port = "COM8"
        baud_rate = 115200
        self.ser = serial.Serial(arduino_port, baud_rate)
        not_used = self.ser.readline()
        self.arm = XArmAPI(ip)
        time.sleep(0.5)
        if self.arm.warn_code != 0:
            self.arm.clean_warn()
        if self.arm.error_code != 0:
            self.arm.clean_error()
        self.arm.motion_enable(True)
        self.arm.set_mode(0)
        self.arm.set_state(0)
        self.datal = ArmWrapper(True, ip)
        thr1 = threading.Thread(target=self.moveloop)
        thr1.setDaemon(True)
        thr1.start()
        thr2 = threading.Thread(target=self.sendloop)
        thr2.setDaemon(True)
        thr2.start()
        thr3 = threading.Thread(target=self.receiveloop)
        thr3.setDaemon(True)
        thr3.start()

    # 記録データからグリッパー動かす
    def moveloop(self):
        with open(
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul10_100.csv"
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul10_150.csv"
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul10_200.csv"
            "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul20_100.csv"
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul20_150.csv"
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul20_200.csv"
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul40_100.csv"
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul40_150.csv"  # 中間、硬いが力位置ほぼ同じ
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul40_200.csv"  # 中間、硬いが力位置ほぼ同じ
            # "C:\\Users\\SANOLAB\\Documents\\GitHub\\gripper_FB_namba\\cul40_250.csv"    #力なし
        ) as f1:
            reader = csv.reader(f1)
            self.l1 = [row for row in reader]
        self.count = 0
        self.start_time = time.perf_counter()
        while True:
            # self.bendingValue_int = int(400 - int(self.l1[self.count][0]) * 400 / 2800)
            self.bendingValue_int = int(float(self.l1[self.count][1]))
            if self.bendingValue_int > 400:
                self.bendingValue_int = 400
            elif self.bendingValue_int < 0:
                self.bendingValue_int = 0
            code, ret = self.arm.getset_tgpio_modbus_data(
                self.datal.ConvertToModbusData(self.bendingValue_int)
            )
            self.count += 1
            time.sleep(0.00005)

    # 記録データをArduinoへ送る
    def sendloop(self):
        self.init_loadcell_val = self.arm.get_cgpio_analog(1)[1]
        while True:
            self.loadcell = (
                float(self.arm.get_cgpio_analog(1)[1]) - float(self.init_loadcell_val)
            ) * 1000
            if self.loadcell > 200:
                self.loadcell = 200
            elif self.loadcell < 0:
                self.loadcell = 0
            self.loadcell_int = int(self.loadcell / (200 - 0) * (255 - 127) + 127)
            # 掴み始め・離し始め
            if self.flag == 0 and self.loadcell_int >= 130:
                # self.grippos = int(self.bendingValue_int * 255 / 2800)
                self.grippos = self.arm.get_gripper_position()[1] / 400 * 255
                self.flag = 1
            elif self.loadcell_int < 130:
                self.grippos = 0
                self.flag = 0
            if self.flag == 0:
                self.num = int(0)
            else:
                # self.num = int((int(self.l2[self.count2][0]) * 255 / 2800 - self.grippos) * (255 - 0)/ (255 - self.grippos))
                self.num = int(
                    (self.grippos - self.arm.get_gripper_position()[1] / 400 * 255)
                    * (255 - 0)
                    / (self.grippos - 0)
                )
            if self.num > 255:
                self.num = 255
            elif self.num < 0:
                self.num = 0
            self.ser.write(bytes([self.num]))
            time.sleep(0.005)

    # Arduinoからデータを受け取る
    def receiveloop(self):
        while True:
            self.line = self.ser.readline().decode("utf-8").rstrip()
            print(
                # 2200 - int(self.arm.get_gripper_position()[1] / 400 * 2200),
                int(self.arm.get_gripper_position()[1]),
                self.loadcell_int,
                self.line,
            )


if __name__ == "__main__":
    text_class = Text_class()
    while True:
        try:
            time.sleep(0.005)
        except KeyboardInterrupt:
            print("KeyboardInterrupt Stop:text")
            break