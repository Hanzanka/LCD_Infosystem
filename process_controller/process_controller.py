from multiprocessing import Queue, Process
from multiprocessing.connection import Pipe
import sys

sys.path.insert(0, "/home/ville/python/infosystem_project/")

from time import sleep
from display.lcd_controller import LCD
from display.dht22_sensor_view import Dht22_view
from display.menu import Menu
from internet_speedtest.networkmonitor import NetworkMonitor as Monitor
from internet_speedtest import speedtester
import sys, tty, os, termios


class KeyLogger:
    def __init__(self, pipe: Pipe()) -> None:
        self.__pipe = pipe

    def __getkey(self):
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        try:
            while True:
                b = os.read(sys.stdin.fileno(), 3).decode()
                if len(b) == 3:
                    k = ord(b[2])
                else:
                    k = ord(b)
                key_mapping = {
                    127: "backspace",
                    10: "enter",
                    32: "space",
                    9: "tab",
                    27: "esc",
                    65: "up",
                    66: "down",
                    67: "right",
                    68: "left",
                }
                return key_mapping.get(k, chr(k))
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def start(self):
        try:
            while True:
                key = self.__getkey()
                if key == "esc":
                    quit()
                else:
                    self.__pipe.send(key)
        except (KeyboardInterrupt, SystemExit):
            print("stopping.")


def main():

    keylogger_end, menu_end = Pipe()

    keylogger = KeyLogger(keylogger_end)
    lcd = LCD()
    menu = Menu(lcd.get_lcd(), menu_end)

    process1 = Process(target=menu.start)
    process1.start()

    keylogger.start()


main()
