# Guardian Crossword Generator

Gets the Guardian Quick crossword and create a printable, accessible PDF. Now with WordArt!

## Installation


1. Create and activate a virtual environment (optional, recommended Python 3.12)
2. Install the packages listed in `requirements.txt` by running `pip install -r requirements.txt`
3. Done!

## Usage

The script can be run with no arguments (intended for quickly generating some new crosswords) or with a set of command line arguments for more customisation.

### Interactive mode


1. Run `main.py`
2. Enter the number of crosswords to generate (recommended to be an even number so that the crosswords can be printed double-sided with no blank pages)

   
   1. If you want to change the default starting point, then modify the number in `tracker.txt` and rerun the script
3. Find the PDF in the working directory (also printed at the end of the script)
4. Done! The script will modify the start point in `tracker.txt` so the next time you run the script it will carry on from where it left off.

### Command line


1. Call main.py using the following arguments:

   ```
     -h, --help       Show this help message
     --from FROM      The crossword number to start at (inclusive). Specify exactly two of --from, --to, --number
     --to TO          The crossword number to end at (exclusive). Specify exactly two of --from, --to, --number  
     --number NUMBER  Number of crosswords to generate. Specify exactly two of --from, --to, --number
     --out OUT        Output directory for the generated PDF (default is cwd/pdfs/)
     --left-handed    Generate left-handed crosswords (grid on left)
     --track          Modify the tracker file after generation
   ```
2. The PDF is generated in the given location.

## Known Issues

* If the clues are abnormally long then they cause wrapping issues and the crossword spills over onto two pages. If this occurs, reset the last generated crosssword number in `tracker.txt` and reduce the `size` parameter in the `GuadianQuickCrossword.imfont` object in `main.py`.
* For compound clues (single clues that are split over multiple clue numbers) then the automatic hyphening/breaking highlighting system will fail to add any marks. If this happens, tough luck because I’m not fixing that.


