""" TF2000 tools library
28.10.2023
Mateusz Mróz
"""

import serial
import sys
import csv
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from collections.abc import Callable
from time import sleep


class TF2000:
    connector = serial.Serial

    FILE_REPLACE, FILE_APPEND = "w", "a"
    (
        F_DECADE_10mHz,
        F_DECADE_100mHz,
        F_DECADE_1Hz,
        F_DECADE_10Hz,
        F_DECADE_100Hz,
        F_DECADE_1kHz,
        F_DECADE_10kHz,
        F_DECADE_100kHz,
    ) = (0.01, 0.1, 1, 10, 100, 1000, 10000, 100000)
    MEASUREMENTS_15, MEASUREMENTS_30, MEASUREMENTS_60, MEASUREMENTS_120 = (
        15,
        30,
        60,
        120,
    )
    AVERAGING_NORMAL, AVERAGING_LONG = "N", "L"
    GAIN_DB, GAIN_RATIO = "D", "R"

    _prefixes = {"m": "e-3", "k": "e3"}

    _csv_file_header = "Frequency,Gain,Phase,Gen Amplitude\n"

    def __init__(self, connector: serial.Serial) -> None:
        self.connector = connector

    def __find_crossover(
        self, freq_points, mag_points, phase_points
    ) -> tuple[float, float]:
        crossover_freq = np.interp(0.0, np.flipud(mag_points), np.flipud(freq_points))
        phase_margin = np.interp(crossover_freq, freq_points, phase_points)

        return (crossover_freq, phase_margin)

    def __generate_sweep_frequency_table(
        self, frequency_decade_start, frequency_decade_end, measurements_per_decade
    ) -> list[str]:
        first_decade_frequency = frequency_decade_start
        frequency_points = np.array([])
        while (first_decade_frequency * 10) <= frequency_decade_end:
            frequency_points = np.append(
                frequency_points,
                np.geomspace(
                    first_decade_frequency,
                    first_decade_frequency * 10,
                    measurements_per_decade,
                    endpoint=False,
                ),
            )
            first_decade_frequency = first_decade_frequency * 10

        frequency_points = np.append(frequency_points, first_decade_frequency)

        formatter = ticker.EngFormatter()
        return_table = list()
        for frequency in frequency_points:
            return_table.append(
                self.__round_frequency_point(formatter(frequency)).replace(" ", "")
            )
        return return_table

    def __round_frequency_point(self, text) -> str:
        match = re.match(r"(\d*\.?\d+)(?:\s*([a-zA-Z]+))?", text)
        if match:
            number, unit = match.groups()
            unit = unit if unit else ""
            # Convert to float and round to three significant digits
            rounded_number = f"{float(number):.3f}"

            # Return always 3 digits excluding dot
            counter = 0
            for index in range(len(rounded_number)):
                if rounded_number[index].isdigit():
                    counter += 1
                if 3 == counter:
                    rounded_number = rounded_number[0 : index + 1]
                    break

            return f"{rounded_number} {unit}"
        return text

    def read_to_file(
        self,
        file_path: str | None = "output/tf2000_data.csv",
        file_access: str = FILE_APPEND,
        measurements_to_read: int = MEASUREMENTS_15,
    ) -> None:
        """Reads given number of measurements to the file

        Keyword arguments:
        file_path -- output file path and name (default "output/tf2000_data.csv")
        file_access -- replace file current content or append (default FILE_APPEND)
        measurements_to_read -- number of measurements to read (default MEASUREMENTS_15)
        WARNING: if frequency range is too low for device generator resolution, it will send other number of measurements
        """

        if file_access not in [self.FILE_REPLACE, self.FILE_APPEND]:
            raise ValueError("Invalid file_access value!")

        if measurements_to_read not in [
            self.MEASUREMENTS_15,
            self.MEASUREMENTS_30,
            self.MEASUREMENTS_60,
            self.MEASUREMENTS_120,
        ]:
            raise ValueError("Invalid measurements_to_read value!")

        file = open(file_path, file_access, newline="")
        csv_writer = csv.writer(file, delimiter=",", lineterminator="\n")

        if self.FILE_REPLACE == file_access:
            file.write(self._csv_file_header)

        for _ in range(measurements_to_read):
            line = self.connector.readline().decode("utf-8")
            data = line.split("    ")
            for index in range(len(data)):
                data[index] = data[index].strip()
            print(data)
            csv_writer.writerow(data)

        file.close()

    def plot_bode_from_file(
        self,
        input_file_path: str | None = "output/tf2000_data.csv",
        output_file_path: str | None = "output/bode_plot.svg",
        title: str | None = "Bode Plot",
        line_style: str | None = ".",
        crossover_marker: bool | None = False,
    ):
        """Plots bode plot from TF2000 data file

        Keyword arguments:
        input_file_path -- input file path and name (default "output/tf2000_data.csv")
        output_file_path -- output plot file path and name (default "output/bode_plot.svg")
        title -- plot title (default "Bode Plot")
        line_style -- magnitude and phase plots matplotlib line style (default ".")
        crossover_marker -- set to True to plot crossover info on the plot (default False)
        """

        try:
            file = open(input_file_path, "r")
        except OSError:
            print("Could not open/read file:", input_file_path)
            sys.exit()

        freq_points = []
        mag_points = []
        phase_points = []
        gen_amplitude_points = []

        for line in file:
            line = (
                line.replace("Hz", "")
                .replace("dB", "")
                .replace("deg", "")
                .replace("V", "")
            )

            words = line.rstrip().split(",")
            # Legacy support
            if len(words) < 3:
                words = line.rstrip().split()

            for prefix in self._prefixes:
                words[0] = words[0].replace(prefix, self._prefixes[prefix])

            try:
                freq_points.append(float(words[0]))
                mag_points.append(float(words[1]))
                phase_points.append(float(words[2]))
                gen_amplitude_points.append(float(words[3]))
            except:
                # This is header or invalid data line
                None

        file.close()

        fig, (ax_gain, ax_phase) = plt.subplots(2, figsize=(10.5, 7.5))

        fig.suptitle(title, fontsize=23)

        ax_gain.grid(which="major", color="#D9EAD3")
        ax_gain.grid(which="minor", color="#D9EAD3", linestyle=":")
        ax_gain.plot(freq_points, mag_points, line_style, markersize=6)
        ax_gain.set_xlabel("Frequency", fontweight="bold")
        ax_gain.set_ylabel("Magnitude", fontweight="bold")
        ax_gain.set_xscale("log")
        ax_gain.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
        ax_gain.yaxis.set_major_formatter(ticker.EngFormatter(unit="dB"))

        ax_phase.grid(which="major", color="#D9EAD3")
        ax_phase.grid(which="minor", color="#D9EAD3", linestyle=":")
        (phase_line,) = ax_phase.plot(
            freq_points, phase_points, line_style, markersize=6
        )
        ax_phase.set_xlabel("Frequency", fontweight="bold")
        ax_phase.set_ylabel("Phase", fontweight="bold")
        ax_phase.set_xscale("log")
        ax_phase.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
        ax_phase.yaxis.set_major_formatter(ticker.EngFormatter(unit="°"))

        if crossover_marker is True:
            formatter = ticker.EngFormatter(unit="Hz", places=2)
            crossover_freq, crossover_phase = self.__find_crossover(
                freq_points, mag_points, phase_points
            )

            ax_gain.axvline(
                x=crossover_freq, linestyle="--", color="#DC143C", linewidth=1
            )
            ax_phase.axvline(
                x=crossover_freq, linestyle="--", color="#DC143C", linewidth=1
            )
            ax_phase.axhline(
                y=crossover_phase, linestyle="--", color="#DC143C", linewidth=1
            )

            textstr = "\n".join(
                (
                    ("Crossover frequency: " + formatter(crossover_freq)),
                    f"Crossover phase:       {crossover_phase:.2f} °",
                )
            )
            crossover_info = ax_phase.legend(
                [phase_line],
                [textstr],
                loc="upper right",
                prop={"size": 10},
                handlelength=0,
                handletextpad=0,
                fancybox=True,
            )
            for item in crossover_info.legendHandles:
                item.set_visible(False)
            ax_phase.add_artist(crossover_info)

        if output_file_path is not None:
            plt.savefig(output_file_path)

        plt.tight_layout()
        plt.show()

    def plot_bode_from_multiple_files(
        self,
        input_file_paths: list[str]
        | None = [
            "output/tf2000_data.csv",
        ],
        legend_names: list[str]
        | None = [
            "1",
        ],
        output_file_path: str | None = "output/bode_plot.svg",
        title: str | None = "Bode Plot",
        line_style: str | None = ".-",
    ):
        """Plots multiple bode plots from TF2000 data files

        Keyword arguments:
        input_file_paths -- list of input file paths and names (default ["output/tf2000_data.csv",])
        legend_names -- list of legend names of consecutive files to be plotted (default ["1",])
        output_file_path -- output plot file path and name (default "output/bode_plot.csv")
        title -- plot title (default "Bode Plot")
        line_style -- magnitude and phase plots matplotlib line style (default ".")
        """

        fig, (ax_gain, ax_phase) = plt.subplots(2, figsize=(10.5, 7.5))

        fig.suptitle(title, fontsize=23)

        ax_gain.grid(which="major", color="#D9EAD3")
        ax_gain.grid(which="minor", color="#D9EAD3", linestyle=":")
        ax_gain.set_xlabel("Frequency", fontweight="bold")
        ax_gain.set_ylabel("Magnitude", fontweight="bold")
        ax_gain.set_xscale("log")
        ax_gain.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
        ax_gain.yaxis.set_major_formatter(ticker.EngFormatter(unit="dB"))

        ax_phase.grid(which="major", color="#D9EAD3")
        ax_phase.grid(which="minor", color="#D9EAD3", linestyle=":")
        ax_phase.set_xlabel("Frequency", fontweight="bold")
        ax_phase.set_ylabel("Phase", fontweight="bold")
        ax_phase.set_xscale("log")
        ax_phase.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
        ax_phase.yaxis.set_major_formatter(ticker.EngFormatter(unit="°"))

        for path in input_file_paths:
            try:
                file = open(path, "r")
            except OSError:
                print("Could not open/read file:", path)
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

            file.close()

            ax_gain.plot(freq_points, mag_points, line_style, markersize=6)
            ax_phase.plot(freq_points, phase_points, line_style, markersize=6)

        ax_gain.legend(legend_names)
        ax_phase.legend(legend_names)

        if output_file_path is not None:
            plt.savefig(output_file_path)

        plt.tight_layout()
        plt.show()

    def perform_gain_phase_analysis(
        self,
        file_path: str | None = "output/tf2000_data.csv",
        file_access: str = FILE_APPEND,
        frequency_decade_start: int = F_DECADE_10Hz,
        frequency_decade_end: int = F_DECADE_100kHz,
        measurements_per_decade: int = MEASUREMENTS_30,
        averaging: str = AVERAGING_NORMAL,
        measurement_cycles: int = 50,
        generator_delay: int = 0,
        generator_pre_bias: bool = True,
        gain_results: str = GAIN_DB,
        generator_amplitude: int | Callable[[int], int] = 20,
        generator_bias: int = 0,
    ):
        """Performs gain phase analysis

        Keyword arguments:
        file_path -- output file path and name (default "output/tf2000_data.csv")
        file_access -- replace file current content or append (default FILE_APPEND)
        frequency_decade_start -- the decade of the frequency at which the sweep starts (default F_DECADE_10Hz)
        frequency_decade_end -- the decade of the frequency at which the sweep ends (default F_DECADE_100kHz)
        measurements_per_decade -- number of measurements per decade (default MEASUREMENTS_30)
        averaging -- averaging option (default AVERAGING_NORMAL):
            NORMAL - averaging until deviation in average value is less than 1%, with upper limit of 50 cycles,
            LONG - averaging until deviation in average value is less than 0.2%, with upper limit of 250 cycles
        measurement_cycles -- maximum number of measurement cycles used for averaging (default 50) TODO test range, to 255?
        generator_delay -- delay between generator turning on and beginning of analysis in range 0 - 999 seconds
            (default 0)
        generator_pre_bias -- when using AC coupling, input 100nF capacitor needs to pre-biased otherwise first few
            measurements may be with error. When True, dummy 3s conversion will be performed (default True)
        gain_results -- gain result format as dB or as a ratio (default GAIN_DB)
        generator_amplitude -- generator amplitude in mV (0 - 5000) in 20mV steps (default 20).
            A callback function can be also provided, which takes a frequency in Hz as an argument and returns
            generator amplitude value, output values will be rounded.
        generator_bias -- generator bias in mV (-5000 - 5000) in 40mV steps (default 0)
        """

        if file_access not in [self.FILE_REPLACE, self.FILE_APPEND]:
            raise ValueError("Invalid file_access value!")

        if frequency_decade_start and frequency_decade_end not in [
            self.F_DECADE_10mHz,
            self.F_DECADE_100mHz,
            self.F_DECADE_1Hz,
            self.F_DECADE_10Hz,
            self.F_DECADE_100Hz,
            self.F_DECADE_1kHz,
            self.F_DECADE_10kHz,
            self.F_DECADE_100kHz,
        ]:
            raise ValueError("Invalid frequency decade value!")

        if frequency_decade_start >= frequency_decade_end:
            raise ValueError("Invalid frequency decade range!")

        if measurements_per_decade not in [
            self.MEASUREMENTS_15,
            self.MEASUREMENTS_30,
            self.MEASUREMENTS_60,
            self.MEASUREMENTS_120,
        ]:
            raise ValueError("Invalid measurements_per_decade value!")

        if averaging not in [self.AVERAGING_NORMAL, self.AVERAGING_LONG]:
            raise ValueError("Invalid averaging value!")

        if measurement_cycles not in range(1, 255):
            raise ValueError("Invalid measurement_cycles value!")

        if generator_delay not in range(0, 999):
            raise ValueError("Invalid generator_delay value!")

        if not isinstance(generator_pre_bias, bool):
            raise ValueError("Invalid generator_pre_bias value!")

        if gain_results not in [self.GAIN_DB, self.GAIN_RATIO]:
            raise ValueError("Invalid gain_results value!")

        if isinstance(generator_amplitude, int) and generator_amplitude not in range(
            0, 5000, 20
        ):
            raise ValueError("Invalid gain_results value!")

        if isinstance(generator_bias, int) and generator_bias not in range(
            -5000, 5000, 40
        ):
            raise ValueError("Invalid generator_bias value!")

        file = open(file_path, file_access, newline="")
        csv_writer = csv.writer(file, delimiter=",", lineterminator="\n")

        if self.FILE_REPLACE == file_access:
            file.write(self._csv_file_header)

        frequency_points = self.__generate_sweep_frequency_table(
            frequency_decade_start, frequency_decade_end, measurements_per_decade
        )
        amplitude_points = list()

        if callable(generator_amplitude):
            for frequency in frequency_points:
                frequency = frequency.replace("Hz", "").replace(" ", "")
                for prefix in self._prefixes:
                    frequency = frequency.replace(prefix, self._prefixes[prefix])
                amplitude_points.append(
                    20 * round(generator_amplitude(float(frequency)) / 20)
                )
                if amplitude_points[-1] < 20:
                    amplitude_points[-1] = 20
                if amplitude_points[-1] > 5000:
                    amplitude_points[-1] = 5000

        if generator_pre_bias is True:
            self.connector.write("D N G20 F100k A1 P S W4 T \n\r".encode())
            line = self.connector.readline().decode("utf-8")

        for index in range(len(frequency_points)):
            request = f"{gain_results} {averaging} G{amplitude_points[index]} F{frequency_points[index]} A{measurement_cycles} P S W{generator_delay} T \n\r"
            print(request)
            sleep(0.005)
            self.connector.write(request.encode())

            line = self.connector.readline().decode("utf-8")
            print(line)
            line = line[1:]
            data = line.split("    ")
            for index in range(len(data)):
                data[index] = data[index].strip()
            data.append(amplitude_points[index])
            csv_writer.writerow(data)
