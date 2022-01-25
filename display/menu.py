import logging
from .lcd_view import LCD_view
from .lcd_controller import LCD_controller
from .dht22_sensor_view import Dht22_view
from .speedtest_view import Internet_speedtest_view
from multiprocessing import Pipe
from threading import Thread


class MenuItem:
    def __init__(
        self, title: str, target: LCD_view, require_pipe: bool = False
    ) -> None:
        if len(title) > 18:
            raise ValueError("Given title is too long (max length is 18)")
        self.title = title
        self.require_pipe = require_pipe
        self.__target = target

    def start(self, pipe: None) -> None:
        if pipe is None:
            self.__target.start()
            return
        self.__target.start(pipe)

    def close(self):
        self.__target.close()

    def select(self) -> None:
        self.title = "> " + self.title

    def unselect(self) -> None:
        self.title = self.title.replace("> ", "")


class Menu:
    def __init__(self, control_pipe) -> None:

        self.__lcd_controller = LCD_controller()

        self.__items = []
        self.__create_items()
        self.__selected_id = 0
        self.__select()

        self.__first_endpoint = 0
        self.__last_endpoint = 4

        self.__control_pipe = control_pipe
        self.__controls = {
            "up": self.__up,
            "down": self.__down,
            "enter": {False: self.__start_view, True: self.__wake_screen},
            "backspace": self.__close_view,
            "esc": self.__screen_saver,
        }
        self.__menu_only_commands = ["backspace", "esc"]

        self.__in_menu = True
        self.__opened_item = None
        self.__pass_through_pipe = None

    def start(self):
        self.__update_menu()
        controller_thread = Thread(target=self.__controller)
        controller_thread.start()

    def __controller(self) -> None:
        while True:
            command = self.__control_pipe.recv()

            if command in self.__controls and (
                (self.__in_menu is True)
                or (self.__in_menu is False and command in self.__menu_only_commands)
            ):
                
                if command == "enter":
                    self.__controls[command][
                        self.__lcd_controller.screen_saver_enabled
                    ]()
                    continue
                logging.info(f'Controller received command {command}')
                self.__controls[command]()

            elif self.__in_menu is False and self.__pass_through_pipe is not None and not self.__lcd_controller.screen_saver_enabled:
                self.__pass_through_pipe.send(command)
            
            elif self.__lcd_controller.screen_saver_enabled:
                self.__lcd_controller.disable_screen_saver()

    def __get_displayed_items(self) -> list:
        return [item.title for item in self.__items[self.__first_endpoint: self.__last_endpoint]]

    def __update_menu(self) -> None:
        self.__lcd_controller.update_lcd(self.__get_displayed_items())

    def __update_endpoints(self, way: str) -> None:

        if way == "up":
            if self.__selected_id < self.__first_endpoint and self.__selected_id != -1:
                self.__first_endpoint -= 1
                self.__last_endpoint -= 1

            elif self.__selected_id == -1:
                self.__selected_id = len(self.__items) - 1
                self.__select()
                self.__first_endpoint = self.__selected_id - 3
                self.__last_endpoint = self.__selected_id + 1

            return

        if self.__selected_id > self.__last_endpoint - 1 and self.__selected_id != len(
            self.__items
        ):
            self.__first_endpoint += 1
            self.__last_endpoint += 1

        elif self.__selected_id == len(self.__items):
            self.__selected_id = 0
            self.__select()
            self.__first_endpoint = 0
            self.__last_endpoint = 4

    def __up(self) -> None:
        self.__update_items(-1)
        print(self.__selected_id)
        self.__update_endpoints("up")
        self.__update_menu()

    def __down(self) -> None:
        self.__update_items(1)
        print(self.__selected_id)
        self.__update_endpoints("down")
        self.__update_menu()

    def __update_items(self, plus: int) -> None:
        self.__unselect(self.__selected_id)
        self.__selected_id += plus
        self.__select()

    def __unselect(self, last_id) -> None:
        self.__items[last_id].unselect()

    def __select(self) -> None:
        if self.__selected_id in range(0, len(self.__items)):
            self.__items[self.__selected_id].select()

    def __create_items(self) -> None:
        dht22_item = MenuItem("DHT22 monitor", Dht22_view(self.__lcd_controller), False)
        self.__items.append(dht22_item)

        speedtest_item = MenuItem(
            "Internet speedtest", Internet_speedtest_view(self.__lcd_controller), True
        )
        self.__items.append(speedtest_item)

    def __close_view(self) -> None:
        self.__opened_item.close()
        self.__opened_item = None
        self.__update_menu()
        if self.__pass_through_pipe is not None:
            self.__pass_through_pipe.close()
            self.__pass_through_pipe = None
        self.__in_menu = True

    def __start_view(self):
        selected_item = self.__items[self.__selected_id]
        if selected_item.require_pipe:
            self.__pass_through_pipe, item__control_pipe = Pipe()
        else:
            item__control_pipe, self.__pass_through_pipe = None, None
        self.__opened_item = selected_item
        self.__in_menu = False
        selected_item.start(item__control_pipe)

    def __screen_saver(self) -> None:
        self.__lcd_controller.enable_screen_saver()

    def __wake_screen(self) -> None:
        self.__lcd_controller.disable_screen_saver()
