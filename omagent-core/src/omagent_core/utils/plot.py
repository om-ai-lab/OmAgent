from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class Annotator:
    def __init__(self, im, line_width=None, font_size=None):
        im = im if isinstance(im, Image.Image) else Image.fromarray(im)
        self.im = im.copy()
        self.draw = ImageDraw.Draw(self.im)
        font = Path(__file__).parents[1].joinpath("resources/font.ttf")
        self.font = ImageFont.truetype(
            str(font), font_size or max(round(sum(self.im.size) / 2 * 0.035), 12)
        )
        self.lw = line_width or max(round(sum(im.size) / 2 * 0.003), 2)  # line width

    def insure(self, y1, x2, fh):
        x_bias = 0
        y_bias = 0
        if y1 < 0:
            y_bias = fh
        if x2 >= self.im.size[0]:
            x_bias = x2 - self.im.size[0]
        return x_bias, y_bias

    def box_label(
        self, box, label="", color=(128, 128, 128), txt_color=(255, 255, 255)
    ):
        # Add one xyxy box to image with label
        self.draw.rectangle(box, width=self.lw, outline=color)  # box
        if label:
            fh = (self.font.getbbox(label)[3] - self.font.getbbox(label)[1]) + 3
            w = self.font.getlength(label)  # text width
            x_bias, y_bias = self.insure(box[1] - fh, box[0] + w + 1, fh)
            self.draw.rectangle(
                [
                    box[0] - x_bias,
                    box[1] + y_bias - fh,
                    box[0] - x_bias + w + 1,
                    box[1] + y_bias + 1,
                ],
                fill=color,
            )
            self.draw.text(
                (box[0] - x_bias, box[1] + y_bias - 1),
                label,
                fill=txt_color,
                font=self.font,
                anchor="ls",
            )

    def polygon_label(self):
        pass

    def result(self):
        return self.im
