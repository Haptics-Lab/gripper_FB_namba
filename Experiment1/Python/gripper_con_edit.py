# Arduino_gripper_out.inoとセット！！,押し込み表現拡大，ロボtグリッパー掴みから100まで
import threading
import time

import numpy as np

import serial
from ArmWrapper1000 import ArmWrapper
from scipy import stats as st
from xarm.wrapper import XArmAPI

class Text_class:
    def __init__(self):
        self.x_data = np.array([])
        self.x_data = np.array([])
        self.x_list = np.array([])
        self.y_list = np.array([])
        self.slope_h = 0
        self.grippos = 0
        self.flag = 0
        self.sample_list = [1, 2, 4]
        ip = "192.168.1.199"
        self.ser = serial.Serial("COM8", 115200)
        not_used = self.ser.readline()
        self.ser2 = serial.Serial("COM7", 115200)
        self.not_used = self.ser2.readline()
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
        thr0 = threading.Thread(target=self.sendloop)
        thr0.setDaemon(True)
        thr0.start()

    def sendloop(self):
        slope = 0
        while True:
            # 掴み始め・離し始め
            if self.flag == 0 and self.datal.loadcell_int >= 130:
                self.grip = self.arm.get_gripper_position()[1]
                self.flag = 1
            elif self.datal.loadcell_int < 130:
                self.grip = 0
                self.flag = 0
                self.x_list = np.array([])
                self.y_list = np.array([])
                self.slope_h = 0
            if self.flag == 1:
                self.x_list = np.append(
                    self.x_list, [self.grip - self.arm.get_gripper_position()[1]]
                )
                self.y_list = np.append(self.y_list, [self.datal.loadcell_int - 129])
                # データ数が10を超えたら古いデータを削除!!!最初の数字を(0,0)にしないと最小二乗法ですべての点が同じ時に傾きがぶれやすくなる！！
                if len(self.x_list) > 10:
                    self.x_list = self.x_list[2:]
                    self.y_list = self.y_list[2:]
                    self.x_list = np.insert(self.x_list, 0, 0)
                    self.y_list = np.insert(self.y_list, 0, 0)
                if len(self.x_list) >= 10:
                    self.x_data = np.array([self.x_list])
                    self.y_data = np.array([self.y_list])
                    if np.std(self.x_data) == 0:
                        pass
                    else:
                        slope, intercept, r_value, p_value, std_err = st.linregress(
                            self.x_data[-1:-11:-1], self.y_data[-1:-11:-1]
                        )
                    if slope < 0.2 or slope > 3:
                        slope = 3
                    slope = 1 / slope
                    self.slope_h = int((slope - 1 / 3) * (255 - 0))
                    if self.slope_h > 200:
                        self.slope_h = 200
                    elif self.slope_h < 0:
                        self.slope_h = 0
            self.ser2.write(bytes([self.slope_h]))
            time.sleep(0.0005)