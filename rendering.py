import pygame

BLK = 0x000000
WHT = 0xFFFFFF
BGR = 0x999999
TIL = 0xFF0000
SPR = 0xFFFFFF

def render_data_to_surface(surface, data, foreground, background):
    pixels = pygame.PixelArray(surface)

    for y, row in enumerate(data):
        for x, char in enumerate(row):
            pixels[x, y] = background if char == "0" else foreground

    del pixels

def recolor_surface(surface, palette):
    pixels = pygame.PixelArray(surface)
    pixels.replace(BGR, palette[0])
    pixels.replace(TIL, palette[1])
    pixels.replace(SPR, palette[2])
    del pixels

class BitsyFontRender:
    BUFFER = pygame.Surface((6, 8))

    def __init__(self):
        self.font = [pygame.Surface((6, 8)) for i in xrange(256)]

    def load_font(self, data):
        sections = data.split("\n\n")

        for i, section in enumerate(sections):
            render_data_to_surface(self.font[i], section.split("\n"), WHT, BLK)

    def render_text_line(self, surface, text, x, y, background = None):
        if background is not None:
            surface.fill(background, (x - 1, y - 2, len(text) * 6 + 3, 11))

        for i, c in enumerate(text):
            surface.blit(self.font[ord(c)], (i * 6 + x, y))

    def get_glyph(self, character, color = None):
        glyph = self.font[ord(character)]

        if color:
            self.BUFFER.blit(glyph, (0, 0))
            glyph = self.BUFFER
            pixels = pygame.PixelArray(self.BUFFER)
            pixels.replace(WHT, color)
            del pixels

        return glyph

class Renderer:
    BLK = 0x000000
    WHT = 0xFFFFFF
    BGR = 0x999999
    TIL = 0xFF0000
    SPR = 0xFFFFFF

    def __init__(self):
        self.font = BitsyFontRender()
        self.arrow = pygame.Surface((5, 3))
        self.renders = {}

    def load_font(self, data, arrow = "11111\n01110\n00100"):
        self.font.load_font(data)
        render_data_to_surface(self.arrow, arrow.split("\n"), self.WHT, self.BLK)
        self.arrow = pygame.transform.scale(self.arrow, (10, 6))

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

    def recolor_surface(self, surface, palette):
        recolor_surface(surface, palette)

    def prerender_world(self, world):
        for item in world["items"].itervalues():
            self.prerender_graphic("item_" + item["id"], item["graphic"], self.SPR, self.BGR)

        for sprite in world["sprites"].itervalues():
            self.prerender_graphic("sprite_" + sprite["id"], sprite["graphic"], self.SPR, self.BGR)

        for tile in world["tiles"].itervalues():
            self.prerender_graphic("tile_" + tile["id"], tile["graphic"], self.TIL, self.BGR)

    def prerender_graphic(self, id, graphic, foreground, background):
        renders = [pygame.Surface((16, 16)), pygame.Surface((16, 16))]

        self.render_frame_to_surface(renders[0], graphic[ 0], foreground, background)
        self.render_frame_to_surface(renders[1], graphic[-1], foreground, background)

        self.renders[id] = renders
