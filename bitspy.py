import pygame
import random
import colorsys
import math
import glob
import sys
import os
import traceback

import operator

from rendering import Renderer
from parsing import BitsyParser
from library import read_index

# CONFIG #
SCREEN = (480, 272)
ALIGN = 0 # "LEFT" "CENTER" "RIGHT"
ROTATE = 1 # 0 1 2 3
TEXT_DELAY = 50 #ms
SHOW_FPS = False
KEY_BINDINGS = {
    pygame.K_KP2: "RIGHT",
    pygame.K_KP5: "DOWN",
    pygame.K_KP8: "LEFT",
    pygame.K_KP6: "UP",
    pygame.K_BACKSPACE: "MENU",
    pygame.K_KP_PLUS: "DEBUG",

    pygame.K_RIGHT: "RIGHT",
    pygame.K_DOWN: "DOWN",
    pygame.K_LEFT: "LEFT",
    pygame.K_UP: "UP",
    pygame.K_e: "MENU",
    pygame.K_r: "DEBUG",

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

class DebugMenu:
    def __init__(self):
        self.screen = pygame.Surface((128, 128))
        self.options = ["rotate", "align", "show fps", "update"]
        self.index = 0

    def input(self, action, pressed):
        if action == "DOWN":
            self.index = (self.index + 1) % len(self.options)
        elif action == "UP":
            self.index = (self.index - 1) % len(self.options)
        elif (action == "MENU" or action == "DEBUG") and pressed:
            switch_focus(launcher)
        elif (action == "LEFT" or action == "RIGHT") and pressed:
            self.do_selected(action == "LEFT")

        self.render()

    def do_selected(self, left):
        global ROTATE, ALIGN, SHOW_FPS

        selected = self.options[self.index]

        if selected == "rotate":
            if left:
                ROTATE = (ROTATE - 1) % 4
            else:
                ROTATE = (ROTATE + 1) % 4
        elif selected == "align":
            if left:
                ALIGN = (ALIGN - 1) % 3
            else:
                ALIGN = (ALIGN + 1) % 3
            clear_screen()
        elif selected == "update":
            update_and_restart()
        elif selected == "show fps":
            SHOW_FPS = not SHOW_FPS

    def render(self):
        self.screen.fill(RENDERER.BLK)

        select_rect = (0, self.index * 12 + 8, 256, 11)

        for i, text in enumerate(self.options):
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, i * 12 + 8 + 2, RENDERER.BLK)

        buffer.fill((255, 255, 255, 255), select_rect)
        buffer.blit(self.screen, select_rect[:2], select_rect, pygame.BLEND_SUB)
        self.screen.blit(buffer, select_rect[:2], select_rect)

    def draw(self, display):
        display.blit(self.screen, (64, 64))

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

        self.show_info = False

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
        if action == "MENU" and pressed:
            self.menu_input()
            return
        elif action == "DEBUG" and pressed:
            switch_focus(debugmenu)
            return

        if action == "UP":
            self.row = (self.row - 1) % len(self.subset)
        elif action == "DOWN":
            self.row = (self.row + 1) % len(self.subset)
        elif action == "RIGHT" and pressed:
            if True:#self.show_info:
                try:
                    player.change_world(load_file(self.selected["boid"]))
                    switch_focus(player)
                except:
                    traceback.print_exc()
                    self.games.remove(self.selected)
                    self.row = (self.row - 1) % len(self.games)
                    player.ended = True
            else:
                self.show_info = True
        elif action == "LEFT" and pressed:
            pass#self.show_info = False

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
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, -1 * 12 + 8 + 2, RENDERER.BLK)

        i = self.ROWS_PER_PAGE
        if self.offset+i < len(self.subset):
            text = self.subset[self.offset+i]["title"]
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, i * 12 + 8 + 2, RENDERER.BLK)

        for i, entry in enumerate(chunk):
            text = entry["title"]
            RENDERER.font.render_text_line(self.screen, text, 8 + 1, i * 12 + 8 + 2, RENDERER.BLK)

        info_x = 128
        info_y = 256 - 44

        if row >= self.ROWS_PER_PAGE // 2:
            info_y = 8

        buffer.fill((255, 255, 255, 255), select_rect)
        buffer.blit(self.screen, select_rect[:2], select_rect, pygame.BLEND_SUB)
        self.screen.blit(buffer, select_rect[:2], select_rect)

        date = self.selected["date"].strftime("%Y/%m/%d")

        self.screen.fill(RENDERER.BLK, (info_x, info_y, 128 - 8, 36))
        RENDERER.font.render_text_line(self.screen, self.selected["credit"], info_x + 8, info_y + 8)
        RENDERER.font.render_text_line(self.screen, date.ljust(16) + "-" + chr(16), info_x + 8, info_y + 8 + 12)

        #if self.show_info:
        #    self.screen.fill(RENDERER.BLK, (8, 8, 256 - 16, 256 - 16))

