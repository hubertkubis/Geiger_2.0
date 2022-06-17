import matplotlib.pyplot as plt
import smbus
import numpy as np
from matplotlib.animation import FuncAnimation
import collections
from timeit import default_timer as timer
from scipy.signal import find_peaks
import itertools
import time

# Variables for ADC.
address = 0x48
A0 = 0x40
bus = smbus.SMBus(1)

# Parameters.
x_len = 500                   # Number of points to display.
yTop_range = [0, 0.15]        # Range of possible Y values to display.
yBot_range = [0, 8]
xs = list(range(0, x_len))    # X-axis list - samples.


# Starting plot parameters.
plt.rcParams["figure.figsize"] = (20, 10)    
plt.style.use(['dark_background'])

# Zero arrays for datasets.
data = collections.deque(np.zeros(x_len))
time_stamp = collections.deque(np.zeros(x_len))
mSv_value = collections.deque(np.zeros(x_len))


# Reading data from ADC.
def read_pin():
    while True:
        bus.write_byte(address, A0)                   # Reading data from an input pin.
        value =((bus.read_byte(address))*3.3)/256     # Converting values to volts.
        return value

# Create figure for plotting
def getfigax():
    fig, (axTop, axBot) = plt.subplots(2,  tight_layout=True)     # Create a stack of two subplots.
    
    # Add labels
    axTop.set_title('Geiger Counter - peak value and radiation dose')
    axTop.set_ylabel('Peak Voltage [V]')
    axTop.set_label('CPM = 0')
    axTop.grid()                  # Adds a grid.
    axTop.margins(0,0)            # Set margins (x, y) to 0%.

    axBot.set_xlabel('Samples')
    axBot.set_ylabel('Radiation Dose [mSv\yr]')
    axBot.set_label('mSv/yr = 0')
    axBot.grid()
    axBot.margins(0,0)
    
    # Setting the axis range.
    axTop.set_ylim(yTop_range)
    axBot.set_ylim(yBot_range)

    # Create a blank line. We will update the line in animate.
    lineTop, = axTop.plot(xs, data)
    lineBot, = axBot.plot(xs, mSv_value)
    return fig, axTop, axBot, lineTop, lineBot


# This function is called periodically from FuncAnimation.
def animate(i, data, mSv_value):
    global time_stamp
    tim = timer()                      # Starts the timer.
    data.popleft()                     # Removes an element from the left side of the deque and returns the value.
    data.append(read_pin())            # Appends an element to the end of the deque.
    time_stamp.popleft()
    time_stamp.append(timer()-tim)
    
    peaks, _ = find_peaks(data)        # Takes a 1-D array and finds all local maxima by simple comparison of neighboring values.
    counts = len(peaks)                # Returns the length of the peaks array.
    
    cpm = counts / np.sum(time_stamp)  # Calculate the average number of CPMs from the number of peaks found and the time over which the counting took place.
    mSv = (counts * 0.000057)*1000     # Calculating the radiation dose value using CPM and a constant that is appropriately selected for the Geiger tube model.
    
    mSv_value.popleft()
    mSv_value.append(mSv)
    
    
    # Display the "calibration" until the table is filled.
    if time_stamp[0] == 0:
        legendTop = axTop.legend(["Calibration"])
        legendBot = axBot.legend(["Calibration"])
    
    # After filling the table, display the CPM and mSv values.
    if time_stamp[0] != 0:
        cpmRound = round(cpm)
        mSvRound = round(mSv,2)
        legendTop = axTop.legend([f"CPM = {cpmRound}"])
        legendBot = axBot.legend([f"mSv/yr = {mSvRound}"])

    
    # Update line with new Y values.
    lineTop.set_ydata(data)
    lineBot.set_ydata(mSv_value)

    return lineTop, lineBot, legendTop, legendBot

fig, axTop, axBot, lineTop, lineBot = getfigax()

# Set up plot to call animate() function periodically.
ani = FuncAnimation(fig, animate, fargs=(data, mSv_value), interval=1, blit=True)
plt.show()
