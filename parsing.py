class BitsyParser:
    def __init__(self, lines):
        self.lines = lines
        self.index = 0
        self.world = {
            "palettes": {},
            "rooms": {},
            "tiles": {},
            "sprites": {},
            "dialogues": {},
            "endings": {},
        }

    def add_object(self, type, object):
        self.world[type][object["id"]] = object

    def parse(self):
        self.world["title"] = self.take_line()

        while self.index < len(self.lines):
            if self.check_line("PAL "):
                self.parse_palette()
            elif self.check_line("ROOM "):
                self.parse_room()
            elif self.check_line("SET "):
                self.parse_room_old()
            elif self.check_line("TIL "):
                self.parse_tile()
            elif self.check_line("SPR "):
                self.parse_sprite()
            elif self.check_line("DLG "):
                self.parse_dialogue()
            elif self.check_line("END "):
                self.parse_ending()
            else:
                self.skip_line()

        self.repair()

    def repair(self):
        for id, sprite in self.world["sprites"].iteritems():
            if sprite["dialogue"] is None and id in self.world["dialogues"]:
                sprite["dialogue"] = id

    def take_line(self):        
        line = self.lines[self.index]
        self.index += 1
        return line

    def skip_line(self):
        line = self.take_line()

        if line.strip():
            print("skipping: " + line)

    def peek_line(self):
        return self.lines[self.index]

    def check_line(self, start):
        return self.peek_line().startswith(start)

    def check_blank(self):
        return len(self.peek_line().strip()) == 0

    def take_split(self, delimiter):
        return self.take_line().split(delimiter)

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
            "endings": [],
            "walls": [],
        }

        _, room["palette"] = self.take_split(" ")
        room["tilemap"] = [self.take_line() for y in xrange(0, 16)]

        if self.check_line("WAL "):
            room["walls"] = self.parse_room_walls()

        self.add_object("rooms", room)

    def parse_room(self):
        room = {
            "exits": [],
            "endings": [],
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
            else:
                print("skipping " + self.peek_line())
                self.take_line()

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

    def parse_room_ending(self):
        ending = {}

        _, ending["id"], pos = self.take_split(" ")
        ending["x"], ending["y"] = (int(c) for c in pos.split(",")) 

        return ending

    def parse_room_walls(self):
        _, row = self.take_split(" ")

        return row.split(",")

    def parse_ending(self):
        ending = {}

        _, ending["id"] = self.take_split(" ")
        ending["text"] = self.take_line()

        self.add_object("endings", ending)

    def parse_tile(self):
        tile = {}

        _, tile["id"] = self.take_split(" ")
        tile["graphic"] = self.parse_graphic()
        tile["name"] = self.parse_name()

        self.add_object("tiles", tile)

    def parse_sprite(self):
        sprite = {
            "room": None,
            "x": 0,
            "y": 0,
            "dialogue": None,
        }

        _, sprite["id"] = self.take_split(" ")
        sprite["graphic"] = self.parse_graphic()

        if self.check_line("DLG "):
            _, sprite["dialogue"] = self.take_line().split(" ", 1)

        if self.check_line("POS "):
            _, sprite["room"], pos = self.take_split(" ") 
            sprite["x"], sprite["y"] = (int(c) for c in pos.split(","))

        self.add_object("sprites", sprite)

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
        else:
            dialogue["text"] = self.take_line()

        self.add_object("dialogues", dialogue)

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