class BitsyPlayer:
    OPERATORS = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.div,

        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "<=": operator.le,
        ">=": operator.ge,
    }

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
        self.dialogue_style = {"shk": False, "wvy": False, "rbw": False, "clr": 0}

        self.starting = False
        self.ending = False
        self.ended = True
        self.prev_frame = -1

    def change_world(self, world):
        self.dialogue_lines = []
        self.dialogue_char = 0
        self.dialogue_states = {}

        self.prev_frame = -1
        self.starting = True
        self.ending = False
        self.ended = False

        self.world = world
        self.renderer.prerender_world(world)

        self.avatar_x = self.world["sprites"]["A"]["x"]
        self.avatar_y = self.world["sprites"]["A"]["y"]

        for item in world["items"].itervalues():
            variable = '{item "%s"}' % item["id"]

            if variable not in world["variables"]:
                world["variables"][variable] = 0

        self.set_room(self.world["sprites"]["A"]["room"])

        self.buffer_dialogue(*self.world["title"])

    def get_room_from_id(self, id):
        return self.world["rooms"][id]

    def input(self, action, pressed):
        if (action == "MENU" or action == "QUIT") and pressed:
            switch_focus(launcher)
            return

        if self.dialogue_lines:
            if pressed:
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

    def avatar_occupying_object(self, object):
        return self.avatar_occupying(object["x"], object["y"])

    def avatar_occupying(self, x, y):
        return self.avatar_x == x and self.avatar_y == y

    def use_exit(self, exit):
        dest = exit["dest"]

        self.avatar_x = dest["x"]
        self.avatar_y = dest["y"]
        self.set_room(dest["room"])

    def use_ending(self, ending):
        if ending["id"] in self.world["endings"]:
            self.buffer_dialogue(*self.world["endings"][ending["id"]]["text"])

        self.ending = True

    def take_item(self, item):
        self.avatar_room["items"].remove(item)

        item_id = item["id"]
        inventory = self.world["sprites"]["A"]["items"]

        if item_id in inventory:
            inventory[item_id] += 1
        else:
            inventory[item_id] = 1

        variable = '{item "%s"}' % item_id
        self.world["variables"][variable] += 1

        self.execute_dialogue(self.world["items"][item_id]["dialogue"])

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

    def get_dialogue_text(self, id):
        return self.world["dialogues"][id]["text"]

    def move_into(self, x, y):
        room = self.avatar_room
        tile = self.avatar_room["tilemap"][y][x]

        for sprite in self.world["sprites"].values():
            if sprite["room"] == self.avatar_room["id"] and x == sprite["x"] and y == sprite["y"] and sprite["id"] != "A":
                dialogue = sprite["dialogue"]
                if dialogue is not None:
                    self.execute_dialogue(dialogue)
                return

        if not self.check_wall(x, y):
            self.avatar_x = x
            self.avatar_y = y

        for ending in room["endings"]:
            if self.avatar_occupying_object(ending):
                self.use_ending(ending)
                return

        for exit in room["exits"]:
            if self.avatar_occupying_object(exit):
                self.use_exit(exit)
                return

        for item in room["items"]:
            if self.avatar_occupying_object(item):
                self.take_item(item)
                self.pre_render_room()

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
                switch_focus(launcher)

        self.dialog.fill(RENDERER.BLK)
        self.dialogue_char = 0
        self.draw_next_char()

    def skip_dialogue(self):
        skipped = False

        while self.draw_next_char():
            skipped = True

        return skipped

    def draw_next_char(self):
        self.dialogue_char += 1

        self.draw_dialogue(self.dialogue_char)

        return self.dialogue_char < sum(len(line) for line in self.dialogue_lines)

    def get_rainbow_color(self, time, x):
        hue = abs(math.sin((time / 600.0) - (x / 8.0)))
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)

        return tuple(c * 255 for c in rgb)

    def draw_dialogue(self, limit):
        def disturb(func, time, offset, mult1, mult2):
            return func(time * mult1 - offset * mult2)

        self.dialog.fill(RENDERER.BLK)

        xoff = 8
        yoff = 8
        xspace = 6
        yspace = 8 + 4
        count = 0

        cut = False

        for y, line in enumerate(self.dialogue_lines[:2]):
            for x, cell in enumerate(line):
                if count >= limit:
                    cut = True
                    break

                time = pygame.time.get_ticks()
                color = None
                char, style = cell

                ox, oy = 0, 0

                if style["wvy"]:
                    oy += math.sin((time / 250.0) - (x / 2.0)) * 4;
                if style["shk"]:
                    oy += (3
                        * disturb(math.sin,time,x,0.1,0.5)
                        * disturb(math.cos,time,x,0.3,0.2)
                        * disturb(math.sin,time,y,2.0,1.0))
                    ox += (3
                        * disturb(math.cos,time,y,0.1,1.0)
                        * disturb(math.sin,time,x,3.0,0.7)
                        * disturb(math.cos,time,x,0.2,0.3))
                if style["rbw"]:
                    color = self.get_rainbow_color(time, x)
                if style["clr"] > 0:
                    color = self.palette[style["clr"] - 1]

                glyph = RENDERER.font.get_glyph(char, color)
                position = (xoff + x * xspace + int(ox), yoff + y * yspace + int(oy))

                self.dialog.blit(glyph, position)

                count += 1

        if not cut:
            self.dialog.blit(RENDERER.arrow, (xoff + 182, yoff + 20))

    def execute_set(self, set):
        _, dest, expression = set

        self.world["variables"][dest] = self.evaluate_expression(expression)

    def evaluate_condition(self, condition):
        if condition == "ELSE":
            return True

        operator, a, b = condition        
        left = self.evaluate_expression(a)
        right = self.evaluate_expression(b)
        value = self.OPERATORS[operator](left, right)

        return value

    def evaluate_expression(self, expression):
        command, values = expression[0], expression[1:]

        if command == "NUMBER" or command == "STRING":
            return values[0]
        elif command == "VARIABLE":
            variable = values[0]

            if not variable in self.world["variables"]:
                self.world["variables"][variable] = 0

            return self.world["variables"][variable]
        elif command == "OPERATOR":
            operator = values[0]
            left = self.evaluate_expression(values[1])
            right = self.evaluate_expression(values[2])
            return self.OPERATORS[operator](left, right)
        elif command == "FUNCTION":
            if values[0].startswith("item"):
                _, string = values[0].split(" ", 1)
                id = string.strip('"')

                for item in self.world["items"].itervalues():
                    if item["name"] == id:
                        id = item["id"]

                inventory = self.world["sprites"]["A"]["items"]

                if id in inventory:
                    return inventory[id]
                else:
                    return 0
            
            return self.world["variables"][values[0]]

        print("WARNING: didn't understand expression")
        print(expression)
        return 0

    def execute_list(self, type, options):
        assert options, "trying to execute an empty %s!" % type

        if id(options) not in self.dialogue_states:
            self.dialogue_states[id(options)] = -1

        curr = self.dialogue_states[id(options)]

        if type == "SHUFFLE":
            curr = random.randint(0, len(options) - 1)
        elif type == "CYCLE":
            curr = (curr + 1) % len(options)
        elif type == "SEQUENCE":
            curr = min(curr + 1, len(options) - 1)

        self.execute_node(options[curr])
        self.dialogue_states[id(options)] = curr

    def style_text(self, text, style):
        return [(char, style) for char in text]

    def execute_node(self, node):
        command = node[0]
        
        if len(node) > 1:
            arguments = node[1]

        if command == "DO":
            if type(arguments) == str:
                print(arguments)
            else:
                for argument in arguments:
                    self.execute_node(argument)
        elif command == "SAY":
            if type(arguments) == str:
                text = arguments
            else:
                value = self.evaluate_expression(arguments)
                text = str(value)

            self.buffer_dialogue(*text)
        elif command == "SET":
            self.execute_set(node)
        elif command == "IF":
            for condition, block in arguments:
                if self.evaluate_condition(condition):
                    self.execute_node(block)
                    break
        elif command == "CYCLE" or command == "SEQUENCE" or command == "SHUFFLE":
            self.execute_list(command, arguments)
        elif command == "\n":
            self.buffer_dialogue("\n")
        elif command == "SHK":
            self.toggle_dialogue_style("shk")
        elif command == "WVY":
            self.toggle_dialogue_style("wvy")
        elif command == "RBW":
            self.toggle_dialogue_style("rbw")
        elif command == "BR":
            self.buffer_dialogue("\n")
        elif command == "CLR1":
            self.set_dialogue_color(1)
        elif command == "CLR2":
            self.set_dialogue_color(2)
        elif command == "CLR3":
            self.set_dialogue_color(3)
        else:
            print(command)

    def toggle_dialogue_style(self, style):
        self.dialogue_style = dict(self.dialogue_style)
        self.dialogue_style[style] = not self.dialogue_style[style]

    def set_dialogue_style(self, **kwargs):
        self.dialogue_style = dict(self.dialogue_style)

        for key, value in kwargs.iteritems():
            self.dialogue_style[key] = value

    def set_dialogue_color(self, color):
        self.dialogue_style = dict(self.dialogue_style)

        if self.dialogue_style["clr"] == color:
            self.dialogue_style["clr"] = 0
        else:
            self.dialogue_style["clr"] = color

    def execute_dialogue(self, id):
        dialogue = self.world["dialogues"][id]
        root = dialogue["root"]

        # reset formatting
        self.set_dialogue_style(shk = False, wvy = False, rbw = False, clr = 0)

        if root is None:
            self.buffer_dialogue(*dialogue["text"])
        else:
            self.execute_node(root)

        self.word_wrap_dialogue()
        #self.debug_dialogue()

    def debug_dialogue(self):
        for line in self.dialogue_lines:
            print("".join(c[0] for c in line))

    def buffer_dialogue(self, *chars):
        if self.dialogue_lines:
            row = self.dialogue_lines.pop()
        else:
            row = []

        for char in chars:
            if char == "\n":
                self.dialogue_lines.append(row)
                row = []
            else:
                row.append((char, self.dialogue_style))

        self.dialogue_lines.append(row)

    def word_wrap_dialogue(self):
        y = 0

        while y < len(self.dialogue_lines):
            row = self.dialogue_lines[y]

            if len(row) > 32:
                split = 32

                for x in reversed(xrange(31)):
                    if row[x][0] == " ":
                        split = x
                        break

                remainder = row[split:]

                if remainder[0][0] == " ":
                    del remainder[0]

                self.dialogue_lines.insert(y + 1, remainder)

                del row[split:]

            y += 1

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
debugmenu = DebugMenu()
player = BitsyPlayer()
index = {}

