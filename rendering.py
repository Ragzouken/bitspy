import pygame

class Renderer:
    def __init__(self, font):
        self.font = font

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
