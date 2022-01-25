import os
import sys
from multiprocessing import Process
from multiprocessing.connection import Pipe
from display.menu import Menu
import sys
import tty
import os
import termios


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
                if key == "3":
                    quit()
                else:
                    print("Sending key:", key)
                    self.__pipe.send(key)
        except (KeyboardInterrupt, SystemExit):
            print("stopping.")


def main():

    keylogger_end, menu_end = Pipe()
    keylogger = KeyLogger(keylogger_end)
    menu = Menu(menu_end)

    process1 = Process(target=menu.start)
    process1.start()

    # speedtest_view = Internet_speedtest_view(lcd)
    # speedtest_view.start(menu_end)

    keylogger.start()


main()
