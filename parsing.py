class BitsyParser:
    def __init__(self, lines):
        self.lines = lines
        self.index = 0
        self.world = {
            "version": None,
            "flags": {},
            "palettes": {},
            "rooms": {},
            "tiles": {},
            "sprites": {},
            "items": {},
            "dialogues": {},
            "endings": {},
            "variables": {},
        }

    def add_object(self, type, object):
        self.world[type][object["id"]] = object

    def parse(self, silent = False):
        if not self.peek_line().strip():
            self.take_line()

        self.world["title"] = self.take_line()

        while self.index < len(self.lines):
            if self.check_line("# BITSY VERSION"):
                self.world["version"] = self.take_line().rsplit(" ", 2)[-1]
            elif self.check_line("! "):
                _, id, value = self.take_split(" ", 3)
                self.world["flags"][id] = value
            elif self.check_line("PAL "):
                self.parse_palette()
            elif self.check_line("ROOM "):
                self.parse_room()
            elif self.check_line("SET "):
                self.parse_room_old()
            elif self.check_line("TIL "):
                self.parse_tile()
            elif self.check_line("SPR "):
                self.parse_sprite()
            elif self.check_line("ITM "):
                self.parse_item()
            elif self.check_line("DLG "):
                self.parse_dialogue()
            elif self.check_line("END "):
                self.parse_ending()
            elif self.check_line("VAR "):
                self.parse_variable()
            elif self.check_line("WAL "): #global walls mod
                self.world["global_walls_mod"] = self.take_split(" ")[1].split(",")
            else:
                self.skip_line(silent)

        self.repair()

    def repair(self):
        for id, sprite in self.world["sprites"].iteritems():
            if sprite["dialogue"] is None and id in self.world["dialogues"]:
                sprite["dialogue"] = id

        if "global_walls_mod" in self.world:
            for id in self.world["global_walls_mod"]:
                self.world["tiles"][id]["wall"] = True

    def take_line(self):        
        line = self.lines[self.index]
        self.index += 1
        return line

    def skip_line(self, silent = False):
        line = self.take_line()

        if line.strip() and not silent:
            print("skipping: " + line)

    def peek_line(self):
        return self.lines[self.index]

    def check_line(self, start):
        return self.peek_line().startswith(start)

    def check_blank(self):
        return len(self.peek_line().strip()) == 0

    def take_split(self, delimiter, limit = -1):
        return self.take_line().split(delimiter, limit)

    def parse_palette(self):
        palette = {}

        _, palette["id"] = self.take_split(" ")
        palette["name"] = self.parse_name()
        palette["colors"] = [self.parse_color(), self.parse_color(), self.parse_color()]

        self.add_object("palettes", palette)

    def parse_color(self):
        return [int(c) for c in self.take_split(",")]

    def parse_room_old(self):
        room = {
            "id": "0",
            "exits": [],
            "links": {},
            "endings": [],
            "walls": [],
            "items": [],
        }

        _, room["palette"] = self.take_split(" ")
        room["tilemap"] = [self.take_line() for y in xrange(0, 16)]

        if self.check_line("WAL "):
            room["walls"] = self.parse_room_walls()

        self.add_object("rooms", room)

    def parse_room(self):
        room = {
            "exits": [],
            "links": {},
            "endings": [],
            "walls": [],
            "items": [],
            "palette": "0",
        }

        _, room["id"] = self.take_split(" ")
        
        if "," in self.peek_line():
            room["tilemap"] = [self.take_split(",") for y in xrange(0, 16)]
        else:
            room["tilemap"] = [self.take_line() for y in xrange(0, 16)]

        room["name"] = self.parse_name()

        while not self.check_line("PAL") and not self.check_blank():
            if self.check_line("EXT "):
                room["exits"].append(self.parse_exit())
            elif self.check_line("WAL "):
                room["walls"] = self.parse_room_walls()
            elif self.check_line("END "):
                room["endings"].append(self.parse_room_ending())
            elif self.check_line("ITM "):
                room["items"].append(self.parse_room_item())
            elif self.check_line("LNK "):
                self.parse_room_link(room["links"])
            else:
                self.skip_line()

        if self.check_line("PAL"):
            _, room["palette"] = self.take_split(" ")

        self.add_object("rooms", room)

    def parse_exit(self):
        exit = {
            "dest": {},
        }

        _, pos1, room, pos2 = self.take_split(" ")
        
        exit["x"], exit["y"] = (int(c) for c in pos1.split(",")) 
        exit["dest"]["room"] = room
        exit["dest"]["x"], exit["dest"]["y"] = (int(c) for c in pos2.split(","))

        return exit

    def parse_room_link(self, links):
        _, dir, room = self.take_split(" ")

        links[dir] = room

    def parse_room_ending(self):
        ending = {}

        _, ending["id"], pos = self.take_split(" ")
        ending["x"], ending["y"] = (int(c) for c in pos.split(",")) 

        return ending

    def parse_room_walls(self):
        _, row = self.take_split(" ")

        return row.split(",")

    def parse_room_item(self):
        item = {}

        _, item["id"], pos = self.take_split(" ")
        item["x"], item["y"] = (int(c) for c in pos.split(","))

        return item

    def parse_ending(self):
        ending = {}

        _, ending["id"] = self.take_split(" ")
        ending["text"] = self.take_line()

        self.add_object("endings", ending)

    def parse_tile(self):
        tile = {
            "wall": False,
        }

        _, tile["id"] = self.take_split(" ", 1)
        tile["graphic"] = self.parse_graphic()
        tile["name"] = self.parse_name()

        if self.check_line("WAL "):
            tile["wall"] = self.take_split(" ")[1].strip() == "true"

        self.add_object("tiles", tile)

    def parse_sprite(self):
        sprite = {
            "room": None,
            "x": 0,
            "y": 0,
            "dialogue": None,
            "items": {},
        }

        _, sprite["id"] = self.take_split(" ")
        sprite["graphic"] = self.parse_graphic()

        if self.check_line("DLG "):
            _, sprite["dialogue"] = self.take_line().split(" ", 1)

        if self.check_line("POS "):
            _, sprite["room"], pos = self.take_split(" ") 
            sprite["x"], sprite["y"] = (int(c) for c in pos.split(","))

        while self.check_line("ITM "):
            _, id, count = self.take_split(" ")
            sprite["items"][id] = count

        self.add_object("sprites", sprite)

    def parse_item(self):
        item = {}

        #print(self.peek_line())

        _, item["id"] = self.take_split(" ")
        item["graphic"] = self.parse_graphic()
        item["name"] = self.parse_name()

        if self.check_line("DLG "):
            _, item["dialogue"] = self.take_line().split(" ", 1)

        self.add_object("items", item)

    def parse_dialogue(self):
        dialogue = {
            "text": "",
        }

        _, dialogue["id"] = self.take_split(" ")

        if self.check_line('"""'):
            self.take_line()
            dialogue["text"] = []
            while not self.check_line('"""'):
                dialogue["text"].append(self.take_line())
            dialogue["text"] = "\n".join(dialogue["text"])
            self.take_line()
        else:
            dialogue["text"] = self.take_line()

        self.add_object("dialogues", dialogue)

    def parse_variable(self):
        _, id = self.take_split(" ")
        self.world["variables"][id] = self.take_line()

    def parse_graphic(self):
        graphic = [self.parse_frame()]

        if self.check_line(">"):
            self.take_line()
            graphic.append(self.parse_frame())

        return graphic

    def parse_frame(self):
        return [[b == "1" for b in self.take_line()] for y in xrange(0, 8)]

    def parse_name(self):
        if self.check_line("NAME "):
            return self.take_split(" ")[1]
        else:
            return "unnamed"
