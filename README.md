# TF2000 Remote Tools
Remote tools for Voltech TF2000 Frequency Response Analyzer control.  
Example plots:

#### 1. Installation
Code was written using Python 3.11.4. It is recommended to use virtual environment to run the scripts:
```
python -m venv .venv
```
To activate the virtual environment run *.venv/Scripts/Activate.ps1*.
To install required packages while in the virtual environment is active run:
```
pip install -r requirements.txt
```

#### 2. RS232 Communication
To connect TF2000 to the RS232 port of the PC, crosslinked cable is required.  
Device uses somewhat strange DE-9 connector pinout:
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

#### 3. TF2000_tools.py

The file contains a simple connector class that allows reading given number of data lines from the serial port.  
This is useful in the sweep mode, in which data is sent to the PC after every measurement.  
The Class saves received data to the file, and also prints Bode plot and save it as a .svg file.

#### 4. TODO
At the moment, only reading and showing Bode plots is available. Unfortunately, User manual v3.1 lacks information  
on some commands, such as setting the upper and lower sweep frequencies. If you have a newer user manual, any 
information on commands or the cryptic TFA.exe file, please contact me.  
Other option is to prepare a script which will poll every frequency point measurement.
It will be prepared in the next code iteration.