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


def draw_rect(pdf, tag, voffset, hoffset, scale):
    pdf.rect(float(tag["x"])*scale + hoffset, 
             float(tag["y"])*scale + voffset, 
             float(tag["height"])*scale, 
             float(tag["width"])*scale,
             style="F",)
    print(tag['width'], tag['height'])


def make_clue_string(tag):
    string = ""
    for clue in tag.find_all("li"):
        number = clue.find("span", class_="printable-crossword__clue__number").text
        text = clue.find("span", class_=None).text
        string += f"{number}: {text}\n"
    string = string.replace("–", "-").replace("—", "-")
    return string


def generate_crossword_pdf(number, style):

    # Download the crossword and set up parser
    url = f"https://www.theguardian.com/crosswords/quick/{number}/print"
    data = requests.get(url).text
    soup = BeautifulSoup(data, features="html.parser")

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

    # Add the Guardian fonts
    pdf.add_font('GHGuardianHeadline-Light', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-Light.ttf', uni=True)
    pdf.add_font('GHGuardianHeadline-LightItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-LightItalic.ttf', uni=True)
    pdf.add_font('GHGuardianHeadline-Medium', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-Medium.ttf', uni=True)
    pdf.add_font('GHGuardianHeadline-MediumItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-MediumItalic.ttf', uni=True)
    pdf.add_font('GHGuardianHeadline-Bold', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-Bold.ttf', uni=True)
    pdf.add_font('GHGuardianHeadline-BoldItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GHGuardianHeadline-BoldItalic.ttf', uni=True)
    pdf.add_font('GuardianTextSans-Regular', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Regular.ttf', uni=True)
    pdf.add_font('GuardianTextSans-Regular', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Regular.ttf', uni=True)
    pdf.add_font('GuardianTextSans-RegularItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-RegularItalic.ttf', uni=True)
    pdf.add_font('GuardianTextSans-RegularItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-RegularItalic.ttf', uni=True)
    pdf.add_font('GuardianTextSans-Bold', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Bold.ttf', uni=True)
    pdf.add_font('GuardianTextSans-Bold', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-Bold.ttf', uni=True)
    pdf.add_font('GuardianTextSans-BoldItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-BoldItalic.ttf', uni=True)
    pdf.add_font('GuardianTextSans-BoldItalic', '', R'\\uol.le.ac.uk\root\staff\home\s\scat2\My Documents\crosswords\fonts\GuardianTextSans-BoldItalic.ttf', uni=True)

    # Draw the crossword number
    #pdf.set_font(family='Times',style='',size=30)
    #pdf.text(10, voffset/2, f"Guardian Quick {number}")
    pdf.set_font(family='GuardianTextSans-Regular', style='', size=9)

    # Draw black background for crossword
    pdf.set_fill_color(0)
    bg = soup.find(class_="crossword__grid-background")
    draw_rect(pdf, bg, voffset, hoffset, scale)
    pdf.set_fill_color(255)

    # Draw the crossword cells
    lookup = [None]
    a = 0
    for i, cell in enumerate(soup.find(class_="cells").findChildren(recursive=False)):
        if cell.name == "g":
            rect = cell.find("rect")
            text = cell.find("text")
            lookup.append((int(rect['x']), int(rect['y'])))
            draw_rect(pdf, rect, voffset, hoffset, scale)
            pdf.text(float(text["x"])*scale + hoffset,
                    float(text["y"])*scale+0.5 + voffset,
                    text.text)
        else:
            draw_rect(pdf, cell, voffset, hoffset, scale)
    print(lookup)

    # Draw the WORDART!
    gap = 2
    h, w = wordart.generate_wordart("crossword", style=style, filename="crossword.png")
    im_height = (pdf.h - voffset - float(bg["height"])*scale - 3*gap) / 2 * 0.9
    pdf.image("crossword.png", hoffset, pdf.h-im_height*2 - gap*2 - 5 , h=im_height)
    wordart.generate_wordart(str(number), style=style, filename="number.png")
    pdf.image("number.png", hoffset, pdf.h-im_height-gap-hoffset, h=im_height)

    # Draw the across clues
    across, down = soup.find_all(class_="printable-crossword__clues")
    string = make_clue_string(down)
    pdf.set_xy(-clue_width, 10)
    pdf.set_font(family='GHGuardianHeadline-Bold',style='',size=titlesize)
    pdf.cell(clue_width, 5, "Down")

    pdf.set_font(family='GuardianTextSans-Regular',style='',size=fontsize)
    pdf.set_xy(-clue_width, 20)
    pdf.multi_cell(clue_width*0.95, fontsize/2, string, align="L")


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

    # Draw the down clues
    string = make_clue_string(across)
    pdf.set_xy(-clue_width*2.1, 10)
    pdf.set_font(family='GHGuardianHeadline-Bold',style='',size=titlesize)
    pdf.cell(clue_width, 5, "Across")

    pdf.set_font(family='GuardianTextSans-Regular',style='',size=fontsize)
    pdf.set_xy(-clue_width*2.1, 20)
    pdf.multi_cell(clue_width, fontsize/2, string, align="L")

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