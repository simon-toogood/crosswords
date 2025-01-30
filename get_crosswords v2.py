from bs4 import BeautifulSoup
import requests
import fpdf
import pypdf
import wordart
import os
import re
import numpy as np
import smtplib
from pathlib import Path
import random



class PDF(fpdf.FPDF):
    def __init__(self, number, **kwargs):
        super().__init__(orientation="landscape", **kwargs)
        self.number = number
        self.scale = 0.33
        self.hoffset = 5
        self.voffset = 10
        self.clue_width = self.w / 4 * 0.95
        self.fontsize = 15
        self.titlesize = 20
        self._font_init()
        self._parser_init()
        
    def _parser_init(self):
        url = f"https://www.theguardian.com/crosswords/quick/{self.number}/print"
        data = requests.get(url).text
        self.soup = BeautifulSoup(data, features="html.parser")

    def _font_init(self):
        self.add_font('GHGuardianHeadline-Light', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-Light.ttf', uni=True)
        self.add_font('GHGuardianHeadline-LightItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-LightItalic.ttf', uni=True)
        self.add_font('GHGuardianHeadline-Medium', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-Medium.ttf', uni=True)
        self.add_font('GHGuardianHeadline-MediumItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-MediumItalic.ttf', uni=True)
        self.add_font('GHGuardianHeadline-Bold', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-Bold.ttf', uni=True)
        self.add_font('GHGuardianHeadline-BoldItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-BoldItalic.ttf', uni=True)
        self.add_font('GuardianTextSans-Regular', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Regular.ttf', uni=True)
        self.add_font('GuardianTextSans-Regular', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Regular.ttf', uni=True)
        self.add_font('GuardianTextSans-RegularItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-RegularItalic.ttf', uni=True)
        self.add_font('GuardianTextSans-RegularItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-RegularItalic.ttf', uni=True)
        self.add_font('GuardianTextSans-Bold', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Bold.ttf', uni=True)
        self.add_font('GuardianTextSans-Bold', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Bold.ttf', uni=True)
        self.add_font('GuardianTextSans-BoldItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-BoldItalic.ttf', uni=True)
        self.add_font('GuardianTextSans-BoldItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-BoldItalic.ttf', uni=True)
        self.set_font(family='GuardianTextSans-Regular', style='', size=9)

    def _crossword2pdf(self, x, y):
        return (x*self.scale + self.hoffset,
                y*self.scale + self.voffset)
    
    def _pdf2crossword(self, x, y):
        return ((x - self.hoffset) / self.scale,
                (y - self.voffset) / self.scale)
    
    def rect(self, x, y, w, h, **kwargs):
        super().rect(*self._crossword2pdf(x, y), w*self.scale, h*self.scale, **kwargs)

    def text(self, x, y, text = ""):
        return super().text(*self._crossword2pdf(x, y), text)

    def draw_rect_from_tag(self, tag):
        self.rect(float(tag["x"]), 
                  float(tag["y"]),
                  float(tag["height"]),
                  float(tag["width"]),
                  style="F")
        
    def draw_text_from_tag(self, tag):
        self.text(float(tag["x"]), 
                  float(tag["y"]),
                  tag.text)

    def draw_clues(self):
        across, down = self.soup.find_all(class_="printable-crossword__clues")
        string = self.make_clue_string(down)
        self.set_xy(-self.clue_width, 10)
        self.set_font(family='GHGuardianHeadline-Bold',style='',size=self.titlesize)
        self.cell(self.clue_width, 5, "Down")
        self.set_font(family='GuardianTextSans-Regular',style='',size=self.fontsize)
        self.set_xy(-self.clue_width, 20)
        self.multi_cell(self.clue_width*0.95, self.fontsize/2, string, align="L")
        string = self.make_clue_string(across)
        self.set_xy(-self.clue_width*2.1, 10)
        self.set_font(family='GHGuardianHeadline-Bold',style='',size=self.titlesize)
        self.cell(self.clue_width, 5, "Across")        
        self.set_font(family='GuardianTextSans-Regular',style='',size=self.fontsize)
        self.set_xy(-self.clue_width*2.1, 20)
        self.multi_cell(self.clue_width, self.fontsize/2, string, align="L")

    def make_clue_string(self, tag):
        string = ""
        for clue in tag.find_all("li"):
            number = clue.find("span", class_="printable-crossword__clue__number").text
            text = clue.find("span", class_=None).text
            string += f"{number}: {text}\n"
        string = string.replace("–", "-").replace("—", "-")
        return string

    def draw_crossword(self):
        # Draw the black background
        self.set_fill_color(0)
        bg = self.soup.find(class_="crossword__grid-background")
        self.draw_rect_from_tag(bg)

        # Draw the crossword cells
        lookup = [None]
        for cell in self.soup.find(class_="cells").findChildren(recursive=False):
            if cell.name == "g":
                rect = cell.find("rect")
                text = cell.find("text")
                lookup.append((int(rect['x']), int(rect['y'])))
                self.draw_rect_from_tag(rect)
                self.draw_text_from_tag(text)   
            else:
                self.draw_rect_from_tag(cell)
        
        # Draw the clues   
        self.draw_clues()



pdf = PDF(17007)
pdf.add_page()
pdf.draw_crossword()
pdf.output(Rf'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\tmp\17007.pdf')



exit()


def generate_crossword_pdf(number, style):

    
    # Create a blank pdf
    pdf = fpdf.FPDF(orientation="landscape")
    pdf.add_page()

    # Do some spacing/sizing calculations
    crossword_width = float(soup.find(class_="crossword__grid-background")["width"])
    scale = pdf.w / (2 * crossword_width) * 0.95
    clue_width = pdf.w / 4 * 0.95
    cell_width = crossword_width / 13
    bar_width = 1.5
    hyphen_width = 3
    hyphen_height = 0.5
    border_size = 1
    voffset = 10
    hoffset = 5
    fontsize = 15
    titlesize = 20

    # Draw the crossword number
    #pdf.set_font(family='Times',style='',size=30)
    #pdf.text(10, voffset/2, f"Guardian Quick {number}")
    pdf.set_font(family='GuardianTextSans-Regular', style='', size=9)

    # Draw black background for crossword
    
    pdf.set_fill_color(255)

    # Draw the crossword cells
    

    # Draw the WORDART!
    gap = 2
    h, w = wordart.generate_wordart("crossword", style=style, filename="crossword.png")
    im_height = (pdf.h - voffset - float(bg["height"])*scale - 3*gap) / 2 * 0.9
    pdf.image("crossword.png", hoffset, pdf.h-im_height*2 - gap*2 - 5 , h=im_height)
    wordart.generate_wordart(str(number), style=style, filename="number.png")
    pdf.image("number.png", hoffset, pdf.h-im_height-gap-hoffset, h=im_height)


    # Add bars to multi word across clues
    for clue in make_clue_string(across).split("\n")[:-1]:
        x = re.findall(R"\((?:[^\(\)]*?,.*?)*\)", clue)
        n = int(re.findall(R"^[^:]+", clue)[0])
        if len(x) == 0:
            continue
        else:
            intervals = np.cumsum([int(b) for b in re.findall(R"\d+", x[0])])[:-1]
        origin = lookup[n]
        pdf.set_fill_color(0,255,0)
        for interv in intervals:
            pdf.rect((origin[0] + cell_width*interv) * scale + hoffset - bar_width/2, 
                     (origin[1]) * scale + voffset, 
                     bar_width, cell_width*scale, style="F")
   
    # ...Hyphens
    for clue in make_clue_string(across).split("\n")[:-1]:
        x = re.findall(R"\((?:[^\(\)]*?-.*?)*\)", clue)
        n = int(re.findall(R"^[^:]+", clue)[0])
        if len(x) == 0:
            continue
        else:
            intervals = np.cumsum([int(b) for b in re.findall(R"\d+", x[0])])[:-1]
        origin = lookup[n]
        print(intervals, origin, n)
        pdf.set_fill_color(255,0,0)
        for interv in intervals:
            print(interv)
            pdf.rect((origin[0] + cell_width*interv) * scale + hoffset - hyphen_width/2, 
                     (origin[1] + cell_width/2) * scale + voffset - hyphen_height/2, 
                     hyphen_width, hyphen_height, style="F")
        
    # ...down bars
    for clue in make_clue_string(down).split("\n")[:-1]:
        x = re.findall(R"\((?:[^\(\)]*?,.*?)*\)", clue)
        n = int(re.findall(R"^[^:]+", clue)[0])
        if len(x) == 0:
            continue
        else:
            intervals = np.cumsum([int(b) for b in re.findall(R"\d+", x[0])])[:-1]
        origin = lookup[n]
        pdf.set_fill_color(0,0,255)
        for interv in intervals:
            pdf.rect((origin[0]) * scale + hoffset - bar_width/2 + origin[0]/cell_width/31, 
                     (origin[1] + cell_width*interv) * scale + voffset, 
                     cell_width*scale, bar_width, style="F")


    # Save pdf
    pdf.output(Rf'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\tmp\{number}.pdf')


generate_crossword_pdf(17007, 20)

# with open("tracker.txt") as file:
#     from_ = int(file.read())

# to_ = from_ + int(input("How many crosswords to generate (should be an even number for double-sided printing):  "))

# for n in range(from_, to_):
#     style = random.randint(0,30)
#     while style in [2, 3, 4, 5, 11, 17, 23, 28, 29, 30]:
#         style = random.randint(0,30)
#     print(f"Generating crossword no.{n}, style {style}")
#     generate_crossword_pdf(n, style)
#     print()

# print("Merging single pdfs...")
# merger = pypdf.PdfWriter()
# for n in range(from_, to_):
#     merger.append(f"tmp/{n}.pdf")
# merger.write(f"{from_}_to_{to_}.pdf")
# merger.close()

# print("Clearing tmp folder...")
# for n in range(from_, to_):
#     os.remove(f"tmp/{n}.pdf")

# print("Writing tracker.txt...")
# with open("tracker.txt", mode="w") as file:
#     file.write(str(to_))

# print("Done!")

# # 17007 last recent one