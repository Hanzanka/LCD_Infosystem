import config
from typing import List
from RPLCD.i2c import CharLCD
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event
from time import sleep
from datetime import datetime
from .lcd_view import LCD_view

able_to_print = True
printing = False


class Dht22_view(LCD_view):

    """
    Displays data from DHT22 sensor to lcd screen

    Parameters:
        lcd: i2c.CharLCD -> lcd-object where data is displayed
    """

    def __init__(self, lcd: CharLCD) -> None:
        self.__lcd = lcd
        self.__observer = None
        self.__eventhandler = None
        self.__thread_event = None
        lcd.backlight_enabled = True
        self.__paths = config.dht22_paths

    def _update_data(self, data) -> None:

        """
        Updates given data to lcd screen

        Parameters:
            data: dict -> dictionary that has temp, and hum data stored in it
        """

        global able_to_print
        global printing

        while True:
            if not printing:
                able_to_print = False
                self.__lcd.cursor_pos = (0, 0)
                self.__lcd.write_string(f"Lämpötila:{data['temp']:>8}°C")
                self.__lcd.crlf()
                self.__lcd.write_string(f"Ilmankosteus:{data['hum']:>6}%")
                self.__lcd.crlf()
                self.__lcd.write_string(f"Mitattu klo{data['time']:>9}")
                able_to_print = True
                break
            else:
                sleep(1 / 1000)

    def __update_clock(self, x: int, y: int):

        global able_to_print
        global printing

        while True:
            if self.__thread_event.is_set():
                break
            if able_to_print:
                printing = True
                self.__lcd.cursor_pos = (y, x)
                self.__lcd.write_string(
                    f'Kellonaika: {datetime.now().time().strftime("%H.%M:%S")}'
                )
                printing = False
            sleep(1 / 10)

    def start(self) -> None:

        """
        Starts the view
        """

        self.__lcd.clear()

        self.__thread_event = Event()

        file_name = self.__paths["latest.csv"]
        self.__observer = Observer()
        self.__eventhandler = FileChangeHandler(self)
        self.__observer.schedule(self.__eventhandler, file_name)
        self.__observer.start()

        thread_clock = Thread(
            target=self.__update_clock,
            args=[
                0,
                3,
            ],
        )

        thread_clock.start()

    def close(self) -> None:

        """
        Closes the view
        """

        self.__thread_event.set()
        self.__observer.stop()
        self.__lcd.clear()


class FileChangeHandler(FileSystemEventHandler):

    """
    Used to detect changes in

    Parameters:
        view: View -> View where data is sent to be updated on the display
    """

    def __init__(self, view: Dht22_view) -> None:
        super().__init__()
        self.view = view
        self.file_name = config.dht22_paths["latest.csv"]

    def on_closed(self, event):
        data = self.__read_file()
        self.view._update_data(data)

    def __read_file(self) -> dict:
        with open(self.file_name, "r") as csv_file:
            keys = ["temp", "hum", "time", "date"]
            values = csv_file.read().split(";")
            if len(values) == 4 and isinstance(values, List):
                data = dict(zip(keys, values))
                return data


if __name__ == "__main__":
    lcd = CharLCD(
        i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
    )
    lcd.backlight_enabled = False
    lcd.display_enabled = True
    lcd.clear()

    k = Dht22_view(lcd)
    k.start()
