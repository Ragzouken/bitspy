import pygame
from time import sleep
import random
import glob
import urllib2
import sys
import os
import csv
import traceback

from rendering import Renderer
from parsing import BitsyParser
from library import read_index

# CONFIG #
SCREEN = (480, 272)
ALIGN = 0 # "LEFT" "CENTER" "RIGHT"
ROTATE = 1 # 0 1 2 3
TEXT_DELAY = 50 #ms
KEY_BINDINGS = {
    pygame.K_KP2: "RIGHT",
    pygame.K_KP5: "DOWN",
    pygame.K_KP8: "LEFT",
    pygame.K_KP6: "UP",

    pygame.K_RIGHT: "RIGHT",
    pygame.K_DOWN:  "DOWN",
    pygame.K_LEFT:  "LEFT",
    pygame.K_UP:    "UP",

    pygame.K_BACKSPACE: "MENU",
    pygame.K_KP_PLUS: "DEBUG",
    pygame.K_q: "QUIT",
    pygame.K_ESCAPE: "QUIT",

    pygame.K_1: "ROTATE",
    pygame.K_2: "ALIGN",
}

FPS = 15
##########

ROOT = os.path.dirname(__file__)

pygame.init()
pygame.mouse.set_visible(False)

gameDisplay = pygame.display.set_mode(SCREEN)
buffer = pygame.Surface((256, 256))

pygame.display.set_caption('bitspy')

clock = pygame.time.Clock()

RENDERER = Renderer()

background = pygame.Surface((256, 256))
background.fill(RENDERER.BGR)

bg_inc = 255
bg_src = [(x, y) for x in xrange(16) for y in xrange(16)]
bg_dst = [(x, y) for x in xrange(16) for y in xrange(16)]

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, * sys.argv)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def chunk(l, n, i):
    return l[i:i + n]

class Launcher:
    ROWS_PER_PAGE = 20

    def __init__(self, screen = None):
        self.debug = False
        self.page = 0
        self.row = 0
        self.offset = 0
        self.games = []
        self.subset = []
        self.screen = screen if screen is not None else pygame.Surface((256, 256))
        self.selected = ""

        self.author = None
        self.saved_row = 0
        self.saved_offset = 0

    def menu_input(self):
        if self.author is not None:
            self.author = None
            self.row = self.saved_row
            self.offset = self.saved_offset
            self.subset = self.games
        else:
            self.author = self.selected["credit"]
            self.saved_row = self.row
            self.saved_offset = self.offset
            self.row = 0
            self.offset = 0
            self.subset = [game for game in self.games if game["credit"] == self.author]

        self.render_page()

    def input(self, action, pressed):
        if action == "MENU":
            self.menu_input()
            return

        if action == "UP":
            self.row = (self.row - 1) % len(self.subset)
        elif action == "DOWN":
            self.row = (self.row + 1) % len(self.subset)
        elif action == "RIGHT":
            try:
                player.change_world(load_file(self.selected["boid"]))
                switch_focus(player)
            except:
                traceback.print_exc()
                self.games.remove(self.selected)
                self.row = (self.row - 1) % len(self.games)
                player.ended = True

        d = self.row - self.offset

        if d >= self.ROWS_PER_PAGE - 4:
            self.offset = min(self.row - self.ROWS_PER_PAGE + 4, len(self.subset))
        elif d <= 4:
            self.offset = max(self.row - 4, 0)

        self.render_page()

    def render_page(self):
        chunk = self.subset[self.offset:self.offset+self.ROWS_PER_PAGE]
        row = self.row - self.offset
        self.selected = self.subset[self.row]

        select_rect = (0, row * 12 + 8, 256, 11)

        self.screen.blit(background, (0, 0))
        #self.screen.fill((96, 0, 0), )

        if self.offset > 0:
            text = self.subset[self.offset - 1]["title"]
            self.screen.fill(RENDERER.BLK, (8, -1 * 12 + 8, len(text) * 6 + 3, 11))
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, -1 * 12 + 8 + 2)

        i = self.ROWS_PER_PAGE
        if self.offset+i < len(self.subset):
            text = self.subset[self.offset+i]["title"]
            self.screen.fill(RENDERER.BLK, (8, i * 12 + 8, len(text) * 6 + 3, 11))
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, i * 12 + 8 + 2)

        for i, entry in enumerate(chunk):
            text = entry["title"]
            self.screen.fill(RENDERER.BLK, (8, i * 12 + 8, len(text) * 6 + 3, 11))
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, i * 12 + 8 + 2)

        info_x = 128
        info_y = 256 - 44

        if row >= self.ROWS_PER_PAGE // 2:
            info_y = 8

        #info_y = select_rect[1] - 44
        #info_y = max(8, info_y)
        #info_y = min(256 - 44, info_y)

        buffer.fill((255, 255, 255, 255), select_rect)
        buffer.blit(self.screen, select_rect[:2], select_rect, pygame.BLEND_SUB)
        self.screen.blit(buffer, select_rect[:2], select_rect)

        date = self.selected["date"].strftime("%Y/%m/%d")

        self.screen.fill(RENDERER.BLK, (info_x, info_y, 128 - 8, 36))
        RENDERER.font.render_text_line(self.screen, self.selected["credit"], info_x + 8, info_y + 8)
        RENDERER.font.render_text_line(self.screen, date.ljust(16) + "-" + chr(16), info_x + 8, info_y + 8 + 12)

