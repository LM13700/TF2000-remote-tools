from TF2000_tools import TF2000
import serial


def main():
    # May be used just to plot data without device connection
    # tf2000 = TF2000(
    #     None
    # )

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

    # When TF2000 is programmed from its front panel
    tf2000.read_to_file(lines_to_read=TF2000.LINES_120)

    # TF2000 programmed remotely
    tf2000.perform_gain_phase_analysis(generator_amplitude=get_generator_amplitude)

    tf2000.plot_bode_from_file()

    files = [
        "output/dataset_1.csv",
        "output/dataset_2.csv",
    ]
    legend = [
        "Original",
        "Compensated",
    ]
    tf2000.plot_bode_from_multiple_files(
        input_file_paths=files,
        legend_names=legend,
        output_file_path="output/comparison.svg",
    )


def get_generator_amplitude(frequency):
    if frequency < 3000.0:
        return 200
    else:
        return 20


if __name__ == "__main__":
    main()
