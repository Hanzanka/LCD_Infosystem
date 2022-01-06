import os
import config
from RPLCD.i2c import CharLCD
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event
from display.lcd_view import LCD_view
from internet_speedtest.networkmonitor import NetworkMonitor
from internet_speedtest.speedtestprovider import SpeedtestProvider
from multiprocessing import Pipe, Process


class Internet_speedtest_view(LCD_view):
    def __init__(self, lcd: CharLCD) -> None:

        self.__lcd = lcd
        lcd.backlight_enabled = True
        self.__paths = config.speedtest_paths
        self.__cursor_row = 0

        self.__ignore_lines = ["Finding Server", "Testing Download", "Testing Upload"]

        self.__print_event = Event()
        self.__thread_event = Event()

        self.__monitor_thread = None
        self.__monitor_process = None
        self.__controller_thread = None
        self.__observer = None
        self.__eventhandler = None

        self.__commands_enabled = True
        self.__commands = {"t": self.__test}

        self.__monitor_controlling_pipe = None
        self.__view_end = None

        self.name = "speedtest_view.py"

    def _update_data(self, data) -> None:
        print("Updating speedtest data on screen")
        if data != "Complete!":
            self.__wait_for_permission_to_print()
            self.__lcd.cursor_pos = (self.__cursor_row, 0)
            self.__lcd.write_string(data + (20 - len(data)) * " ")
            if data not in self.__ignore_lines and self.__cursor_row != 2:
                self.__cursor_row += 1
            elif data == "Testing Upload":
                self.__monitor_controlling_pipe.send("switch")
            self.__print_event.set()
        else:
            self.__finish_test()

    def __wait_for_permission_to_print(self) -> None:
        self.__print_event.wait()
        self.__print_event.clear()

    def __finish_test(self) -> None:
        print("Finishing test")
        self.__close_threads()

        self.__lcd.cursor_pos = (3, 0)
        self.__lcd.write_string("Finished!" + " " * 11)

    def __close_threads(self) -> None:
        print("Closing working threads")
        self.__observer.stop()
        self.__thread_event.set()
        self.__monitor_thread.join()
        self.__monitor_controlling_pipe.send("stop")
        self.__monitor_controlling_pipe.close()
        self.__view_end.close()
        self.__monitor_process.join()

    def __controller(self, pipe: Pipe) -> None:
        print("Speedtest_view controller has been started")
        while True:
            command = pipe.recv()
            print("received command:", command)
            if self.__commands_enabled and command in self.__commands:
                self.__commands[command]()

    def start(self, pipe: Pipe) -> None:
        print("Starting speedtest_view.py")
        self.__controller_thread = Thread(target=self.__controller, args=[pipe])
        self.__controller_thread.start()

    def __test(self):
        print("Starting internet speedtest")
        self.__lcd.clear()
        self.__cursor_row = 0

        self.__thread_event.clear()
        self.__print_event.set()

        file_name = self.__paths["latest.txt"]
        self.__observer = Observer()
        self.__eventhandler = FileChangeHandler(self)
        self.__observer.schedule(self.__eventhandler, file_name)
        self.__observer.start()

        self.__monitor_thread = Thread(
            target=self.__bandwidth_monitor,
            args=[],
        )
        self.__monitor_thread.start()

        provider = SpeedtestProvider()
        provider.test()

    def __bandwidth_monitor(self):
        print("Starting bandwidth monitor")
        monitor_end, self.__view_end = Pipe()
        monitor_controller_end, self.__monitor_controlling_pipe = Pipe()
        monitor = NetworkMonitor()
        self.__monitor_process = Process(
            target=monitor.start,
            daemon=True,
            args=[monitor_end, monitor_controller_end],
        )
        self.__monitor_process.start()

        while True:
            if self.__thread_event.is_set():
                print("Closing bandwidth monitor")
                break
            data = self.__view_end.recv()
            self.__wait_for_permission_to_print()
            self.__lcd.cursor_pos = (self.__cursor_row + 1, 0)
            self.__lcd.write_string(self.__convert_for_lcd(data))
            self.__print_event.set()

    def __convert_for_lcd(self, data):
        mbps = f"{data:.2f} mbps"
        return f'Speed{mbps:>15}'

class FileChangeHandler(FileSystemEventHandler):

    """
    Used to detect changes in

    Parameters:
        view: View -> View where data is sent to be updated on the display
    """

    def __init__(self, view: Internet_speedtest_view) -> None:
        super().__init__()
        self.view = view
        self.file_name = config.speedtest_paths["latest.txt"]

    def on_closed(self, event):
        data = self.__read_file()
        if data is not None:
            self.view._update_data(data)

    def __read_file(self) -> dict:
        if os.stat(self.file_name).st_size == 0:
            return None
        with open(self.file_name, "r") as file:
            data = file.readlines()[-1]
            return data.strip("\n")


if __name__ == "__main__":
    lcd = CharLCD(
        i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
    )
    lcd.backlight_enabled = False
    lcd.display_enabled = True
    lcd.clear()

    k = Internet_speedtest_view(lcd)
    k.test()
