# Guardian Crossword Generator

Gets the Guardian Quick crossword and create a printable, accessible PDF.

## Installation


1. Create a virtual environment (recommended Python 3.12)
2. Install the packages listed in `requirements.txt`

## Usage


1. Run `main.py`
2. Enter the number of crosswords to generate (recommended to be an even number so that the crosswords can be printed double-sided with no blank pages)

   
   1. If you want to change the default starting point, then modify the number in `tracker.txt` and rerun the script
3. Find the PDF in the working directory (also printed at the end of the script)
4. Done!

## Known Issues

* The fun wordart generation is broken for some reason - I don’t know why and nor do I have the time or inclination to fix it yet
* If the clues are abnormally long then they cause wrapping issues and the crossword spills over onto two pages. If this occurs, reset the last generated crosssword number in `tracker.txt` and reduce the `fontsize` parameter in the `PDF.__init__` class in `main.py`
* For complex clues (eg. clues with hypens/word breaks that are split over multiple clues) then the automatic hyphening/breaking highlighting system may break. If this happens, tough luck because I’m not fixing that.


