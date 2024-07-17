""" TF2000 tools library
28.10.2023
Mateusz Mróz
"""

import serial
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


class TF2000:
    connector = serial.Serial

    FILE_REPLACE, FILE_APPEND = "w", "a"
    LINES_15, LINES_30, LINES_60, LINES_120 = 15, 30, 60, 120
    AVERAGING_NORMAL, AVERAGING_LONG = "N", "L"
    GAIN_DB, GAIN_RATIO = "D", "R"

    _prefixes = {"m": "e-3", "k": "e3"}

    def __init__(self, connector: serial.Serial) -> None:
        self.connector = connector

    def __find_crossover(self, freq_points, mag_points, phase_points) -> tuple[float, float]:
        crossover_freq = np.interp(0.0, np.flipud(mag_points), np.flipud(freq_points))
        phase_margin = np.interp(crossover_freq, freq_points, phase_points)

        return (crossover_freq, phase_margin)

    def read_to_file(
        self,
        file_path: str | None = "output/tf2000_data.csv",
        file_access: str = FILE_APPEND,
        lines_to_read: int = LINES_15,
    ) -> None:
        """Reads given number of lines to the file

        Keyword arguments:
        file_path -- output file path and name (default "output/tf2000_data.csv")
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
        input_file_path: str | None = "output/tf2000_data.csv",
        output_file_path: str | None = "output/bode_plot.svg",
        title: str | None = "Bode Plot",
        line_style: str | None = ".",
        crossover_marker: bool | None = False,
    ):
        """Plots bode plot from TF2000 data file

        Keyword arguments:
        input_file_path -- input file path and name (default "output/tf2000_data.csv")
        output_file_path -- output plot file path and name (default "output/bode_plot.csv")
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

        for line in file:
            line = line.replace("Hz", "").replace("dB", "").replace("deg", "")

            words = line.rstrip().split()

            for prefix in self._prefixes:
                words[0] = words[0].replace(prefix, self._prefixes[prefix])

            freq_points.append(float(words[0]))
            mag_points.append(float(words[1]))
            phase_points.append(float(words[2]))

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
        (phase_line,) = ax_phase.plot(freq_points, phase_points, line_style, markersize=6)
        ax_phase.set_xlabel("Frequency", fontweight="bold")
        ax_phase.set_ylabel("Phase", fontweight="bold")
        ax_phase.set_xscale("log")
        ax_phase.xaxis.set_major_formatter(ticker.EngFormatter(unit="Hz"))
        ax_phase.yaxis.set_major_formatter(ticker.EngFormatter(unit="°"))

        if crossover_marker is True:
            formatter = ticker.EngFormatter(unit="Hz", places=2)
            crossover_freq, crossover_phase = self.__find_crossover(freq_points, mag_points, phase_points)

            ax_gain.axvline(x=crossover_freq, linestyle="--", color="#DC143C", linewidth=1)
            ax_phase.axvline(x=crossover_freq, linestyle="--", color="#DC143C", linewidth=1)
            ax_phase.axhline(y=crossover_phase, linestyle="--", color="#DC143C", linewidth=1)

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
