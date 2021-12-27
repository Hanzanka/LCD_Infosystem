from typing import List
from RPLCD import i2c
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
from time import sleep
from datetime import datetime
from view import View

able_to_print = True
printing = False


class Dht22_view(View):

    """
    Displays data from DHT22 sensor to lcd screen

    Parameters:
        lcd: i2c.CharLCD -> lcd-object where data is displayed
    """

    def __init__(self, lcd: i2c.CharLCD) -> None:
        self.__lcd = lcd
        self.__observer = Observer()
        self.__eventhandler = FileChangeHandler(self)
        self.__threads = []
        lcd.backlight_enabled = True

    def __start_observer(self) -> None:

        """
        Starts observer for detecting changes in latest.csv file
        """

        file_name = "/home/ville/python/infosystem_project/data/temperature_and_humidity/latest.csv"
        self.__observer.schedule(self.__eventhandler, file_name)
        self.__observer.start()

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

        """
        Updates current time in format xxH.xxM.xxS every tenth of a second

        Parameters:
            x: int -> lcd row where time is displayed
            y: int -> lcd column where time is displayed
        """

        global able_to_print
        global printing

        while True:
            if able_to_print:
                printing = True
                self.__lcd.cursor_pos = (y, x)
                self.__lcd.write_string(
                    f'Kello:{datetime.now().time().strftime("%H.%M:%S"):>14}'
                )
                printing = False
            sleep(1 / 10)

    def launch(self) -> None:

        """
        Starts the view
        """

        thread_clock = Thread(
            target=self.__update_clock,
            args=[
                0,
                3,
            ],
        )

        thread_observe = Thread(
            target=self.__start_observer,
            args=[],
        )

        thread_clock.start()
        thread_observe.start()

        self.__threads.append(thread_clock)
        self.__threads.append(thread_observe)

    def close(self) -> None:
        for t in self.__threads:
            t.stop()
        self.__observer.stop()


class FileChangeHandler(FileSystemEventHandler):

    """
    When file given to observer is closed this class will read the file and sends data to view to be updated on the display

    Parameters:
        view: View -> View where data is sent to be updated on the display
    """

    def __init__(self, view: Dht22_view) -> None:
        super().__init__()
        self.view = view
        self.file_name = "/home/ville/python/infosystem_project/data/temperature_and_humidity/latest.csv"

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
