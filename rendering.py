import pygame

class Renderer:
    BLK = 0x000000
    WHT = 0xFFFFFF
    BGR = 0x999999
    TIL = 0xFF0000
    SPR = 0xFFFFFF

    def __init__(self):
        self.font = [pygame.Surface((6, 8)) for i in xrange(256)]
        self.arrow = pygame.Surface((5, 3))

    def load_font(self, data, arrow = "11111\n01110\n00100"):
        sections = data.split("\n\n")

        for i, section in enumerate(sections):
            self.render_data_to_surface(self.font[i], section.split("\n"), self.WHT, self.BLK)

        self.render_data_to_surface(self.arrow, arrow.split("\n"), self.WHT, self.BLK)
        self.arrow = pygame.transform.scale(self.arrow, (10, 6))

    def render_text_to_surface(self, surface, text, x, y, font = None):
        font = self.font if font is None else font

        for i, c in enumerate(text):
            surface.blit(font[ord(c)], (i * 6 + x, y))

    def render_frame_to_surface(self,
                                surface, 
                                frame,
                                foreground, 
                                background,
                                scale = 2):
        for y in xrange(0, 8):
            for x in xrange(0, 8):
                color = foreground if frame[y][x] else background
                surface.fill(color, (x * scale, y * scale, scale, scale))

    def render_data_to_surface(self,
                               surface,
                               data,
                               foreground,
                               background):
        pixels = pygame.PixelArray(surface)

        for y, row in enumerate(data):
            for x, char in enumerate(row):
                pixels[x, y] = background if char == "0" else foreground

    def recolor_surface(self, surface, palette):
        pixels = pygame.PixelArray(surface)
        pixels.replace(self.BGR, palette[0])
        pixels.replace(self.TIL, palette[1])
        pixels.replace(self.SPR, palette[2])
