Cplotter
======

[![Build Status](https://img.shields.io/badge/release-1.0.0-orange)](https://github.com/arcunique/Cplotter)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-371/)

Cplotter is a python package for runtime interaction with the Matplotlib plots generated. It allows users to 
modify data points on the plots as well as modify axis and figure layouts. This is extremely useful in removing the 
outliers and other unintended points in a plot. It has provision for keystroke inputs as well as mouse button inputs.
It also allows interaction through button widgets as well as I/O textbox. Once a plot (plots) is (are) generated
the control on the plot can be transferred to this package by calling the __iplot()__ class.

Author
------
* Aritra Chakrabarty (IIA, Bangalore)

Requirements
------------
* python>3.6
* numpy
* matplotlib 

Instructions on installation and use
------------------------------------
Presently, the code is only available on [Github](https://github.com/arcunique/Cplotter). Either download the code or
use the following line on terminal to install using pip:\
pip install git+https://github.com/arcunique/Cplotter  #installs from the current master on this repo.

The instructions regarding the use of the keystrokes, mouse buttons, button widgets and textboxes are as follows:
1. Use iplot() after plotting to acquire the control
2. Click the left MB to select a plot (line2D)
3. Click the right MB to delete a single point from a plot
4. To select multiple points take the cursor everytime near a point and press 'a'
5. To delete all the points selected press 'd'
6. Press 'u' to update the axis X & Y limits
7. In case multiple plots have a common point of intersection, to delete that point from one of these plots select the line first by clicking left MB and then press 'a' to select the point or directly delete by clicking right MB. Otherwise the tool will decide by itself which plot to delete the point from.
8. Undo a change by pressing 'Ctrl+z' and redo by pressing 'Ctrl+Shift+z' or 'Ctrl+y'
9. To pre-provide a path for saving a plot use the 'saveto' kwarg
10. To save a plot to any path type "save /full/path \[optional argument\]" in the 'I/O' textbox. The optional argument is either -c for the plot including the textboxes and buttons or -o for the figure only
11. Press the 'Save' button for quicksaving. If a path is pre-provided the plot is saved to that path, otherwise saves to the last path typed in the textbox. If no path is found, it shows a warning message
12. Also, you can type standard Python commands in the 'I/O' textbox. These commands, however, are not undo/redo-able
13. The control can be released by pressing 'Shift+q'






