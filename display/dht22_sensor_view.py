import config
from typing import List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event, Timer
from datetime import datetime
from display.lcd_controller import LCD_controller
from .lcd_view import LCD_view


class Dht22_view(LCD_view):

    """
    Displays data from DHT22 sensor to lcd screen

    Parameters:
        lcd_controller: LCD_controller -> LCD_controller is used to access 2004-lcd
    """

    def __init__(self, lcd_controller: LCD_controller) -> None:
        self.__lcd_controller = lcd_controller

        self.__observer = None
        self.__eventhandler = None
        self.__thread_clock = None
        self.__thread_event = Event()

        self.__paths = config.dht22_paths
        self.__file_name = self.__paths["latest.csv"]
        self.__contents = ["" for _ in range(4)]
        self.__contents[0] = "Waiting for data"

    def _update_data(self, data) -> None:

        """
        Updates given data to lcd screen

        Parameters:
            data: dict -> dictionary that has temp, and hum data stored in it
        """

        self.__contents[0] = f"Lämpötila:{data['temp']:>8}°C"
        self.__contents[1] = f"Ilmankosteus:{data['hum']:>6}%"
        self.__contents[2] = f"Mitattu klo{data['time']:>9}"
        self.__lcd_controller.update_lcd(self.__contents)

    def __update_clock(self):
        if self.__thread_event.is_set():
            return
        self.__thread_clock = Timer(1 / 2.5, self.__update_clock)
        self.__thread_clock.start()
        self.__contents[3] = f'Kellonaika: {datetime.now().time().strftime("%H.%M:%S")}'
        self.__lcd_controller.update_lcd(self.__contents)

    def start(self) -> None:
        """
        Starts the view
        """
        self.__thread_event.clear()

        self.__observer = Observer()
        self.__eventhandler = FileChangeHandler(self)
        self.__observer.schedule(self.__eventhandler, self.__file_name)
        self.__observer.start()

        self.__update_clock()

    def close(self) -> None:

        """
        Closes the view
        """
        self.__lcd_controller.wait()
        self.__thread_event.set()
        self.__thread_clock.join()
        self.__observer.stop()
        self.__lcd_controller.ready()


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

    def on_closed(self, event=None):
        data = self.__read_file()
        self.view._update_data(data)

    def __read_file(self) -> dict:
        with open(self.file_name, "r") as csv_file:
            keys = ["temp", "hum", "time", "date"]
            values = csv_file.read().split(";")
            if len(values) == 4 and isinstance(values, List):
                data = dict(zip(keys, values))
                return data
