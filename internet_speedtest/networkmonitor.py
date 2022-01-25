from time import sleep
from multiprocessing import Pipe
from threading import Thread


class NetworkMonitor:
    def __init__(
        self, update_interval=2, rounding=2, iface="eth0", direction="rx"
    ) -> None:
        self.__update_interval = update_interval
        self.__rounding = rounding
        
        self.__direction = direction
        self.__direction_dict = {"rx": "tx", "tx": "rx"}
        self.__iface = iface
        
        self.__commands = {"switch": self.__switch_direction}
        
        self.__monitor_pipe = None
        self.__controller_pipe = None

        self.__monitor_thread = None
        self.__controller_thread = None

        self.name = 'networkmonitor.py'

    def __monitor_bandwidth(self) -> None:
        while True:
            speed = self.__transfer_rate()
            try:
                self.__monitor_pipe.send(speed)
            except OSError:
                print(f'Closing bandwidth monitor on {self.name}')
                break
            except BrokenPipeError:
                print(f'Closing bandwidth monitor on {self.name}')
                break

    def __get_bytes(self, direction: str):
        with open(
            f"/sys/class/net/{self.__iface}/statistics/{direction}_bytes", "r"
        ) as file:
            data = file.read()
            return int(data)

    def __transfer_rate(self) -> tuple:
        results = []
        for _ in range(5):
            direction = self.__direction
            result_1 = self.__get_bytes(direction)
            sleep(1 / self.__update_interval / 5)
            result_2 = self.__get_bytes(direction)
            results.append(
                self.__convert_to_megabits(result_1, result_2)
                * 5
                * self.__update_interval
            )
        return round(sum(results) / len(results), self.__rounding)

    def __convert_to_megabits(self, result_1, result_2) -> float:
        bits = 8 * (result_2 - result_1)
        megabits = bits / (1024 ** 2)
        return megabits

    def start(self, monitor_pipe: Pipe, controller_pipe: Pipe):
        
        self.__controller_pipe = controller_pipe
        self.__monitor_pipe = monitor_pipe

        self.__monitor_thread = Thread(target=self.__monitor_bandwidth, args=[])
        self.__controller_thread = Thread(target=self.__controller, args=[])

        self.__monitor_thread.start()
        self.__controller_thread.start()

    def __switch_direction(self):
        self.__direction = self.__direction_dict[self.__direction]

    def __controller(self) -> None:
        while True:
            command = self.__controller_pipe.recv()
            if command != "stop" and command in self.__commands:
                self.__commands[command]()
            elif command == "stop":
                print(f"Closing controller on {self.name}")
                self.__monitor_pipe.close()
                self.__controller_pipe.close()
                break
        
        self.__monitor_thread.join()
        
        if not self.__monitor_thread.is_alive():
            print(f'Bandwidth monitor on {self.name} is closed')
        else:
            print(f'Bandwidth monitor on {self.name} is still alive')
            
        print(f'Controller on {self.name} is closed')
