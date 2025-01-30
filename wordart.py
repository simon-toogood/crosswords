import os
import numpy as np
from PIL import Image
from html2image import Html2Image


CANV_WIDTH = 1920
CANV_HEIGHT = 1080
SRC = None


def count_left(arr):
    i = 0
    for row in arr:
        if (row == (255,255,255)).all():
            i += 1
        else:
            return i

def count_right(arr):
    i = 0
    for row_index in range(arr.shape[0]):
        if (arr[-row_index] == (255,255,255)).all():
            i += 1
        else:
            return i
        

def crop_whitespace(arr):
    i = count_left(arr)
    j = count_right(arr)
    k = count_left(np.swapaxes(arr, 0,1))
    l = count_right(np.swapaxes(arr, 0,1))
    return arr[i:-j, k:-l]


def genHTML(wordartText, wordartStyle, wordartSize):
    srcfolder = os.path.abspath(os.path.dirname(__file__))
    myhtml = f"""<!DOCTYPE html>
                 <html>
                 <head>
                 <title>CSS3 WordArt</title>
                 <link href=\"file://{srcfolder}/css3wordart/css/style.css\" rel=\"stylesheet\" type=\"text/css\" />
                 <script src=\"file://{srcfolder}/css3wordart/js/object-observe-lite.js\"></script>
                 <script src=\"file://{srcfolder}/css3wordart/js/wordart.js\"></script>
                 </head>
                 <body>
                 <input type=\"hidden\" id=\"canvasWidth\" name=\"canvasWidth\" value=\"{CANV_WIDTH}\">
                 <input type=\"hidden\" id=\"canvasHeight\" name=\"canvasHeight\" value=\"{CANV_HEIGHT}\">
                 <input type=\"hidden\" id=\"wordart-style\" name=\"wordart-style\" value=\"{wordartStyle}\">
                 <input type=\"hidden\" id=\"wordart-size\" name=\"wordart-size\" value=\"{wordartSize}\">
                 <section class=\"background\">
                 <template id=\"bgWordart\">
                 <div class=\"wordart\">
                 <span class=\"text\" id=\"wordart-text\" name=\"wordart-text\" data-text=\"{wordartText}\">{wordartText}</span>
                 </div>
                 </template>
                 </section>
                 </body>
                 </html>"""
    return myhtml


def generate_wordart(string, style, filename="wordart.png"):
    if style in [5, 11, 17, 23, 29]:
        raise ValueError("Vertical styles not allowed")
    
    data = genHTML(string, style, 200)
    hti = Html2Image()
    hti.screenshot(html_str=data, save_as=filename)
    img = np.array(Image.open(filename))
    img = crop_whitespace(img)
    Image.fromarray(img).save(filename)
    return img.shape[0], img.shape[1]