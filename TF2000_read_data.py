""" Reads data from TF2000 serial port and stores them in the file with example
28.10.2023
Mateusz Mróz
"""

import serial
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


class TF2000:
    connector = serial.Serial

    FILE_REPLACE, FILE_APPEND = "w", "a"
    LINES_15, LINES_30, LINES_60, LINES_120 = 15, 30, 60, 120
    AVERAGING_NORMAL, AVERAGING_LONG = "N", "L"
    GAIN_DB, GAIN_RATIO = "D", "R"

    _prefixes = {"m": "e-3", "k": "e3"}

    def __init__(self, connector: serial.Serial) -> None:
        self.connector = connector

    def read_to_file(
        self,
        file_path: str | None = "tf2000_data.csv",
        file_access: str = FILE_APPEND,
        lines_to_read: int = LINES_15,
    ) -> None:
        """Reads given number of lines to the file

        Keyword arguments:
        file_path -- output file path and name (default "tf2000_data.csv")
        file_access -- replace file current content or append (default FILE_APPEND)
        lines_to_read -- number of lines to read (default LINES_15)
        WARNING: if frequency range is too low for device generator resolution, it will send other number of lines
        """

        if file_access not in [self.FILE_REPLACE, self.FILE_APPEND]:
            raise ValueError("Invalid file_access value!")

        if lines_to_read not in [
            self.LINES_15,
            self.LINES_30,
            self.LINES_60,
            self.LINES_120,
        ]:
            raise ValueError("Invalid lines_to_read value!")

        file = open(file_path, file_access, newline="")

        for _ in range(lines_to_read):
            line = self.connector.readline().decode("utf-8")
            print(line)
            file.write(line)

        file.close()

    def plot_bode_from_file(
        self,
        input_file_path: str | None = "tf2000_data.csv",
        output_file_path: str | None = "bode_plot.svg",
    ):
        """Plots bode plot from TF2000 data file

        Keyword arguments:
        input_file_path -- input file path and name (default "tf2000_data.csv")
        output_file_path -- output plot file path and name (default "bode_plot.csv")
        """

        try:
            file = open(input_file_path, "r")
        except OSError:
            print("Could not open/read file:", input_file_path)
            sys.exit()

        freq_points = []
        mag_points = []
        phase_points = []

        for line in file:
            line = line.replace("Hz", "").replace("dB", "").replace("deg", "")

            words = line.rstrip().split()

            for prefix in self._prefixes:
                words[0] = words[0].replace(prefix, self._prefixes[prefix])

            freq_points.append(float(words[0]))
            mag_points.append(float(words[1]))
            phase_points.append(float(words[2]))

        plt.rcParams["figure.figsize"] = [10.5, 7.5]

        plt.figure(1)
        plt.suptitle("Bode Plot", fontsize=23)
        plt.subplot(2, 1, 1)
        plt.grid(which="both", color="#D9EAD3")
        plt.plot(freq_points, mag_points, ".", markersize=4)
        plt.xlabel("Frequency [Hz]", fontweight="bold")
        plt.ylabel("Magnitude [dB]", fontweight="bold")
        plt.xscale("log")
        plt.gca().xaxis.set_major_formatter(ticker.EngFormatter(unit=""))

        plt.subplot(2, 1, 2)
        plt.grid(which="both", color="#D9EAD3")
        plt.plot(freq_points, phase_points, ".", markersize=4)
        plt.xlabel("Frequency [Hz]", fontweight="bold")
        plt.ylabel("Phase [deg]", fontweight="bold")
        plt.xscale("log")
        plt.gca().xaxis.set_major_formatter(ticker.EngFormatter(unit=""))

        if output_file_path is not None:
            plt.savefig(output_file_path)

        plt.tight_layout()
        plt.show()

    def __set_gain_phase_analysys(
        self,
        averaging: str = AVERAGING_NORMAL,
        averaging_cycles: int = 50,
        gain_results: str = GAIN_DB,
    ):
        """Plots bode plot from TF2000 data file
        WORK IN PROGRESS - user manual v3.1 seems to lack serial commands documentation

        Keyword arguments:
        input_file_path -- input file path and name (default "tf2000_data.csv")
        output_file_path -- output plot file path and name (default "bode_plot.csv")
        """

        self.connector.write("F1k G500 VB P S W1 T \n\r".encode())


def main():
    tf2000 = TF2000(
        serial.Serial(
            port="COM4",
            baudrate=1200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            rtscts=True,
        )
    )

    tf2000.read_to_file(lines_to_read=TF2000.LINES_120)
    tf2000.plot_bode_from_file()


if __name__ == "__main__":
    main()
