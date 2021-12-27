from time import sleep
import sys
from multiprocessing import Queue


class NetworkMonitor:
    def __init__(self, update_rate=5, rounding=2) -> None:
        self.update_rate = update_rate
        self.rounding = rounding

    def monitor_download_rate(self, queue: Queue) -> None:
        while True:
            speed = self.__transfer_rate(2)
            print(speed)
            if queue is not None:
                while True:
                    if queue.empty() is not True:
                        data = queue.get()
                        data["monitor"]['speed'] = f"Speed: {f'{speed} MBit/s':>12}"                      
                        queue.put(data)
                        break
                    else:
                        sleep(1 / 1000000)
            else:
                print(f"Download speed: {speed} MBit/s")
                self.__clear_line(1)

    def __get_bytes(self, direction: str, iface="eth0"):
        with open(f"/sys/class/net/{iface}/statistics/{direction}_bytes", "r") as file:
            data = file.read()
            file.close()
            return int(data)

    def __transfer_rate(self, update_interval: int = 2, rounding: int = 2) -> tuple:
        results = []
        for _ in range(5):
            result_1 = self.__get_bytes("rx")
            sleep(1 / update_interval / 5)
            result_2 = self.__get_bytes("rx")
            results.append((result_2 - result_1) * 7.6294 * (10 ** (-6)) * 5)
        return f"{round(sum(results) / len(results) * update_interval, rounding):.2f}"

    def __clear_line(self, lines=1) -> None:
        CURSOR_UP_ONE = "\x1b[1A"
        ERASE_LINE = "\x1b[2K"
        for _ in range(lines):
            sys.stdout.write(CURSOR_UP_ONE)
            sys.stdout.write(ERASE_LINE)

    def main(self, queue: Queue = None):
        self.monitor_download_rate(queue)


if __name__ == "__main__":
    monitor = NetworkMonitor()
    monitor.monitor_download_rate(None)
