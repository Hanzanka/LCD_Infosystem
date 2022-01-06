import os
import sys
import config
from multiprocessing import Process
from multiprocessing.connection import Pipe
from display import speedtest_view
from display.lcd_builder import LCD
from display.menu import Menu
import sys, tty, os, termios
from display.speedtest_view import Internet_speedtest_view
from RPLCD.i2c import CharLCD


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
                    print('Sending key:', key)
                    self.__pipe.send(key)
        except (KeyboardInterrupt, SystemExit):
            print("stopping.")


def main():

    keylogger_end, menu_end = Pipe()
    keylogger = KeyLogger(keylogger_end)
    # lcd = LCD()
    # menu = Menu(lcd.get_lcd(), menu_end)

    # process1 = Process(target=menu.start)
    # process1.start()

    lcd = CharLCD(
        i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
    )
    speedtest_view = Internet_speedtest_view(lcd)
    speedtest_view.start(menu_end)

    keylogger.start()

main()