class BitsyPlayer:
    def __init__(self):
        self.screen = pygame.Surface((256, 256))
        self.dialog = pygame.Surface((208, 38))

        self.room_frame_0 = pygame.Surface((256, 256))
        self.room_frame_1 = pygame.Surface((256, 256))

        self.avatar_frame_0 = pygame.Surface((16, 16))
        self.avatar_frame_1 = pygame.Surface((16, 16))

        self.renderer = Renderer()

        self.avatar_x = 0
        self.avatar_y = 0
        self.avatar_room = None
        self.palette = None

        self.dialogue_lines = []
        self.dialogue_char = 0

        self.starting = False
        self.ending = False
        self.ended = True
        self.prev_frame = -1

    def change_world(self, world):
        self.dialogue_lines = []
        self.dialogue_char = 0

        self.prev_frame = -1
        self.starting = True
        self.ending = False
        self.ended = False

        self.world = world
        self.renderer.prerender_world(world)

        self.avatar_x = self.world["sprites"]["A"]["x"]
        self.avatar_y = self.world["sprites"]["A"]["y"]

        self.set_room(self.world["sprites"]["A"]["room"])

        self.generate_dialogue(self.world["title"])

    def get_room_from_id(self, id):
        return self.world["rooms"][id]

    def input(self, action, key):
        if action == "MENU" or action == "QUIT":
            switch_focus(launcher)
            return

        if self.dialogue_lines:
            if key:
                self.advance_dialogue()
        else:
            if action == "LEFT":
                if self.avatar_x == 0 and "L" in self.avatar_room["links"]:
                    self.avatar_x = 15
                    self.set_room(self.avatar_room["links"]["L"])
                else:
                    self.move_into(max(0, self.avatar_x - 1), self.avatar_y)
            elif action == "RIGHT":
                if self.avatar_x == 15 and "R" in self.avatar_room["links"]:
                    self.avatar_x = 0
                    self.set_room(self.avatar_room["links"]["R"])
                else:
                    self.move_into(min(15, self.avatar_x + 1), self.avatar_y)
            elif action == "UP":
                if self.avatar_y == 0 and "U" in self.avatar_room["links"]:
                    self.avatar_y = 15
                    self.set_room(self.avatar_room["links"]["U"])
                else:
                    self.move_into(self.avatar_x, max(0, self.avatar_y - 1))
            elif action == "DOWN":
                if self.avatar_y == 15 and "D" in self.avatar_room["links"]:
                    self.avatar_y = 0
                    self.set_room(self.avatar_room["links"]["D"])
                else:
                    self.move_into(self.avatar_x, min(15, self.avatar_y + 1))

        self.draw(self.prev_frame)

    def set_frame_count(self, frame_count):
        next_frame = (frame_count // 6) % 2

        if next_frame != self.prev_frame:
            self.draw(next_frame)
        elif self.dialogue_lines and self.draw_next_char():
            self.draw_dialog()

    def draw(self, frame):
        self.prev_frame = frame
        self.screen.fill(self.palette[0]) 

        if not self.ending and not self.starting:
            room = self.room_frame_0 if frame == 0 else self.room_frame_1
            avi = self.avatar_frame_0 if frame == 0 else self.avatar_frame_1
            self.screen.blit(room, (0, 0))

            self.screen.blit(avi, (self.avatar_x * 16, self.avatar_y * 16))

        if self.dialogue_lines:
            self.draw_dialog()

    def draw_dialog(self):
        d_x = 24
        d_y = 24

        if self.starting or self.ending:
            d_y = 108
        elif self.avatar_y < 8:
            d_y = 194

        self.screen.blit(self.dialog, (d_x, d_y))

    def avatar_occupying(self, x, y):
        return self.avatar_x == x and self.avatar_y == y

    def use_exit(self, exit):
        dest = exit["dest"]

        self.avatar_x = dest["x"]
        self.avatar_y = dest["y"]
        self.set_room(dest["room"])

    def use_ending(self, ending):
        self.generate_dialogue(self.world["endings"][ending["id"]]["text"])
        self.ending = True

    def get_tile_from_id(self, tile_id):
        if tile_id in self.world["tiles"]:
            return self.world["tiles"][tile_id]
        else:
            return None

    def check_wall(self, x, y):
        room = self.avatar_room
        tile_id = self.avatar_room["tilemap"][y][x]
        tile = self.get_tile_from_id(tile_id)

        if room["walls"]:
            return tile_id in room["walls"]
        elif tile is not None:
            return tile["wall"]
        else:
            return False

    def move_into(self, x, y):
        room = self.avatar_room
        tile = self.avatar_room["tilemap"][y][x]

        for sprite in self.world["sprites"].values():
            if sprite["room"] == self.avatar_room["id"] and x == sprite["x"] and y == sprite["y"] and sprite["id"] != "A":
                dialogue = sprite["dialogue"]
                if dialogue is not None:
                    self.generate_dialogue(self.world["dialogues"][dialogue]["text"])
                return

        if not self.check_wall(x, y):
            self.avatar_x = x
            self.avatar_y = y

        for ending in room["endings"]:
            if self.avatar_occupying(ending["x"], ending["y"]):
                self.use_ending(ending)
                return

        for exit in room["exits"]:
            if self.avatar_occupying(exit["x"], exit["y"]):
                self.use_exit(exit)
                return

    def pre_render_room(self):
        self.render_room_frame(self.room_frame_0, self.avatar_room, 0)
        self.render_room_frame(self.room_frame_1, self.avatar_room, 1)

        self.avatar_frame_0.blit(self.renderer.renders["sprite_A"][ 0], (0, 0))
        self.avatar_frame_1.blit(self.renderer.renders["sprite_A"][-1], (0, 0))

        RENDERER.recolor_surface(self.avatar_frame_0, self.palette)
        RENDERER.recolor_surface(self.avatar_frame_1, self.palette)

    def render_room_frame(self, surface, room, frame):
        for y in xrange(0, 16):
            for x in xrange(0, 16):
                id = room["tilemap"][y][x]
                if id == "0":
                    surface.fill(RENDERER.BGR, (x * 16, y * 16, 16, 16))
                    continue
                tile = self.world["tiles"][id]

                surface.blit(self.renderer.renders["tile_" + id][frame], (x * 16, y * 16))

        for item in room["items"]:
            surface.blit(self.renderer.renders["item_" + item["id"]][frame], (item["x"] * 16, item["y"] * 16))

        for sprite in self.world["sprites"].values():
            if sprite["id"] != "A" and sprite["room"] == room["id"]:
                surface.blit(self.renderer.renders["sprite_" + sprite["id"]][frame], (sprite["x"] * 16, sprite["y"] * 16))

        RENDERER.recolor_surface(surface, self.palette)

    def set_room(self, id):
        room = self.get_room_from_id(id)

        self.avatar_room = room
        self.palette = self.world["palettes"][room["palette"]]["colors"]
        self.pre_render_room()

    def advance_dialogue(self):
        if self.skip_dialogue():
            return
        
        self.dialogue_lines = self.dialogue_lines[2:]

        if not self.dialogue_lines:
            self.starting = False

            if self.ending:
                self.ended = True

        self.dialog.fill(RENDERER.BLK)
        self.dialogue_char = 0
        self.draw_next_char()

    def skip_dialogue(self):
        skipped = False

        while self.draw_next_char():
            skipped = True

        return skipped

    def draw_next_char(self):
        xoff = 8
        yoff = 8
        chars = 32
        demo = "".join(line.ljust(chars) for line in self.dialogue_lines[:2])
        demo = demo[:chars*2]

        if self.dialogue_char >= len(demo):
            return False

        x = self.dialogue_char % 32
        y = self.dialogue_char // 32

        c = demo[self.dialogue_char]
        self.dialog.blit(RENDERER.font.font[ord(c)], (xoff + x * 6, yoff + y * (8 + 4)))

        self.dialogue_char += 1 
        while self.dialogue_char < len(demo) and demo[self.dialogue_char].strip() == "":
            self.dialogue_char += 1 

        if self.dialogue_char == len(demo):
            self.dialog.blit(RENDERER.arrow, (xoff + 182, yoff + 20)) 

        return True

    def generate_dialogue(self, text):
        lines = text.split("\n")
        rows = []
        limit = 32

        for line in lines:
            if len(line) > limit:
                row = ""
                words = line.split(" ")
                next = 0

                while next < len(words):
                    if len(row) + 1 + len(words[next]) > limit:
                        rows.append(row)
                        row = words[next]
                    elif row:
                        row += " " + words[next]
                    else:
                        row = words[next]

                    next += 1 

                if row:
                    rows.append(row)
            else:
                rows.append(line)

        self.dialogue_lines.extend(rows)

def load_file(name):
    file = os.path.join(ROOT, "games", name + ".bitsy.txt")
    music = os.path.join(ROOT, "games", name + ".ogg")

    with open(file, "rb") as file:
        data = file.read().replace("\r\n", "\n")
        lines = data.split("\n")
        parser = BitsyParser(lines)
        parser.parse()
        world = parser.world

        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(music)
            pygame.mixer.music.play(-1)
        except Exception as exception:
            print(exception)

        return world

def load_game():
    game = {}

    data = ""

    search = os.path.join(ROOT, "games", "*.bitsy.txt")

    global index
    index = read_index(open(os.path.join(ROOT, "games", "index.txt"), "rb"))

    for file in glob.glob(search):
        path, filename = os.path.split(file)
        boid, _, _ = filename.split(".")

        if boid in index:
            launcher.games.append(index[boid])

    random.shuffle(launcher.games)
    launcher.games.sort(key=lambda entry: entry["date"])
    launcher.subset = launcher.games

launcher = Launcher()
player = BitsyPlayer()
index = {}

def draw():
    gameDisplay.fill(RENDERER.BLK)

    gap_h = SCREEN[0] - 256
    gap_v = SCREEN[1] - 256
    pad_x = gap_h // 2
    pad_y = gap_v // 2

    if ALIGN == 0: # left
        pad_x = pad_y
    elif ALIGN == 1: # center
        pad_x = gap_h // 2
    elif ALIGN == 2: # right
        pad_x = SCREEN[0] - 256 - pad_y

    if FOCUS == launcher:
        player.screen.blit(launcher.screen, (0, 0))

    screen2 = pygame.transform.rotate(player.screen, -90 * ROTATE)
    #screen2 = pygame.transform.scale(screen, (512, 512))
    #screen2 = pygame.transform.smoothscale(screen, ((272, 272)))
    #pad_y = 0
    gameDisplay.blit(screen2, (pad_x, pad_y))

    pygame.display.update((pad_x, pad_y, SCREEN[0], SCREEN[1]))

def clear_screen():
    gameDisplay.fill(RENDERER.BLK)
    pygame.display.update()

RESTART = False
FOCUS = launcher

def capture_bg():
    global bg_inc
    bg_inc = bg_inc + 1
    if (bg_inc > 255):
        bg_inc = 0
        random.shuffle(bg_src)
        random.shuffle(bg_dst)

    sx, sy = bg_src[bg_inc]
    dx, dy = bg_dst[bg_inc]

    background.blit(player.screen, 
                    (sx * 16, sy * 16),
                    (dx * 16, dy * 16, 16, 16))

def switch_focus(thing):
    global FOCUS
    FOCUS = thing

def game_loop():
    global ROTATE, ALIGN, RESTART

    action = None
    pressed = False
    exit = False
    anim = 0

    launcher.render_page()

    #get_avatars()

    while not exit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
            if event.type == pygame.KEYDOWN:
                pressed = True

                for key, val in KEY_BINDINGS.iteritems():
                    if event.key == key:
                        action = val

                used = True

                if action == "MENU":
                    FOCUS.input(action, True)
                elif action == "DEBUG":
                    from subprocess import call
                    call(["bash", os.path.join(ROOT, "update.sh")])
                    exit = True
                    RESTART = True
                elif action == "QUIT":
                    if FOCUS == launcher:
                        exit = True
                    else: 
                        player.ended = True
                        switch_focus(launcher)
                elif action == "ROTATE":
                    ROTATE = (ROTATE + 1) % 4
                elif action == "ALIGN":
                    ALIGN = (ALIGN + 1) % 3
                    clear_screen()
                else:
                    used = False

                if used:
                    action = None

        if anim % 3 == 0:
            down = pygame.key.get_pressed()

            for key, val in KEY_BINDINGS.iteritems():
                if down[key]:
                    action = val

            FOCUS.input(action, pressed)

            if not player.ended and not player.dialogue_lines:
                capture_bg()

            action = None
            pressed = False

        if not player.ended:
            player.set_frame_count(anim)
        
        draw()
        
        clock.tick(FPS)
        anim += 1

    pygame.mouse.set_visible(True)
    pygame.quit()
    quit()

if __name__ == "__main__":
    with open(os.path.join(ROOT, "font.txt"), "rb") as file:
        RENDERER.load_font(file.read().replace("\r\n", "\n"))

    load_game()
    #launcher.render_page()
    game_loop()

    if RESTART:
        print("RESTARTING")
        restart_program()
