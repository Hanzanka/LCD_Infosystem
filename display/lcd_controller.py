from datetime import datetime
import multiprocessing
from multiprocessing import Queue
from queue import Empty
from RPLCD import i2c
from time import clock, sleep
from dataclasses import astuple
import threading

able_to_print = True
printing = False


class LCD:
    def __init__(self) -> None:

        self.lcd = i2c.CharLCD(
            i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
        )
        self.lcd.backlight_enabled = False
        self.lcd.display_enabled = True
        self.lcd.clear()

    def get_lcd(self) -> i2c.CharLCD:
        return self.lcd

    def display_dht22(self, pipe) -> None:

        global able_to_print
        global printing

        while True:

            data = pipe.recv()
            temp, hum, time, date = astuple(data)

            if printing:
                able_to_print = False
                sleep(0.1)
            else:
                able_to_print = False
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(f"Lämpötila: {temp}°C")
            self.lcd.crlf()
            self.lcd.write_string(f"Ilmankosteus: {hum}%")
            self.lcd.crlf()
            self.lcd.write_string(f"Mitattu klo {time}")
            able_to_print = True

    def launch_dht22_display(self, pipe):

        self.lcd.backlight_enabled = True

        display_dht_thread = threading.Thread(
            target=self.display_dht22,
            args=[pipe],
        )

        update_clock_thread = threading.Thread(target=self.update_clock, args=[0, 3])

        display_dht_thread.start()
        update_clock_thread.start()

    def launch_network_display(self, pipe):
        self.display_network_speed(pipe)

    def update_clock(self, x: int, y: int):

        """
        Updates current time on lcd screen to given position every second

        Parameters:
            x: int -> x-cordinate of clock
            y: y-cordinate of clock
        """

        global able_to_print
        global printing

        while True:
            if able_to_print:
                printing = True
                self.lcd.cursor_pos = (y, x)
                self.lcd.write_string(datetime.now().time().strftime("%H.%M:%S"))
                printing = False
                sleep(1)
            else:
                sleep(0.2)

    def display_network_speed(self, queue: Queue):
        self.lcd.backlight_enabled = True
        self.lcd.clear()
        global able_to_print
        global printing

        down = (
            0b00000,
            0b00100,
            0b00100,
            0b00100,
            0b10101,
            0b01110,
            0b00100,
            0b00000,
        )

        self.lcd.create_char(0, down)

        while True:
            if able_to_print:
                while True:
                    if queue.empty() is not True:
                        data = queue.get()
                        queue.put(data)
                        printing = True
                        x, y = data["monitor"]["pos"]
                        speed = data["monitor"]["speed"]
                        self.lcd.cursor_pos = (y, x)
                        self.lcd.write_string(f"{speed}\x00")
                        printing = False
                    else:
                        sleep(1 / 1000000)
            else:
                sleep(0.1)


if __name__ == "__main__":
    lcd = LCD()
    lcd.lcd.display_enabled = False
