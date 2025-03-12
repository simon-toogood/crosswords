from bs4 import BeautifulSoup
import requests
import fpdf
import re
import numpy as np
from pathlib import Path



class PDF(fpdf.FPDF):
    def __init__(self, **kwargs):
        super().__init__(orientation="landscape", **kwargs)
        self.set_auto_page_break(False, 0)
        self.scale = 0.33
        self.hoffset = 5
        self.voffset = 10
        self.clue_width = self.w / 4 * 0.95
        self.fontsize = 14
        self.titlesize = 20
        self.current_num = None
        self._font_init()
        
    def _parser_init(self, number):
        url = f"https://www.theguardian.com/crosswords/quick/{number}/print"
        resp = requests.get(url)
        data = resp.text
        self.soup = BeautifulSoup(data, features="html.parser")
        self.current_num = number

    def add_new_page(self, number):
        self.add_page()
        self._parser_init(number)
        self.draw_crossword()

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

    def draw_rect_from_tag(self, tag, color):
        self.set_fill_color(color)
        self.rect(float(tag["x"]), 
                  float(tag["y"]),
                  float(tag["height"]),
                  float(tag["width"]),
                  style="F")
        
    def draw_text_from_tag(self, tag):
        self.set_font(family='GuardianTextSans-Regular',style='',size=10)
        self.text(float(tag["x"])+1, 
                  float(tag["y"])+1,
                  tag.text)

    def draw_clues(self):
        self.across, self.down = self.soup.find_all(class_="printable-crossword__clues")
        string = self.make_clue_string(self.down)
        self.set_xy(-self.clue_width, 10)
        self.set_font(family='GHGuardianHeadline-Bold',style='',size=self.titlesize)
        self.cell(self.clue_width, 5, "Down")
        self.set_font(family='GuardianTextSans-Regular',style='',size=self.fontsize)
        self.set_xy(-self.clue_width, 20)
        self.multi_cell(self.clue_width*0.95, self.fontsize/2, string, align="L")
        string = self.make_clue_string(self.across)
        self.set_xy(-self.clue_width*2.1, 10)
        self.set_font(family='GHGuardianHeadline-Bold',style='',size=self.titlesize)
        self.cell(self.clue_width, 5, "Across")        
        self.set_font(family='GuardianTextSans-Regular',style='',size=self.fontsize)
        self.set_xy(-self.clue_width*2.1, 20)
        self.multi_cell(self.clue_width, self.fontsize/2, string, align="L")

    def make_clue_string(self, tag):
        string = ""
        for clue in tag.find_all("li"):
            n = clue.find("span", class_="printable-crossword__clue__number").text
            text = clue.find("span", class_=None).text
            string += f"{n}: {text}\n"
        string = string.replace("–", "-").replace("—", "-")
        return string

    def draw_crossword(self):
        # Draw the black background
        bg = self.soup.find(class_="crossword__grid-background")
        self.draw_rect_from_tag(bg, color=0)

        # Draw the crossword cells
        self.lookup = [None]
        for cell in self.soup.find(class_="cells").findChildren(recursive=False):
            if cell.name == "g":
                rect = cell.find("rect")
                text = cell.find("text")
                self.lookup.append((int(rect['x']), int(rect['y'])))
                self.draw_rect_from_tag(rect, color=255)
                self.draw_text_from_tag(text)   
            else:
                self.draw_rect_from_tag(cell, color=255)
        
        # Draw the clues   
        self.draw_clues()

        self.set_font_size(70)
        self.text(0, 550, str(self.current_num))
        self.set_font_size(14)
        self.text(0, 570, "wordart broke :(")

        # Draw the breaks
        self.draw_breaks()

    def draw_breaks(self):
        for clue in self.make_clue_string(self.across).split("\n")[:-1]:
            x = re.findall(r"\(.*?\)", clue)
            if len(x) == 0:
                continue
            else:
                x = x[-1]
            types = re.findall(r'(?<=\d)([^0-9]+)(?=\d)', x)

            try:
                n = int(re.findall(R"^[^:]+", clue)[0])
            except:
                continue

            if len(x) == 0:
                continue
            else:
                intervals = np.cumsum([int(b) for b in re.findall(R"\d+", x)])[:-1]

            origin = self.lookup[n]
            self.set_fill_color(0)
            for typ, intv in zip(types, intervals):
                if typ == ",":
                    self.rect(origin[0] + 32*intv - 3,
                            origin[1],
                            5, 31,
                            style="F")
                elif typ == "-":
                    self.rect(origin[0] + 32*intv - 5,
                            origin[1] + 16,
                            10, 2,
                            style="F")
                

        for clue in self.make_clue_string(self.down).split("\n")[:-1]:
            x = re.findall(r"\(.*?\)", clue)
            if len(x) == 0:
                continue
            else:
                x = x[-1]
            types = re.findall(r'(?<=\d)([^0-9]+)(?=\d)', x)

            try:
                n = int(re.findall(R"^[^:]+", clue)[0])
            except:
                continue 

            if len(x) == 0:
                continue
            else:
                intervals = np.cumsum([int(b) for b in re.findall(R"\d+", x)])[:-1]

            origin = self.lookup[n]
            self.set_fill_color(0)
            for typ, intv in zip(types, intervals):
                if typ == ",":
                    self.rect(origin[0],
                            origin[1] + 32*intv - 3,
                            31, 5,
                            style="F")
                elif typ == "-":
                    self.rect(origin[0] + 16,
                            origin[1] + 32*intv - 5,
                            2, 10,
                            style="F")
                

with open("tracker.txt") as file:
    from_ = int(file.read())

num = int(input("Enter number of crosswords to generate: "))

out_fp = Path(f"{from_}_{from_+num-1}.pdf")

pdf = PDF()
for n in range(from_, from_ + num):
    print(f"Generating {n}...")
    pdf.add_new_page(n)

pdf.output(out_fp)

with open("tracker.txt", mode="w") as file:
    file.write(str(from_ + num))

print(f"The PDF is at {out_fp.resolve()}")