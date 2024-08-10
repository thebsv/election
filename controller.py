"""
This class is used to coordinate the whole election from a top level, it runs one thread.

It will hold an object of the election class, and it polls this class in both a 
blocking and non blocking fashion to get the current network wide leader. 

Contains functions that you can specify this instance of the application to do, if it is the
LEADER of the network, and also functions that it should do if it is one of the FOLLOWERS.

"""

__author__ = "Bhargav Srinivasan"
__copyright__ = "Copyright 2024, Earth"
__email__ = "bhargav.srinivasan92@gmail.com"
__version__ = "1.1.0"


import logging
import os
import threading