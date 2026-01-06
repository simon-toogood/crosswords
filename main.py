import re
import os
import io
import sys
import random
import argparse
import datetime as dt
from pathlib import Path
from functools import partial
from multiprocessing import Pool, Manager, cpu_count

import fpdf
import pypdf
import requests
import numpy as np
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from google_news_feed import GoogleNewsFeed
from nltk.sentiment import SentimentIntensityAnalyzer

import wordart


class WhiteCell:
    def __init__(self, x, y, clue_number):
        self.x = x
        self.y = y
        self.clue_number = clue_number

    @classmethod
    def from_guardian_soup(cls, soup):
        if soup.name == "g":
            rect = soup.find("rect")
            text = soup.find("text").text
        else:
            rect = soup
            text = ""
        x = int(rect['x'])
        y = int(rect['y'])
        s = int(rect['height'])
        return cls(x//s, y//s, text)

    def is_clue_start(self):
        return self.clue_number != ""


class Clue:
    def __init__(self, number, direction, text, num_letters):
        self.number = number
        self.direction = direction
        self.text = text
        self.num_letters = num_letters

    def __repr__(self):
        return f"<Clue {self.number} {self.direction}: {self.text} {self.num_letters}>"
    
    def __str__(self):
        return f"**{self.number}:** {self.text} {self.num_letters}"

    @classmethod
    def from_guardian_soup(cls, soup, direction):
        text = soup.find("span", class_=None).text
        n = soup.find("span", class_="printable-crossword__clue__number").text
        x = re.findall(r"\(.*?\)", text)
        if len(x) == 0:
            x = ""
        else:
            x = x[-1]
        
        text = text.replace("–", "-").replace("—", "-")
        text = text.rstrip(x).rstrip()

        return cls(n, direction, text, x)
    
    def get_multiword_lengths(self):
        multiword = "," in self.num_letters or "-" in self.num_letters
        if not multiword:
            return False
        x = self.num_letters.replace("(", "").replace(")", "")
        numbers = list(map(int, re.findall(r'\d+', x)))
        delimiters = re.findall(r'[^\d]+', x)
        return numbers, delimiters


class GuardianQuickCrossword(fpdf.FPDF):
    def __init__(self, right_handed=True):
        super().__init__(orientation="landscape")
        self.set_auto_page_break(False, 0)
        self.right_handed = right_handed
        self.page_margin = 5
        self.clue_margin = 3
        self.news_height = 7
        self.res = 100
        self.clue_width = self.w/4 - self.page_margin/2 - self.clue_margin
        self.imfont = ImageFont.FreeTypeFont(R"fonts\GuardianTextSans-Regular.ttf", size=self.res//3.5)
        self.add_font(family="Guardian", style="", fname=R"fonts\GuardianTextSans-Regular.ttf")
        self.add_font(family="Guardian", style="b", fname=R"fonts\GHGuardianHeadline-Bold.ttf")
        self.set_font(family="Guardian", style="", size=14)

    def generate_new_page(self, number):
        self.add_page()

        # Get the crossword and parse using bs4
        url = f"https://www.theguardian.com/crosswords/quick/{number}/print"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, features="html.parser")
        number = number

        # Get the web version and scrape for the date
        s = BeautifulSoup(requests.get(f"https://www.theguardian.com/crosswords/quick/{number}").text,  features="html.parser")
        elem = s.find("div", attrs={"data-gu-name": "dateline"})
        date = dt.datetime.strptime(" ".join(elem.text.split()[:-1]), r"%a %d %b %Y %H.%M")

        # Extract clues
        a, d = soup.find_all(class_="printable-crossword__clues")
        across_clues = [Clue.from_guardian_soup(tag, "across") for tag in a.find_all("li")]
        down_clues = [Clue.from_guardian_soup(tag, "down") for tag in d.find_all("li")]
        all_clues = across_clues + down_clues

        # Extract white cells 
        white_cells = [WhiteCell.from_guardian_soup(x) for x in soup.find(class_="cells").find_all(recursive=False)]

        # Create the crossword grid
        self.create_crossword_image(white_cells, all_clues)

        # Draw the clues
        self.draw_clues(across_clues, down_clues)

        # Create the wordart
        self.create_wordart_image(number)

        # Draw the news headlines
        self.draw_news(date)

    def create_crossword_image(self, white_cells, clues, nx=13, ny=13, lw=1):
        image = Image.new(mode="L", size=(nx*self.res, ny*self.res), color=0)
        draw = ImageDraw.Draw(image)

        clue_map = dict()

        for cell in white_cells:
            draw.rectangle((cell.x*self.res, cell.y*self.res, (cell.x+1)*self.res, (cell.y+1)*self.res), fill=255, outline=0, width=lw)
            draw.text(((cell.x+0.05)*self.res, (cell.y+0.05)*self.res), text=cell.clue_number, font=self.imfont, anchor="lt", fill=0)
            if cell.is_clue_start():
                clue_map[cell.clue_number] = (cell.x, cell.y)
        draw.rectangle((0,0,image.width,image.height), fill=None, outline=0, width=2)

        for clue in clues:
            if a := clue.get_multiword_lengths():
                try:
                    x,y = clue_map[clue.number]
                except:
                    # sometimes the guardian puts multiple clue numbers on one line. cant be bothered to parse that
                    continue
                
                lengths, delims = a
                cum_length = np.cumsum(lengths)
                for d, c in zip(delims, cum_length):
                    if d == "-":
                        if clue.direction == "across":
                            draw.line(((x+c-0.2)*self.res, (y+0.5)*self.res, (x+c+0.2)*self.res, (y+0.5)*self.res), fill=0, width=lw*5)
                        else:
                            draw.line(((x+0.5)*self.res, (y+c-0.2)*self.res, (x+0.5)*self.res, (y+c+0.2)*self.res), fill=0, width=lw*5)
                    else:
                        if clue.direction == "across":
                            draw.line(((x+c)*self.res, y*self.res, (x+c)*self.res, (y+1)*self.res), fill=0, width=lw*5)
                        else:
                            draw.line((x*self.res, (y+c)*self.res, (x+1)*self.res, (y+c)*self.res), fill=0, width=lw*5)
        
        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        if self.right_handed:
            x = self.page_margin + 2*self.clue_margin + 2*self.clue_width
            self.image(buf, x=x, y=self.page_margin, w=self.w/2-self.page_margin)
        else:
            self.image(buf, x=self.page_margin, y=self.page_margin, w=self.w/2-self.page_margin)

    def create_wordart_image(self, number):
        w = wordart.WordArt.randomise(number)
        w._expand_canvas(1.1)
        img = w.to_buffer()

        crossword_height = self.w/2 - self.page_margin
        top = crossword_height + 2*self.page_margin
        bottom = self.h - self.page_margin - self.news_height
        if self.right_handed:
            x = self.page_margin + 2*self.clue_width + 2*self.clue_margin
        else:
            x = self.page_margin
        self.image(img, 
                   x, top, 
                   w=self.w/2-self.page_margin,
                   h=bottom-top,
                   keep_aspect_ratio=True)

    def draw_news(self, date):
        date = date.date()
        gnf = GoogleNewsFeed(language='en',country='GB')
        headlines = gnf.query("news", before=date+dt.timedelta(days=1), after=date)
        sia = _get_sia()
        heads = []
        sentiments = []
        for h in headlines:
            score = sia.polarity_scores(str(h))
            heads.append(str(h))
            sentiments.append(score['compound'] + 1)
        headline = random.choices(heads, weights=sentiments, k=1)[0]

        top = self.h - self.page_margin - self.news_height
        if self.right_handed:
            x = self.page_margin + 2*self.clue_width + 2*self.clue_margin
        else:
            x = self.page_margin
        self.set_xy(x, top)
        self.set_font("Guardian", "", 11)
        self.multi_cell(self.w/2-self.page_margin, 
                        text=f"**{date.strftime('%a %d %b %Y')}** {headline}",
                        align="l",
                        markdown=True)
        self.set_font("Guardian", "", 14)

    def draw_clues(self, across, down):
        h = 11
        if self.right_handed:
            x1edge = self.page_margin
            x2edge = self.page_margin + self.clue_width + self.clue_margin
        else:
            x1edge = self.w/2 + self.clue_margin
            x2edge = 3*self.w/4 - self.page_margin/2 + self.clue_margin
    
        across_string = "\n".join([str(c) for c in across])
        self.set_xy(x1edge, self.page_margin)
        self.set_font("Guardian", "b", 20)
        self.cell(self.clue_width, text="Across")
        self.set_font("Guardian", "", 14)
        self.set_xy(x1edge, self.page_margin+h)
        self.multi_cell(w=self.clue_width,
                        h=7, 
                        text=across_string,
                        align="l",
                        markdown=True)
        
        down_string = "\n".join([str(c) for c in down])
        self.set_xy(x2edge, self.page_margin)
        self.set_font("Guardian", "b", 20)
        self.cell(self.clue_width, text="Down")
        self.set_font("Guardian", "", 14)
        self.set_xy(x2edge, self.page_margin+h)
        self.multi_cell(w=self.clue_width,
                        h=7, 
                        text=down_string,
                        align="l",
                        markdown=True)

        # self.set_draw_color(255,0,0)
        # self.line(self.page_margin,0,self.page_margin,self.h, )
        # self.line(self.w-self.page_margin,0,self.w-self.page_margin,self.h, )
        # self.line(0, self.page_margin, self.w, self.page_margin)
        # self.line(0,self.h-self.page_margin,self.w,self.h-self.page_margin, )
        # self.line(self.w/2,0,self.w/2,self.h)

    def output_to_buffer(self):
        return io.BytesIO(self.output())


def _get_sia():
    try:
        return SentimentIntensityAnalyzer()
    except LookupError:
        import nltk
        nltk.download("vader_lexicon")
        return SentimentIntensityAnalyzer()
    

def parse_args():
    # Interactive mode
    if len(sys.argv) == 1:
        with open("tracker.txt", mode="r") as file:
            from_ = int(file.read())
        num = int(input("Enter number of crosswords to generate: "))
        return {"from": from_, 
                "to": from_+num, 
                "number": num, 
                "out": Path(os.getcwd()) / "pdfs", 
                "left_handed": False,
                "track": True}
    
    # Read command line arguments
    else:  
        parser = argparse.ArgumentParser(description="Utility for generating PDFs of the Guardian Quick crossword.")
        parser.add_argument("--from",   type=int,  help="The crossword number to start at (inclusive). Specify exactly two of --from, --to, --number")
        parser.add_argument("--to",     type=int,  help="The crossword number to end at (exclusive). Specify exactly two of --from, --to, --number")
        parser.add_argument("--number", type=int,  help="Number of crosswords to generate. Specify exactly two of --from, --to, --number")
        parser.add_argument("--out", default=Path(os.getcwd()) / "pdfs", help="Output directory for the generated PDF (default is cwd/pdfs/)")
        parser.add_argument("--left-handed", action="store_true", default=False, help="Generate left-handed crosswords (grid on left)")
        parser.add_argument("--track", action="store_true", default=False, help="Modify the tracker file after generation")
        args = parser.parse_args()

        provided = [args.from_ is not None,
                    args.to is not None,
                    args.number is not None]

        if sum(provided) != 2:
            parser.error("Exactly two of --from, --to, and --number must be provided.")

        if args.from_ is not None and args.to is not None:
            args.number = args.to - args.from_ + 1

        elif args.from_ is not None and args.number is not None:
            if args.number < 1:
                parser.error("--number must be >= 1")
            args.to = args.from_ + args.number - 1

        elif args.to is not None and args.number is not None:
            if args.number < 1:
                parser.error("--number must be >= 1")
            args.from_ = args.to - args.number - (-1)

        return {
            "from": args.from_,
            "to": args.to,
            "number": args.number,
            "out": Path(args.out),
            "left_handed": args.left_handed,
            "track": args.track
        }


def build_single_page(number, right_handed):
    page = GuardianQuickCrossword(right_handed=right_handed)
    page.generate_new_page(number)
    return number, page.output_to_buffer()  # return number so we can re-order later


if __name__ == "__main__":
    # Read in arguments from command line or interactively
    args = parse_args()
    right_handed = not args["left_handed"]

    # Set up multiprocessing pool
    manager = Manager()
    page_buffers = manager.dict() 
    n_processes = min(cpu_count(), args["number"])

    # Build pages in parallel
    print("Starting generation...")
    with Pool(processes=n_processes) as pool:
        imap = pool.imap_unordered(partial(build_single_page, right_handed=right_handed), list(range(args["from"], args["to"])))
        completed = 0
        for number, buffer_obj in imap:
            page_buffers[number] = buffer_obj
            completed += 1
            print(f"{completed}/{args['number']} pages completed")

    # Merge pages in order
    merger = pypdf.PdfWriter()
    for number in range(args["from"], args["to"]):
        merger.append(page_buffers[number])

    # Write final PDF to disk
    output_filename = args["out"] / f"{args['from']}_{args['to']}.pdf"
    with open(output_filename, "wb") as f:
        merger.write(f)
        merger.close()
    print(f"The PDF is at {output_filename}")

    # Update tracker
    if args["track"]:
        with open("tracker.txt", "w") as file:
            file.write(str(args["to"]))
