import logging
import os
import config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event
from display.lcd_controller import LCD_controller
from display.lcd_view import LCD_view
from internet_speedtest.networkmonitor import NetworkMonitor
from internet_speedtest.speedtestprovider import SpeedtestProvider
from multiprocessing import Pipe, Process


class Internet_speedtest_view(LCD_view):
    def __init__(self, lcd_controller: LCD_controller) -> None:

        self.__logger = logging.getLogger()
        self.__logger.setLevel(logging.INFO)

        self.__lcd_controller = lcd_controller

        self.__paths = config.speedtest_paths
        self.__contents = ["" for _ in range(4)]
        self.__index = 0

        self.__ignore_lines = ["Finding Server", "Testing Download", "Testing Upload"]

        self.__thread_event = Event()
        self.__monitor_thread = None
        self.__monitor_process = None
        self.__controller_thread = None
        self.__observer = None
        self.__eventhandler = None

        self.__commands_enabled = True
        self.__commands = {"enter": self.__test}

        self.__monitor_controlling_pipe = None
        self.__view_end = None
        self.__view_controlling_pipe = None

        self.__provider = SpeedtestProvider()

        self.name = "speedtest_view.py"

        self.__on_screen = False

    def _update_data(self, data) -> None:
        if data != "Complete":
            self.__contents[self.__index] = data

            if data not in self.__ignore_lines and self.__index != 2:
                self.__index += 1

            elif data == "Testing Upload":
                self.__monitor_controlling_pipe.send("switch")
            if self.__on_screen:
                self.__lcd_controller.update_lcd(self.__contents)
        else:
            self.__finish_test()

    def __finish_test(self) -> None:
        self.__close_threads()
        self.__logger.info("All threads and processes closed")
        self.__contents[3] = "Hit enter to re-run"
        if self.__on_screen:
            self.__lcd_controller.update_lcd(self.__contents)
        self.__commands_enabled = True

    def __close_threads(self) -> None:
        self.__logger.info("Closing processes and threads in speedtest_view")
        self.__observer.stop()
        self.__thread_event.set()
        self.__monitor_thread.join()
        self.__monitor_controlling_pipe.send("stop")
        self.__monitor_controlling_pipe.close()
        self.__view_end.close()
        self.__monitor_process.join()

    def __controller(self) -> None:
        print("Speedtest_view controller has been started")
        while True:
            try:
                command = self.__view_controlling_pipe.recv()
                print("received command:", command)
                if self.__commands_enabled and command in self.__commands:
                    self.__commands[command]()

                elif not self.__commands_enabled:
                    print("Commands are not enabled on speedtest_view.py")
            except EOFError:
                break

    def close(self) -> None:
        self.__on_screen = False
        self.__logger.info("Exiting speedtest_view")

    def start(self, pipe: Pipe) -> None:
        if self.__commands_enabled:
            self.__index = 0
        self.__on_screen = True
        self.__logger.info("Starting speedtest_view.py")
        self.__view_controlling_pipe = pipe
        self.__controller_thread = Thread(target=self.__controller)
        self.__controller_thread.start()
        if self.__commands_enabled and self.__contents[0] != "Finding Server":
            self.__contents[0] = "Hit enter to start"
        self.__lcd_controller.update_lcd(self.__contents)

    def __test(self):
        print("Starting internet speedtest")

        self.__commands_enabled = False

        self.__thread_event.clear()

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

        self.__provider.test()
        self.__finish_test()

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

        print("Bandwidth monitor is started")

        while True:
            if self.__thread_event.is_set():
                print("Closing bandwidth monitor")
                break
            data = self.__view_end.recv()
            self.__contents[self.__index + 1] = self.__convert_for_lcd(data)
            if self.__on_screen:
                self.__lcd_controller.update_lcd(self.__contents)

    def __convert_for_lcd(self, data):
        mbps = f"{data:.2f} mbps"
        return f"Speed{mbps:>15}"


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
