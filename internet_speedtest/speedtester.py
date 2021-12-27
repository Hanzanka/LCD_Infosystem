from multiprocessing import Queue
from speedtest import Speedtest
import time
import sys
from time import sleep
import asyncio

class SpeedtestProvider:
    def __init__(self, round_results: int = 2) -> None:
        self.tester = Speedtest()
        self.results = []
        self.rounding = round_results

    async def __download_test(self) -> float:
        return round(self.tester.download() / 10 ** 6, self.rounding)

    async def __upload_test(self) -> float:
        return round(self.tester.upload(pre_allocate=False) / 10 ** 6, self.rounding)

    async def __get_server(self) -> dict:
        data = self.tester.get_best_server()
        url = data["url"]
        location = data["name"] + ", " + data["country"]
        ping = int(data["latency"])

        return {"url": url, "location": location, "ping": ping}

    def get_data(self) -> list:
        return self.last_ten_results

    async def test(self, queue: Queue = None):
        print("Finding server...")
        task_server_data = asyncio.create_task(self.__get_server())
        server_data = await task_server_data
        if queue is not None:
            while True:
                if queue.empty() is False:
                    data = queue.get()
                    data["results"]["ping"] = server_data["ping"]
                    data["monitor"]["pos"] = (0, 1)
                    queue.put(data)
                    break
                else:
                    print('queue is empty')
                    sleep(1 / 1000000)

        print(
            f"Server found at {server_data['location']}\nURL: {server_data['url']}\nPing: {server_data['ping']} ms\nPerforming download speed test..."
        )

        task_download_result = asyncio.create_task(self.__download_test())
        download_result = await task_download_result
        if queue is not None:
            while True:
                if queue.empty() is False:
                    data = queue.get()
                    data["results"]["download_speed"] = f"DL: {download_result} MBit/s"
                    data["monitor"]["pos"] = (0, 2)
                    queue.put(data)
                    break
                else:
                    sleep(1 / 1000000)

        print(
            f"Download speed: {download_result} MBit/s\nPerforming upload speed test..."
        )

        task_upload_result = asyncio.create_task(self.__upload_test())
        upload_result = await task_upload_result
        if queue is not None:
            while True:
                if queue.empty() is False:
                    data = queue.get()
                    data["results"]["upload_speed"] = f"UP: {upload_result} MBit/s"
                    data["monitor"]["pos"] = (0, 3)
                    queue.put(data)
                    break
                else:
                    sleep(1 / 1000000)

        print(f"Upload speed: {upload_result} Mb/s")

    def main(self, queue: Queue):
        asyncio.run(self.test(queue))


if __name__ == "__main__":
    tester = SpeedtestProvider(2)
    tester.test()
