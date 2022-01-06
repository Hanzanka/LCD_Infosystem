from time import sleep
import config
import csv
from speedtest import Speedtest


class SpeedtestProvider:
    def __init__(self, round_results: int = 2) -> None:
        self.__tester = Speedtest()
        self.__rounding = round_results
        self.__paths = config.speedtest_paths

    def __download_test(self) -> float:
        return round(self.__tester.download() / 10 ** 6, self.__rounding)

    def __upload_test(self) -> float:
        return round(
            self.__tester.upload(pre_allocate=False) / 10 ** 6, self.__rounding
        )

    def __get_server(self) -> dict:
        data = self.__tester.get_best_server()
        url = data["url"]
        location = data["name"] + ", " + data["country"]
        ping = int(data["latency"])

        return {"url": url, "location": location, "ping": ping}

    def test(self):
        open(self.__paths["latest.txt"], "w").close()

        results = []

        print("Finding server...")
        open(self.__paths["latest.txt"], "a").write("Finding Server\n")
        server_data = self.__get_server()
        results.append(server_data["ping"])
        open(self.__paths["latest.txt"], "a").write(
            f'Ping{str(server_data["ping"]):>13} ms\n'
        )
        print(
            f"Server found at {server_data['location']}\nURL: {server_data['url']}\nPing: {server_data['ping']} ms\nPerforming download speed test..."
        )

        sleep(1 / 100)

        open(self.__paths["latest.txt"], "a").write("Testing Download\n")
        download_result = self.__download_test()
        results.append(download_result)
        open(self.__paths["latest.txt"], "a").write(
            f"Down{str(download_result):>11} Mbps\n"
        )
        print(
            f"Download speed: {download_result} MBit/s\nPerforming upload speed test..."
        )

        sleep(1 / 100)

        open(self.__paths["latest.txt"], "a").write("Testing Upload\n")
        upload_result = self.__upload_test()
        results.append(upload_result)
        open(self.__paths["latest.txt"], "a").write(
            f"Up{str(upload_result):>13} Mbps\n"
        )
        print(f"Upload speed: {upload_result} Mb/s")

        self.__log_results(results)

        sleep(1 / 100)

        open(self.__paths["latest.txt"], "a").write("Complete!")

    def __log_results(self, results: list):

        with open(self.__paths["data.csv"], "a", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(results)


if __name__ == "__main__":
    tester = SpeedtestProvider(2)
    tester.test()
