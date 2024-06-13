import sys
import logging
import yaml
import numpy as np
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets, uic, QtSvg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QMessageBox, QMainWindow, QApplication, QFileDialog

import logs
import version
import utils
import motion
import gui

LOGGER = logging.getLogger(__name__)
LOGGER.info('start')

COLOR_GREEN = '#33cc33'
COLOR_YELLOW = '#E5B500'
COLOR_RED = '#C0150E'
SETTINGS_FILE = 'config.yaml'


class Status():
    status = str

    limit_x = bool
    limit_y = bool
    limit_z = bool
    limit_a = bool

    pos_x = float
    pos_y = float
    pos_z = float
    pos_a = float

    block_buffer_avail = int
    rx_buffer_avail = int


if sys.platform == 'win32':
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


class VLine(QFrame):
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine | self.Sunken)


class MyWindowClass(QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindowClass, self).__init__(parent)

        self.current_motion_profile = None
        self.current_motion_filename = None
        self.hw_connected = False
        self.source_filename = ""
        self.status = Status()
        self.lens_name = None

        # Load settings from YAML
        self.config = {}
        self.config = utils.boot_routine(SETTINGS_FILE)
        LOGGER.info(self.config)

        self.setupUi(self)
        self.original_window_name = self.windowTitle()
        self.setWindowTitle(self.original_window_name + " (" + version.__version__ + ")")

        # Disable all groups initially
        self.group_step_size.setEnabled(False)
        self.group_speed.setEnabled(False)
        self.group_mdi.setEnabled(False)
        self.group_filter1.setEnabled(False)
        self.group_filter2.setEnabled(False)
        self.group_pi.setEnabled(False)
        self.group_iris.setEnabled(False)
        self.group_x_axis.setEnabled(False)
        self.group_y_axis.setEnabled(False)
        self.group_z_axis.setEnabled(False)
        self.group_a_axis.setEnabled(False)
        self.group_p1.setEnabled(False)
        self.group_p2.setEnabled(False)
        self.group_p3.setEnabled(False)
        self.group_p4.setEnabled(False)
        self.group_p5.setEnabled(False)

        # Com port
        self.btn_connect.clicked.connect(self.btn_connect_clicked)
        self.btn_disconnect.clicked.connect(self.btn_disconnect_clicked)
        self.btn_com_refresh.clicked.connect(self.btn_com_refresh_clicked)
        self.btn_mdi_send.clicked.connect(self.btn_mdi_send_clicked)

        # Prepare serial communications
        self.hw = motion.SerialComm()
        self.thread_serial = QtCore.QThread()
        self.hw.strStatus.connect(self.serStatus)
        self.hw.strVersion.connect(self.serVersion)
        self.hw.strError.connect(self.strError)
        self.hw.serFeedback.connect(self.serFeedback)
        self.hw.moveToThread(self.thread_serial)
        self.thread_serial.started.connect(self.hw.serial_worker)
        self.thread_serial.start()
        self.btn_com_refresh_clicked()

        # Functions
        self.btn_f1_on.clicked.connect(self.btn_f1_on_clicked)
        self.btn_f1_off.clicked.connect(self.btn_f1_off_clicked)
        self.btn_f2_on.clicked.connect(self.btn_f2_on_clicked)
        self.btn_f2_off.clicked.connect(self.btn_f2_off_clicked)
        self.btn_pi_led_on.clicked.connect(self.btn_pi_led_on_clicked)
        self.btn_pi_led_off.clicked.connect(self.btn_pi_led_off_clicked)
        self.btn_iris_on.clicked.connect(self.btn_iris_on_clicked)
        self.btn_iris_off.clicked.connect(self.btn_iris_off_clicked)
        self.btn_x_left.clicked.connect(self.btn_x_left_clicked)
        self.btn_x_right.clicked.connect(self.btn_x_right_clicked)
        self.btn_y_left.clicked.connect(self.btn_y_left_clicked)
        self.btn_y_right.clicked.connect(self.btn_y_right_clicked)
        self.btn_z_left.clicked.connect(self.btn_z_left_clicked)
        self.btn_z_right.clicked.connect(self.btn_z_right_clicked)
        self.btn_a_left.clicked.connect(self.btn_a_left_clicked)
        self.btn_a_right.clicked.connect(self.btn_a_right_clicked)
        self.btn_x_seek.clicked.connect(self.btn_x_seek_clicked)
        self.btn_y_seek.clicked.connect(self.btn_y_seek_clicked)
        self.btn_z_seek.clicked.connect(self.btn_z_seek_clicked)
        self.btn_a_seek.clicked.connect(self.btn_a_seek_clicked)
        self.push_pr1_set.clicked.connect(self.push_pr1_set_clicked)
        self.push_pr2_set.clicked.connect(self.push_pr2_set_clicked)
        self.push_pr3_set.clicked.connect(self.push_pr3_set_clicked)
        self.push_pr4_set.clicked.connect(self.push_pr4_set_clicked)
        self.push_pr5_set.clicked.connect(self.push_pr5_set_clicked)
        self.push_pr1_go.clicked.connect(self.push_pr1_go_clicked)
        self.push_pr2_go.clicked.connect(self.push_pr2_go_clicked)
        self.push_pr3_go.clicked.connect(self.push_pr3_go_clicked)
        self.push_pr4_go.clicked.connect(self.push_pr4_go_clicked)
        self.push_pr5_go.clicked.connect(self.push_pr5_go_clicked)

    def push_pr1_go_clicked(self):
        preset = self.config["lens"][self.lens_name]["preset"]["p1"].split(" ")
        cmd = "G90"
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            cmd += " X"
            cmd += preset[0]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            cmd += " Y"
            cmd += preset[1]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            cmd += " Z"
            cmd += preset[2]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            cmd += " A"
            cmd += preset[3]
        cmd += " F"
        cmd += self.combo_speed.currentText()
        self.hw.send(cmd + "\n")

    def push_pr2_go_clicked(self):
        preset = self.config["lens"][self.lens_name]["preset"]["p2"].split(" ")
        cmd = "G90"
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            cmd += " X"
            cmd += preset[0]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            cmd += " Y"
            cmd += preset[1]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            cmd += " Z"
            cmd += preset[2]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            cmd += " A"
            cmd += preset[3]
        cmd += " F"
        cmd += self.combo_speed.currentText()
        self.hw.send(cmd + "\n")

    def push_pr3_go_clicked(self):
        preset = self.config["lens"][self.lens_name]["preset"]["p3"].split(" ")
        cmd = "G90"
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            cmd += " X"
            cmd += preset[0]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            cmd += " Y"
            cmd += preset[1]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            cmd += " Z"
            cmd += preset[2]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            cmd += " A"
            cmd += preset[3]
        cmd += " F"
        cmd += self.combo_speed.currentText()
        self.hw.send(cmd + "\n")

    def push_pr4_go_clicked(self):
        preset = self.config["lens"][self.lens_name]["preset"]["p4"].split(" ")
        cmd = "G90"
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            cmd += " X"
            cmd += preset[0]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            cmd += " Y"
            cmd += preset[1]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            cmd += " Z"
            cmd += preset[2]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            cmd += " A"
            cmd += preset[3]
        cmd += " F"
        cmd += self.combo_speed.currentText()
        self.hw.send(cmd + "\n")

    def push_pr5_go_clicked(self):
        preset = self.config["lens"][self.lens_name]["preset"]["p5"].split(" ")
        cmd = "G90"
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            cmd += " X"
            cmd += preset[0]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            cmd += " Y"
            cmd += preset[1]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            cmd += " Z"
            cmd += preset[2]
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            cmd += " A"
            cmd += preset[3]
        cmd += " F"
        cmd += self.combo_speed.currentText()
        self.hw.send(cmd + "\n")

    def push_pr1_set_clicked(self):
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            val_x = str(self.status.pos_x)
        else:
            val_x = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            val_y = str(self.status.pos_y)
        else:
            val_y = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            val_z = str(self.status.pos_z)
        else:
            val_z = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            val_a = str(self.status.pos_a)
        else:
            val_a = "--"

        self.config["lens"][self.lens_name]["preset"]["p1"] = val_x + " " + val_y + " " + val_z + " " + val_a

        self.label_pr1_x.setText(val_x)
        self.label_pr1_y.setText(val_y)
        self.label_pr1_z.setText(val_z)
        self.label_pr1_a.setText(val_a)

    def push_pr2_set_clicked(self):
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            val_x = str(self.status.pos_x)
        else:
            val_x = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            val_y = str(self.status.pos_y)
        else:
            val_y = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            val_z = str(self.status.pos_z)
        else:
            val_z = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            val_a = str(self.status.pos_a)
        else:
            val_a = "--"

        self.config["lens"][self.lens_name]["preset"]["p2"] = val_x + " " + val_y + " " + val_z + " " + val_a

        self.label_pr2_x.setText(val_x)
        self.label_pr2_y.setText(val_y)
        self.label_pr2_z.setText(val_z)
        self.label_pr2_a.setText(val_a)

    def push_pr3_set_clicked(self):
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            val_x = str(self.status.pos_x)
        else:
            val_x = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            val_y = str(self.status.pos_y)
        else:
            val_y = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            val_z = str(self.status.pos_z)
        else:
            val_z = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            val_a = str(self.status.pos_a)
        else:
            val_a = "--"

        self.config["lens"][self.lens_name]["preset"]["p3"] = val_x + " " + val_y + " " + val_z + " " + val_a

        self.label_pr3_x.setText(val_x)
        self.label_pr3_y.setText(val_y)
        self.label_pr3_z.setText(val_z)
        self.label_pr3_a.setText(val_a)

    def push_pr4_set_clicked(self):
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            val_x = str(self.status.pos_x)
        else:
            val_x = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            val_y = str(self.status.pos_y)
        else:
            val_y = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            val_z = str(self.status.pos_z)
        else:
            val_z = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            val_a = str(self.status.pos_a)
        else:
            val_a = "--"

        self.config["lens"][self.lens_name]["preset"]["p4"] = val_x + " " + val_y + " " + val_z + " " + val_a

        self.label_pr4_x.setText(val_x)
        self.label_pr4_y.setText(val_y)
        self.label_pr4_z.setText(val_z)
        self.label_pr4_a.setText(val_a)

    def push_pr5_set_clicked(self):
        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
            val_x = str(self.status.pos_x)
        else:
            val_x = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
            val_y = str(self.status.pos_y)
        else:
            val_y = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
            val_z = str(self.status.pos_z)
        else:
            val_z = "--"

        if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
            val_a = str(self.status.pos_a)
        else:
            val_a = "--"

        self.config["lens"][self.lens_name]["preset"]["p5"] = val_x + " " + val_y + " " + val_z + " " + val_a

        self.label_pr5_x.setText(val_x)
        self.label_pr5_y.setText(val_y)
        self.label_pr5_z.setText(val_z)
        self.label_pr5_a.setText(val_a)

    def btn_x_seek_clicked(self):
        cmd = "$HX"
        self.hw.send(cmd + "\n")

    def btn_y_seek_clicked(self):
        cmd = "$HY"
        self.hw.send(cmd + "\n")

    def btn_z_seek_clicked(self):
        cmd = "$HZ"
        self.hw.send(cmd + "\n")

    def btn_a_seek_clicked(self):
        cmd = "$HA"
        self.hw.send(cmd + "\n")

    def btn_x_left_clicked(self):
        cmd = "G91 X-"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_x_right_clicked(self):
        cmd = "G91 X"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_y_left_clicked(self):
        cmd = "G91 Y-"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_y_right_clicked(self):
        cmd = "G91 Y"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_z_left_clicked(self):
        cmd = "G91 Z-"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_z_right_clicked(self):
        cmd = "G91 Z"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_a_left_clicked(self):
        cmd = "G91 A-"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_a_right_clicked(self):
        cmd = "G91 A"
        cmd += str(self.combo_step.currentText())
        cmd += " F"
        cmd += str(self.combo_speed.currentText())
        self.hw.send(cmd + "\n")

    def btn_f1_on_clicked(self):
        cmd = self.config["lens"][self.lens_name]["filter1"]["state_on"]

        if type(cmd) == str:
            self.hw.send(cmd + "\n")

        if type(cmd) == list:
            for c in cmd:
                self.hw.send(c + "\n")

    def btn_f1_off_clicked(self):
        cmd = self.config["lens"][self.lens_name]["filter1"]["state_off"]

        if type(cmd) == str:
            self.hw.send(cmd + "\n")

        if type(cmd) == list:
            for c in cmd:
                self.hw.send(c + "\n")

    def btn_f2_on_clicked(self):
        cmd = self.config["lens"][self.lens_name]["filter2"]["state_on"]

        if type(cmd) == str:
            self.hw.send(cmd + "\n")

        if type(cmd) == list:
            for c in cmd:
                self.hw.send(c + "\n")

    def btn_f2_off_clicked(self):
        cmd = self.config["lens"][self.lens_name]["filter2"]["state_off"]

        if type(cmd) == str:
            self.hw.send(cmd + "\n")

        if type(cmd) == list:
            for c in cmd:
                self.hw.send(c + "\n")

    def btn_pi_led_on_clicked(self):
        cmd = self.config["lens"][self.lens_name]["limit_sensor"]["led_on"]
        self.hw.send(cmd + "\n")

    def btn_pi_led_off_clicked(self):
        cmd = self.config["lens"][self.lens_name]["limit_sensor"]["led_off"]
        self.hw.send(cmd + "\n")

    def btn_iris_on_clicked(self):
        cmd = self.config["lens"][self.lens_name]["iris"]["open"]
        self.hw.send(cmd + "\n")

    def btn_iris_off_clicked(self):
        cmd = self.config["lens"][self.lens_name]["iris"]["close"]
        self.hw.send(cmd + "\n")

    def btn_mdi_send_clicked(self):
        self.hw.send(self.line_mdi.text() + "\n")

    def btn_connect_clicked(self):
        self.config["port"] = self.combo_ports.currentText()
        try:
            self.hw.connect(self.config["port"], self.config["com_baud"], self.config["com_timeout"])
        except Exception as e:
            LOGGER.error(f"Failed to connect: {e}")
            self.strError(f"Failed to connect: {e}")

    def btn_disconnect_clicked(self):
        try:
            self.hw.disconnect()
        except Exception as e:
            LOGGER.error(f"Failed to disconnect: {e}")
            self.strError(f"Failed to disconnect: {e}")

    def btn_com_refresh_clicked(self):
        self.combo_ports.clear()
        com_ports = sorted(self.hw.get_compot_list())
        for port, desc in com_ports:
            self.combo_ports.addItem(port.strip())
        self.combo_ports.setCurrentIndex(self.combo_ports.findText(self.config["port"]))
        
        # Add default Linux serial port options
        self.combo_ports.addItem("/dev/ttyUSB0")
        self.combo_ports.addItem("/dev/ttyS0")

    def serStatus(self, text):
        self.s_status.setText(text)
        self.combo_ports.setEnabled(False)
        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(False)
        
        if text == "Connected":
            self.hw_connected = True
            self.hw.action_recipe.put("status1")
            self.hw.action_recipe.put("version")
            self.hw.action_recipe.put("get_param_list")
            
        elif text == "Disconnected":
            self.hw_connected = False

        elif text == "Error":
            self.hw_connected = False
            self.strError("Serial connection error")

        self.update_enabled_elements()

    def update_enabled_elements(self):
        if not self.hw.commands.empty():
            self.push_run.setEnabled(False)

        if self.hw_connected:
            self.combo_ports.setEnabled(False)
            self.btn_connect.setEnabled(False)
            self.btn_com_refresh.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
        else:
            self.combo_ports.setEnabled(True)
            self.btn_connect.setEnabled(True)
            self.btn_com_refresh.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            
            # Re-enable potential serial port errors visibility
            if self.s_status.text() == "Error":
                self.btn_connect.setEnabled(True)

    def strError(self, text):
        LOGGER.error(text)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")
        msg.exec_()

        # Ensure error status is updated for reconnection attempts
        self.s_status.setText("Error")
        self.update_enabled_elements()

    def serVersion(self, text):
        self.s_controller_fw.setText(text)

        try:
            # Expecting: [VER:1.1f-SCE2.20211130:L086,6ZG-BEG19]
            txt = text.replace('[', '').replace(']', '')
            LOGGER.info(f"Parsed version string: {txt}")

            txt_list = txt.split(':')
            LOGGER.info(f"Version string components: {txt_list}")

            if len(txt_list) < 3:
                raise ValueError("Unexpected version string format")
            
            id_strings = txt_list[2].split(',')
            LOGGER.info(f"ID strings: {id_strings}")

            lens_detected = False
            for i in id_strings:
                if i[0:3] == "LS8":
                    self.lens_name = "L085"
                    self.label_lens_name.setText(self.lens_name)
                    lens_detected = True

                if i[0:3] == "6ZG":
                    self.lens_name = "L086"
                    self.label_lens_name.setText(self.lens_name)
                    lens_detected = True

                if i[0:3] == "JWF":
                    self.lens_name = "L084"
                    self.label_lens_name.setText(self.lens_name)
                    lens_detected = True

                if lens_detected:
                    cmd = self.config["lens"][self.lens_name]["limit_sensor"]["led_on"]
                    self.hw.send(cmd + "\n")
                    cmd = self.config["lens"][self.lens_name]["iris"]["open"]
                    self.hw.send(cmd + "\n")

                    self.group_step_size.setEnabled(True)
                    self.combo_step.clear()
                    default_step = None
                    step_list = self.config["lens"][self.lens_name]["motor"]["step_list"].split(" ")
                    for i in step_list:
                        if "*" in i:
                            default_step = i.replace("*", "")
                        self.combo_step.addItem(i.replace("*", ""))
                    if default_step:
                        self.combo_step.setCurrentText(default_step)

                    self.group_speed.setEnabled(True)
                    self.combo_speed.clear()
                    default_speed = None
                    speed_list = self.config["lens"][self.lens_name]["motor"]["speed_list"].split(" ")
                    for i in speed_list:
                        if "*" in i:
                            default_speed = i.replace("*", "")
                        self.combo_speed.addItem(i.replace("*", ""))
                    if default_speed:
                        self.combo_speed.setCurrentText(default_speed)

                    self.group_mdi.setEnabled(True)

                    if "filter1" in self.config["lens"][self.lens_name]:
                        self.group_filter1.setEnabled(True)
                        self.group_filter1.setTitle("Filter: " + self.config["lens"][self.lens_name]["filter1"]["name"])

                    if "filter2" in self.config["lens"][self.lens_name]:
                        self.group_filter2.setEnabled(True)
                        self.group_filter2.setTitle("Filter: " + self.config["lens"][self.lens_name]["filter2"]["name"])

                    self.group_pi.setEnabled(True)

                    if "iris" in self.config["lens"][self.lens_name]:
                        self.group_iris.setEnabled(True)

                    self.group_p1.setEnabled(True)
                    self.group_p2.setEnabled(True)
                    self.group_p3.setEnabled(True)
                    self.group_p4.setEnabled(True)
                    self.group_p5.setEnabled(True)

                    preset = self.config["lens"][self.lens_name]["preset"]["p1"].split(" ")
                    self.label_pr1_x.setText(preset[0])
                    self.label_pr1_y.setText(preset[1])
                    self.label_pr1_z.setText(preset[2])
                    self.label_pr1_a.setText(preset[3])

                    preset = self.config["lens"][self.lens_name]["preset"]["p2"].split(" ")
                    self.label_pr2_x.setText(preset[0])
                    self.label_pr2_y.setText(preset[1])
                    self.label_pr2_z.setText(preset[2])
                    self.label_pr2_a.setText(preset[3])

                    preset = self.config["lens"][self.lens_name]["preset"]["p3"].split(" ")
                    self.label_pr3_x.setText(preset[0])
                    self.label_pr3_y.setText(preset[1])
                    self.label_pr3_z.setText(preset[2])
                    self.label_pr3_a.setText(preset[3])

                    preset = self.config["lens"][self.lens_name]["preset"]["p4"].split(" ")
                    self.label_pr4_x.setText(preset[0])
                    self.label_pr4_y.setText(preset[1])
                    self.label_pr4_z.setText(preset[2])
                    self.label_pr4_a.setText(preset[3])

                    preset = self.config["lens"][self.lens_name]["preset"]["p5"].split(" ")
                    self.label_pr5_x.setText(preset[0])
                    self.label_pr5_y.setText(preset[1])
                    self.label_pr5_z.setText(preset[2])
                    self.label_pr5_a.setText(preset[3])

                    if self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"]:
                        self.group_x_axis.setEnabled(True)
                        self.group_x_axis.setTitle("X axis / " + self.config["lens"][self.lens_name]["motor"]["function"]["axis_x"])

                    if self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"]:
                        self.group_y_axis.setEnabled(True)
                        self.group_y_axis.setTitle("Y axis / " + self.config["lens"][self.lens_name]["motor"]["function"]["axis_y"])

                    if self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"]:
                        self.group_z_axis.setEnabled(True)
                        self.group_z_axis.setTitle("Z axis / " + self.config["lens"][self.lens_name]["motor"]["function"]["axis_z"])

                    if self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"]:
                        self.group_a_axis.setEnabled(True)
                        self.group_a_axis.setTitle("A axis / " + self.config["lens"][self.lens_name]["motor"]["function"]["axis_a"])

        except (IndexError, ValueError) as e:
            LOGGER.error(f"Failed to parse version string: {e} | Received text: {text}")
            self.strError(f"Failed to parse version string: {e}")

    def serFeedback(self, text):
        txt = text.replace('<', '').replace('>', '')
        txt_list = txt.split("|")
        s = Status()
        s.status = txt_list[0]  # always first element

        for p in txt_list[1:]:
            if p[0:2] == "Bf":
                temp1 = p.split(":")[1]
                s.block_buffer_avail = int(temp1.split(",")[0])
                s.rx_buffer_avail = int(temp1.split(",")[1])

            s.limit_x = False
            s.limit_y = False
            s.limit_z = False
            s.limit_a = False

            if p[0:2] == "Pn":
                temp1 = p.split(":")[1]
                s.limit_x = "X" in temp1
                s.limit_y = "Y" in temp1
                s.limit_z = "Z" in temp1
                s.limit_a = "A" in temp1

            if p[0:4] == "MPos":
                temp1 = p.split(":")[1]
                s.pos_x = float(temp1.split(",")[0])
                s.pos_y = float(temp1.split(",")[1])
                s.pos_z = float(temp1.split(",")[2])
                s.pos_a = float(temp1.split(",")[3])

        self.status = s

        self.label_x_pos.setText(str(round(s.pos_x, 3)))
        self.label_y_pos.setText(str(round(s.pos_y, 3)))
        self.label_z_pos.setText(str(round(s.pos_z, 3)))
        self.label_a_pos.setText(str(round(s.pos_a, 3)))

        self.btn_x_seek.setEnabled(True)
        self.btn_y_seek.setEnabled(True)
        self.btn_z_seek.setEnabled(True)
        self.btn_a_seek.setEnabled(True)

        self.label_buffer_count.setText(str(s.block_buffer_avail))
        self.label_motion_status.setText(str(s.status))

    def closeEvent(self, event):
        global config
        global running

        if self.s_status.text() == "Connected":
            p1 = self.label_pr1_x.text() + " " + self.label_pr1_y.text() + " " + self.label_pr1_z.text() + " " + self.label_pr1_a.text()
            self.config["lens"][self.lens_name]["preset"]["p1"] = p1

            p2 = self.label_pr2_x.text() + " " + self.label_pr2_y.text() + " " + self.label_pr2_z.text() + " " + self.label_pr2_a.text()
            self.config["lens"][self.lens_name]["preset"]["p2"] = p2

            p3 = self.label_pr3_x.text() + " " + self.label_pr3_y.text() + " " + self.label_pr3_z.text() + " " + self.label_pr3_a.text()
            self.config["lens"][self.lens_name]["preset"]["p3"] = p3

            p4 = self.label_pr4_x.text() + " " + self.label_pr4_y.text() + " " + self.label_pr4_z.text() + " " + self.label_pr4_a.text()
            self.config["lens"][self.lens_name]["preset"]["p4"] = p4

            p5 = self.label_pr5_x.text() + " " + self.label_pr5_y.text() + " " + self.label_pr5_z.text() + " " + self.label_pr5_a.text()
            self.config["lens"][self.lens_name]["preset"]["p5"] = p5

        utils.exit_routine(SETTINGS_FILE, self.config)
        running = False
        app.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    myWindow = MyWindowClass(None)
    myWindow.show()
    sys.exit(app.exec_())
