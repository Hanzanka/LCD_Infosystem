import pathlib

conf_path = str(pathlib.Path(__file__).parent.resolve().parent.resolve()) + "/config.py"
import importlib.util

spec = importlib.util.spec_from_file_location("config", conf_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

from datetime import datetime
import adafruit_dht
from board import D12
import asyncio
from dataclasses import astuple, dataclass
from datetime import datetime
import csv


class DHT22:

    """
    Measures temperature and humidity
    """

    def __init__(self) -> None:
        self.dht = adafruit_dht.DHT22(pin=D12, use_pulseio=True)

    async def measure(self) -> tuple:

        """Measures current temperature and humidity"""

        temperature, humidity, time, date = None, None, None, None
        while True:

            try:
                temperature = self.dht.temperature
                humidity = self.dht.humidity
                time = datetime.now().time().strftime("%H.%M:%S")
                date = datetime.now().date().strftime("%d.%m.%Y")
                break

            except RuntimeError:
                print(
                    f"An error occurred while measuring temperature and humidity! {datetime.now().strftime('%H.%M:%S')}"
                )
                await asyncio.sleep(2)

        return dht22_result(temperature, humidity, time, date)


@dataclass
class dht22_result:

    """
    Class which stores dht22 measure data

    Parameters:
        temperature: str -> measuring result for temperature
        humidity: str -> measuring result for humidity
        time: str -> time of the measurement
        date: str -> date of the measurement
    """

    temperature: str
    humidity: str
    time: str
    date: str


class Logger:

    """
    Uses DHT22 class to measure temperature and humidity. Logs data to csv file given in __init__() function

    Parameters:
        update_interval: int -> Time between every measurement
        file_name: str -> Path of the file where logs will be saved
    """

    def __init__(
        self,
        update_interval=10,
        file_name=config.paths["data.csv"],
        recent_result_file=config.paths["latest.csv"],
    ) -> None:

        self.update_interval = update_interval
        self.file_name = file_name
        self.DHT = DHT22()
        self.recent_result_file = recent_result_file

    def get_last_result(self):
        return self.last_result

    async def __log(self, data: dht22_result) -> None:

        """
        Logs data to csv file

        Parameters:
            data: dht22_result -> dht22_result class containing measure data
        """

        with open(self.file_name, "a", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(astuple(data))

        with open(self.recent_result_file, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(astuple(data))

    async def __run(self):

        """
        Starts logger
        """

        while True:

            task_sleep = asyncio.create_task(asyncio.sleep(self.update_interval))
            task_measure = asyncio.create_task((self.DHT.measure()))

            data = await task_measure
            task_log = asyncio.create_task(self.__log(data))

            await task_log
            await task_sleep

    def main(self):
        """
        Starts logger

        """

        asyncio.run(self.__run())


if __name__ == "__main__":

    logger = Logger()
    logger.main()
