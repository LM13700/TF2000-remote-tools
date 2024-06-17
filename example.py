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

    tf2000.read_to_file(lines_to_read=TF2000.LINES_120)

    tf2000.plot_bode_from_file()

    files = ["output/dataset_1.csv", "output/dataset_2.csv",]
    legend = ["Original", "Compensated",]
    tf2000.plot_bode_from_multiple_files(input_file_paths=files, legend_names=legend,
                                         output_file_path="output/comparison.svg")

if __name__ == "__main__":
    main()
