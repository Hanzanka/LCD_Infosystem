from os import pipe
from time import sleep
from .lcd_controller import LCD
from .lcd_view import LCD_view
from .dht22_sensor_view import Dht22_view
from multiprocessing import Pipe
from threading import Thread
from datetime import datetime
from RPLCD.i2c import CharLCD


class Menuitem:
    def __init__(self, title: str, target: LCD_view) -> None:
        self.title = title
        self.target = target

    def start(self) -> None:
        self.target.start()

    def close(self) -> None:
        self.target.close()


class Menu:
    def __init__(self, lcd, pipe: Pipe) -> None:
        self.__lcd = lcd
        self.__items = []
        self.__items.append(Menuitem("DHT22 view", Dht22_view(self.__lcd)))
        self.__selected = self.__items[0]
        self.__pipe = pipe
        self.__controls = {
            "enter": self.__start_view,
            "backspace": self.__return_to_menu,
        }
        self.__in_menu = True
        self.__opened_view = None
        self.__last_command = None

    def start(self) -> None:
        self.__load__menu()

        controller_thread = Thread(target=self.__controller)
        controller_thread.start()

    def __load__menu(self) -> None:
        self.__lcd.clear()
        for item in self.__items[:4]:
            self.__lcd.write_string(item.title)
            self.__lcd.crlf()

    def __start_view(self) -> None:
        if self.__in_menu:
            print("Starting view...")
            self.__selected.start()
            self.__in_menu = False

    def __return_to_menu(self) -> None:
        if not self.__in_menu:
            print("Returning to menu")
            self.__lcd.display_enabled = False
            self.__selected.close()
            sleep(1 / 10)
            self.__lcd.display_enabled = True
            self.__load__menu()
            self.__in_menu = True

    def __controller(self) -> None:
        while True:
            command = self.__pipe.recv()

            time = datetime.now()
            if self.__last_command is None:
                time_difference = 2
            else:
                time_difference = (time - self.__last_command).total_seconds()

            if command in self.__controls and time_difference >= 2:
                self.__controls[command]()
                self.__last_command = time
            elif time_difference < 2:
                print("Can't receive commands right now")
