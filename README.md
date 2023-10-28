# TF2000 Remote Tools
Remote tools for Voltech TF2000 Frequency Response Analyzer control.

#### 1. TODO
At the moment, only reading and showing Bode plots is available. Unfortunetely, User manual v3.1 lacks information on  
some commands, such as setting the upper and lower sweep frequencies, which makes it impossible to fully automate  
device control. If you have a newer user manual, any information on commands or the cryptic TFA.exe file,  
please contact me.

#### 2. RS232 Communication
To connect TF2000 to the RS232 port of the PC, crosslinked cable is required.  
Device uses somewhat strage DE-9 connector pinout:
* PIN 6 - RX (input)
* PIN 7 - CTS (input)
* PIN 8 - TX (output)
* PIN 9 - RTS (output)
* Rest of the pins - Ground

This requires custom cable connecting *RX* to *TX* lines and *CTS* to *RTS* lines.

TF2000 needs following configuration to be able to communicate via RS232:  
PRINT &rarr; Parallel Port >OFF< &rarr; Serial Port >ON< &rarr; Serial Output >Computer< &rarr; Baud Rate >1200<

PC needs following serial port configuration:
* Baud: 1200
* Data bits: 8
* Parity: None
* Stop bits: 2
* Flow control: RTS/CTR

#### 3. TF2000_read_data.py

The file contains a simple connector class that allows reading given number of data lines from the serial port.  
This is usefull in the sweep mode, in which data is sent to the PC after every measurement.  
The Class saves received data to the file, and also prints Bode plot and save it as a .svg file.