def get_screen_rect():
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

    return (pad_x, pad_y, SCREEN[0], SCREEN[1])

def draw():
    gameDisplay.fill(RENDERER.BLK)

    rect = get_screen_rect()

    if FOCUS == launcher:
        player.screen.blit(launcher.screen, (0, 0))
    elif FOCUS == debugmenu:
        debugmenu.draw(player.screen)

    if SHOW_FPS:
        fps = str(round(clock.get_fps(), 1))
        RENDERER.font.render_text_line(player.screen, fps, 2, 2, RENDERER.BLK)

    screen2 = pygame.transform.rotate(player.screen, -90 * ROTATE)
    #screen2 = pygame.transform.scale2x(screen2)
    #screen2 = pygame.transform.scale(screen, (512, 512))
    #screen2 = pygame.transform.smoothscale(screen, ((272, 272)))
    gameDisplay.blit(screen2, rect[:2])

    pygame.display.update(rect)

def clear_screen():
    gameDisplay.fill(RENDERER.BLK)
    pygame.display.update()

RESTART = False
EXIT = False
FOCUS = launcher

def update_and_restart():
    rect = get_screen_rect()
    buffer.fill((255, 0, 0))
    RENDERER.font.render_text_line(buffer, "updating...", 8, 8, RENDERER.BLK)
    screen = pygame.transform.rotate(buffer, -90 * ROTATE)
    gameDisplay.blit(screen, rect[:2])
    pygame.display.update(rect)
    global EXIT, RESTART
    from subprocess import call
    call(["bash", os.path.join(ROOT, "update.sh")])
    EXIT = True
    RESTART = True

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

ANIM = 0

def switch_focus(thing):
    global FOCUS
    FOCUS = thing

def game_loop():
    global ROTATE, ALIGN, RESTART, EXIT, ANIM

    action = None
    pressed = False

    launcher.render_page()
    debugmenu.render()

    #get_avatars()

    while not EXIT:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                EXIT = True
            if event.type == pygame.KEYDOWN:
                pressed = True

                for key, val in KEY_BINDINGS.iteritems():
                    if event.key == key:
                        action = val

                used = True

                if action == "MENU":
                    FOCUS.input(action, True)
                elif action == "DEBUG":
                    FOCUS.input(action, True)
                elif action == "QUIT":
                    if FOCUS == launcher:
                        EXIT = True
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
                    pressed = False

        if ANIM % 3 == 0:
            down = pygame.key.get_pressed()

            for key, val in KEY_BINDINGS.iteritems():
                if down[key]:
                    action = val

            FOCUS.input(action, pressed)

            if FOCUS == player and not player.dialogue_lines and action is not None:
                capture_bg()

            action = None
            pressed = False

        if not player.ended:
            player.set_frame_count(ANIM)
        
        draw()
        
        clock.tick(FPS)
        ANIM += 1

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
