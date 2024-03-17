# colornamespace

colornamespace is a GUI program that maps your personal color semantics. It began as a consistent disagreement between my partner and myself about where the line is between "green" and "blue". We then discovered that we disagreed about the line between other colors as well. So I wrote this program to map out and visualize the differences in our color naming intuitions. The program displays a random color and you can choose which of twelve color words best describes that color. After you have categorized a few hundred colors, the boundaries of your color naming intuitions can be visualized in RGB space and HSV space.

## Installation

The best way to install the application is using `pip` or another python package manager. 

From the source directory:
```py -m pip install .```

From a source distribution file:
```py -m pip install /path/to/colornamespace-0.8.0.tar.gz```

## Usage

To run the application, run the command `ColorNameMapper` in a terminal window. The main application window allows you to categorize colors, review your categorizations for accuracy, save your answers to a text file, and load previously saved answers. 