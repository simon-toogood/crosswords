from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import colorsys
import random
import numpy as np
from io import BytesIO
import math
from pathlib import Path
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import sys


class WordArt:
    def __init__(self, string, res=300, follow_path=None, fontpath="C:\Windows\Fonts\Comic.ttf", path_kwargs=dict(), **kwargs):
        self.string = str(string)
        self.res = res
        self.font = ImageFont.truetype(fontpath, size=res)
        if follow_path is None:
            self._generate_text_mask(**kwargs)  
        else:
            self._generate_text_mask_on_path(follow_path, path_kwargs=path_kwargs, **kwargs)

    @classmethod
    def randomise(cls, string, seed=None, res=300,):
        # Pick a random font
        fonts = list(Path(R"C:\Windows\Fonts").glob("*.ttf"))
        good = False
        while not good:
            font = random.choice(fonts)
            good = not is_missing_glyph("1", font)
            if not good:
                print(f"Rejecting {font}")

        # Pick random follow path
        x = random.random()
        if x > 0.8:
            f = random.random() * 2
            a = random.random() / 5
            w = cls(string, res=res, follow_path=sine_path, fontpath=font, path_kwargs={"freq":f, "amplitude":a})
        else:
            w = cls(string, res=res, fontpath=font)

        # Pick random colour
        x = random.random()
        gradient = x > 0.5
        if gradient:
            cmap = random.choice(plt.colormaps())
            direction = random.choice(["horizontal", "vertical", "radial", "diagonal"])
            w.add_gradient(cmap, direction)
        else:
            rgb = random_hls_in_rgb()
            w.set_colour(rgb)

        # extrude text?
        x = random.random()
        if x > 0.5:
            extruded = True
            depth = np.max((5, int(random.random() * 50)))
            direction = np.array((random.random(), random.random()))
            direction /= np.linalg.norm(direction)
            if gradient:
                darken = random.random()
                colour = None
            else:
                if x > 0.75:
                    darken = None
                    colour = random_hls_in_rgb(l=0.4)
                else:
                    darken = random.random()
                    colour = None
            w.extrude_text(depth, direction, darken, colour)
        else:
            extruded = False

        # Pick random shadow type
        x = random.random()
        if x < 0.33 and extruded:
            #drop shadow
            offset_x = (random.random() - 0.5) * 100
            offset_y = (random.random() - 0.5) * 100
            blur_radius = random.random() * 10 + 2
            shadow_colour = random_hls_in_rgb(s=random.random(), l=0.2)
            w.add_drop_shadow((offset_x, offset_y), blur_radius, shadow_colour)
        elif x < 0.67 and not extruded:
            # perspective shadow
            shear = (random.random() - 0.5) + 1
            vert = (random.random() - 0.5) + 1
            blur_radius = random.random() * 4
            shadow_colour = tuple(random_hls_in_rgb(s=random.random(), l=0.2))
            w.add_perspective_shadow(shear, vert, shadow_colour, blur_radius)
        else:
            # no shadow
            pass

        return w

    def _generate_text_mask(self):
        bbox = self.font.getbbox(self.string, anchor="lt")
        sx = (bbox[2] - bbox[0])
        sy = (bbox[3] - bbox[1])
        self.img = Image.new("RGBA", (sx,sy), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.img)
        draw.text((0,0), self.string, font=self.font, anchor="lt")
        self.baseline = bbox[3] - 1
        self._trim_canvas()

    def _generate_text_mask_on_path(
            self,
            path_func,
            spacing=1,
            angle_offset=0,
            path_kwargs=dict()
    ):
        # Measure total text length
        total_length = sum(self.font.getlength(c) for c in self.string) * spacing

        # Sample points along the path to get bounding box
        n_samples = max(200, len(self.string) * 10)
        points = []
        for i in range(n_samples+1):
            t = i / n_samples
            x, y, angle = path_func(t, **path_kwargs)
            points.append((x, y))
        
        # Convert unit coordinates to pixel coordinates
        xs, ys = zip(*points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Scale to text length in pixels
        # Scale factor to map unit length to text pixel length
        scale = total_length / (max_x - min_x) if max_x != min_x else 1
        bb = self.font.getbbox("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        char_height = bb[3] - bb[1]
        em = self.font.getbbox("m")
        char_width = em[2] - em[0]
        char_diag = int(math.sqrt(char_height**2 + char_width**2))
        
        width = int((max_x - min_x) * scale + 1) + char_diag
        height = int((max_y - min_y) * scale + 1) + char_diag

        # Create canvas
        img = Image.new("RGBA", (width, height), (0,0,0,0))

        # Draw each character along the path
        dist = 0
        for ch in self.string:
            ch_width = self.font.getlength(ch) * spacing
            t = dist / total_length
            x_unit, y_unit, angle = path_func(t, **path_kwargs)

            # Convert to pixel coordinates
            x_px = int((x_unit - min_x) * scale) + char_diag/2
            y_px = int((y_unit - min_y) * scale) + char_diag/2

            # Render character on its own layer
            ch_img = Image.new("RGBA", (width, height), (0,0,0,0))
            ch_draw = ImageDraw.Draw(ch_img)
            ch_draw.text((x_px, y_px), ch, font=self.font, fill=(255,255,255), anchor="mm")
            ch_img = ch_img.rotate(angle + angle_offset, center=(x_px, y_px), resample=Image.BICUBIC)

            # Composite onto main image
            img = Image.alpha_composite(img, ch_img)
            dist += ch_width

        # Trim excess blank space around image
        self.img = img
        self._trim_canvas()

    def _expand_canvas(self, factor=2):
        width, height = self.img.size
        new_width = int(width * factor)
        new_height = int(height * factor)

        # Create a new blank image with the same mode and white background
        new_image = Image.new("RGBA", (new_width, new_height), (0,0,0,0))

        # Calculate top-left coordinates to paste original image in the center
        left = (new_width - width) // 2
        top = (new_height - height) // 2

        # Paste the original image onto the new canvas
        new_image.paste(self.img, (left, top))

        # Modify baseline location
        self.baseline += top

        self.img = new_image

    def _trim_canvas(self):
        bbox = self.img.getbbox()
        self.baseline = bbox[3] - bbox[1] - 1
        self.img = self.img.crop(bbox)

    def set_colour(self, rgb):
        arr = np.array(self.img).astype(float)
        r, g, b, a = arr[...,0], arr[...,1], arr[...,2], arr[...,3]

        fr, fg, fb = rgb
        if not fr <= 1 and fg <= 1 and fb <= 1:
            factor = 255
        else:
            factor = 1

        r *= fr * factor
        g *= fg * factor
        b *= fb * factor

        # clip + reassemble
        out = np.dstack([r, g, b, a])
        out = np.clip(out, 0, 255).astype(np.uint8)
        self.img = Image.fromarray(out, "RGBA")

    def add_perspective_shadow(self, shear_factor=1, scale_factor=1.5, shadow_colour=(0,0,0), blur_radius=5):
        self._expand_canvas(3)
        tx = -shear_factor * self.baseline     
        ty = self.baseline * (1 - scale_factor)     
        matrix = (1, shear_factor, tx, 0, scale_factor, ty)

        sheared = self.img.transform(
            self.img.size,
            Image.AFFINE,
            matrix,
            resample=Image.BICUBIC,
            fillcolor=(0,0,0,0)
        )

        a = sheared.split()[-1]
        shadow_img = Image.new("RGBA", sheared.size, shadow_colour + (0,))
        shadow_img.putalpha(a)
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(blur_radius))

        shadow_img.paste(self.img, (0, 0), self.img)
        self.img = shadow_img
        self._trim_canvas()

    def add_drop_shadow(self, offset=(10, 20), blur_radius=5, shadow_colour=(0, 0, 0, 180)):
        """
        Adds a soft drop shadow behind the image.
        
        Parameters:
            offset (tuple): (x, y) pixel offset of the shadow relative to the image.
            blur_radius (int): how soft the shadow appears.
            shadow_colour (tuple): RGBA color of the shadow (default: semi-transparent black).
        """
        self._expand_canvas(1.2)
        offset = [int(x) for x in offset]

        # Create shadow base (just the alpha mask filled with shadow colour)
        r, g, b, a = self.img.split()
        shadow = Image.new("RGBA", self.img.size, tuple(shadow_colour))
        shadow.putalpha(a)

        # Apply Gaussian blur to soften shadow
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

        # Create a new image large enough to fit shadow + image
        width =  self.img.width + abs(offset[0])
        height = self.img.height + abs(offset[1])
        combined = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Compute placement positions
        shadow_pos = (max(offset[0], 0), max(offset[1], 0))
        img_pos =    (max(-offset[0], 0), max(-offset[1], 0))

        # Paste shadow, then original image
        combined.paste(shadow, shadow_pos, shadow)
        combined.paste(self.img, img_pos, self.img)

        # Update the instance image
        self.img = combined

    def add_gradient(self, cmap='viridis', direction='horizontal'):
        w, h = self.img.size

        if isinstance(cmap, str):
            cmap = cm.get_cmap(cmap)

        # Create normalized coordinate grid
        x = np.linspace(0, 1, w)
        y = np.linspace(0, 1, h)
        X, Y = np.meshgrid(x, y)

        if direction == 'horizontal':
            gradient = X
        elif direction == 'vertical':
            gradient = Y
        elif direction == 'diagonal':
            gradient = (X + Y) / 2
        elif direction == 'radial':
            cx, cy = 0.5, 0.5
            aspect = w / h
            Xn = (X - cx) * aspect
            Yn = (Y - cy)
            dist = np.sqrt(Xn**2 + Yn**2)
            gradient = dist / np.max(dist)
        else:
            raise ValueError("direction must be 'horizontal', 'vertical', or 'diagonal'")

        # Apply the colormap and convert to RGB 0–255
        rgba = cmap(gradient)
        rgb = (rgba[:, :, :4] * 255).astype(np.uint8)
        i = Image.fromarray(rgb, mode='RGBA') 
        self.img = ImageChops.multiply(self.img, i)

    def extrude_text(self, depth=10, direction=(-1,1), darken=None, colour=None):
        self._expand_canvas(1.1)
        if darken is not None and colour is not None:
            raise ValueError("Specify exactly one of darken or colour")
        
        w, h = self.img.size
        base = Image.new("RGBA", (w + depth, h + depth), (0, 0, 0, 0))
        arr = np.array(self.img).astype(np.float32)
        rgb, alpha = arr[..., :3], arr[..., -1]

        for i in range(0, depth, 1):
            if darken is not None:
                factor = darken ** (depth - i + 1)
                shaded_rgb = rgb * factor
            else:
                rgb[alpha != 0] = colour
                shaded_rgb = rgb
            shaded = np.concatenate([shaded_rgb, alpha[...,np.newaxis]], axis=-1).astype(np.uint8)
            layer = Image.fromarray(shaded, "RGBA")
            offset = (np.array(direction) / np.linalg.norm(direction) * i).astype(int).tolist()
            base.alpha_composite(layer, offset)

        # Front face on top
        base.alpha_composite(self.img, offset)

        self.img = base
        self._trim_canvas()
    
    def perspective_transform(self, x_tilt=0.3, y_tilt=0.1):

        w, h = self.img.size
        cx, cy = w / 2, h / 2

        self._expand_canvas(3)

        # Translation to keep transformation centered
        a, b, c = 1, x_tilt, -x_tilt * cy
        d, e, f = y_tilt, 1, -y_tilt * cx

        transformed = self.img.transform(
            self.img.size,
            Image.AFFINE,
            (a, b, c, d, e, f),
            resample=Image.BICUBIC,
            fillcolor=(0, 0, 0, 0)
        )
        
        self.img = transformed
        # self._trim_canvas()

    def show(self):
        draw = ImageDraw.Draw(self.img)
        # draw.line((0, self.baseline, 4000, self.baseline), width=2, fill=(255,0,0))

        # draw.line((0,0,0,self.img.height))

        self.img.show()

    def to_buffer(self):
        buf = BytesIO()
        self.img.save(buf, format="PNG")   # or "JPEG" depending on image
        buf.seek(0)
        return buf


def circle_path(t, start=0, end=360):
    theta = np.interp(t, (0,1), (np.deg2rad(start), np.deg2rad(end)))
    x = np.cos(theta)
    y = np.sin(theta)
    phi = -np.rad2deg(theta) - 90
    return x, y, phi


def sine_path(t, freq=1, amplitude=1, phase=0):
    y = np.sin(2*np.pi * t * freq + phase) * amplitude
    return t, y, 0


def is_missing_glyph(char, font):
    if not isinstance(font, ImageFont.FreeTypeFont):
        font = ImageFont.truetype(font)
    char_mask = font.getmask(char)
    missing_mask = font.getmask("\uFFFD")  # replacement char
    return list(char_mask) == list(missing_mask)


def random_hls_in_rgb(l=0.5, s=1):
    h = random.random()
    return [int(x*255) for x in colorsys.hls_to_rgb(h,l,s)]


if __name__ == "__main__":
    i = WordArt.randomise("13041")
    # i = WordArt("0123456789", follow_path=sine_path, path_kwargs={"amplitude":0.1})
    #i = WordArt("0123456789")
    # i.add_gradient(cmap="prism", direction="radial")
    # i.extrude_text(darken=0.90)
    # i.add_perspective_shadow(blur_radius=1, shear_factor=-1)
    #i.perspective_transform()
    i.show()