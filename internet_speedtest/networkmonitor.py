from enum import Enum
import logging
from time import sleep
import asyncio
from threading import Thread


class BandwidthMonitor:
    def __init__(self, iface="eth0") -> None:

        self.__update_interval = 2
        self.__rounding = 2
        self.__iface = iface
        self.__direction = {
            BandwidthMonitorState.DOWNLOAD: "rx",
            BandwidthMonitorState.UPLOAD: "tx",
        }

        self.__event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__event_loop)
        self.__wait_event = asyncio.Event()
        
        self.__state = BandwidthMonitorState.OFF
        
        self.__monitor_thread = None

        self.__logger = logging.getLogger()
        self.__logger.setLevel(logging.INFO)

        self.__call_on_update = None

    def __monitor_bandwidth(self) -> None:
        self.__call_on_update(self.__transfer_rate())
        asyncio.get_event_loop().call_soon(self.__monitor_bandwidth)

    def __get_bytes(self, direction: str):
        with open(
            f"/sys/class/net/{self.__iface}/statistics/{direction}_bytes", "r"
        ) as file:
            data = file.read()
            return int(data)

    def __transfer_rate(self) -> list:
        if self.__state == BandwidthMonitorState.READY or self.__state == BandwidthMonitorState.OFF:
            return []
        direction = self.__direction[self.__state]
        results = []
        for _ in range(5):
            result_1 = self.__get_bytes(direction)
            sleep(1 / self.__update_interval / 5)
            result_2 = self.__get_bytes(direction)
            results.append((result_2 - result_1) * 5 * self.__update_interval)
        return self.__convert_to_megabits(
            round(sum(results) / len(results), self.__rounding)
        )

    async def __wait_until_ready(self) -> None:
        await self.__wait_event.wait()

    def __convert_to_megabits(self, result_in_B) -> float:
        bits = 8 * result_in_B
        megabits = bits / (1024 ** 2)
        return megabits

    def __start_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.__wait_event = asyncio.Event()
        loop.call_soon(self.__monitor_bandwidth)
        loop.run_until_complete(self.__wait_until_ready())

    def start(self, function: callable):
        self.__call_on_update = function
        self.__monitor_thread = Thread(target=self.__start_loop)
        self.__monitor_thread.start()

    def reset(self) -> None:
        self.__state == BandwidthMonitorState.OFF

    def set_state(self, state) -> None:
        self.__state = state
        if state == BandwidthMonitorState.READY:
            self.__wait_event.set()

            self.__monitor_thread.join(timeout=10)

            if not self.__monitor_thread.is_alive():
                self.__logger.info("Monitor thread is closed")
            else:
                self.__logger.info("Monitor thread is still alive")


class BandwidthMonitorState(Enum):
    OFF = "off"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    READY = "ready"
