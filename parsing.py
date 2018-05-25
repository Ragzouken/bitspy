from __future__ import print_function

import pprint
import traceback

LIST_TYPES = ["cycle", "shuffle", "sequence"]
TAGS = ["wvy", "shk", "rbw", "clr1", "clr2", "clr3", "br"]
COMPARISONS = [">=", "<=", ">", "<", "=="]
OPERATORS = ["+", "-", "*", "/"]
VARIABLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_.0123456789"

def make_say(chars):
    if len(chars) == 0:
        return ()
    else:
        return ("SAY", "".join(chars))

def clean_chunks(chunks):
    return [chunk for chunk in chunks if len(chunk) > 0]

def indent(string, count):
    return "%s%s" % (" " * count, string)

def string_comparison(comparison):
    operator, a, b = comparison

    left = string_expression(a)
    right = string_expression(b)

    return "%s %s %s" % (left, operator, right)

def string_expression(expression):
    return str(expression)

def print_dialogue(root, depth = 0):
    command = root[0]

    if command == "DO":
        #print(indent("DO:", depth))
        for chunk in root[1]:
            print_dialogue(chunk, depth)
    elif command == "IF":
        prefix = "IF"
        for chunk in root[1]:
            condition, block = chunk
            if condition != "ELSE":
                print(indent("%s %s THEN", depth) % (prefix, string_comparison(condition)))
                print_dialogue(block, depth + 1)
                prefix = "ELIF"
            else:
                print(indent("ELSE", depth))
        print(indent("END", depth))
    elif command == "SAY":
        print(indent('"%s"', depth) % (root[1],))
    elif command == "SET":
        print(indent("SET %s TO %s", depth) % (root[1], root[2]))
    elif command.lower() in LIST_TYPES:
        print(indent(command, depth))
        for chunk in root[1]:
            print_dialogue(chunk, depth + 1)
    elif command.lower() in TAGS:
        print(indent(command, depth))
    else:
        print(pad("OOPS %s", depth) % command)

class DialogueParser:
    def __init__(self, text, debug = None):
        self.text = text
        self.index = 0
        self.debug = debug
        self.taken = []

    def print_rest(self):
        print(self.text[:self.index])
        print("XXX HERE XXX")
        print(self.text[self.index:])

    def parse(self):
        chars = []
        chunks = []

        while self.index < len(self.text):
            if self.check("{"):
                chunks.append(make_say(chars))
                del chars[:]

                chunks.append(self.parse_code_block())
            else:
                chars.append(self.take())

        chunks.append(make_say(chars))

        chunks2 = [""]

        for chunk in chunks:
            if type(chunk) == str:
                chunks2[-1] = chunks2[-1] + chunk
            else:
                chunks2.append(chunk)
                chunks2.append("") 

        chunks = clean_chunks(chunks2)

        return ("DO", chunks)

    def parse_statements(self, text):
        statements = []
        for line in text.split("\n"):
            statements.append(self.parse_statement(line))

        return statements

    def parse_code_block(self):
        self.take("{")

        chars = []
        chunks = []

        def flush_chars():
            #chunks.append(self.parse_statement("".join(chars)))
            try:
                chunks.append(self.parse_statement("".join(chars)))
            except:
                print("-----")
                traceback.print_exc()
                self.print_rest()
                print("-----")
            del chars[:]

        def skip_to_end():
            skipped = []

            while not self.check("}"):
                if self.check("{"):
                    print("SKIPPING: %s" % (self.parse_code_block(),))
                else:
                    skipped.append(self.take())

            if skipped:
                print("SKIPPED: %s" % "".join(skipped))

        self.skip_whitespace()

        # either it's an if
        if self.check("-"):
            block = self.parse_if()
            skip_to_end()
            self.take("}")
            return block

        # or it's a sequence/cycle/shuffle
        for type in LIST_TYPES:
            if self.check(type):
                block = self.parse_list(type.upper())
                skip_to_end()
                self.take("}")
                return block

        # or it's a number of commands/nested code
        while not self.check("}"):
            # if an assigment or command didn't start yet, we can nest
            if not chars and self.check("{"): # can only nest if nothing else appeared during this line
                flush_chars()
                chunks.append(self.parse_code_block())
            # if a new line is starting, then the previous command is over
            if self.check("\n"): # newline means statement ends
                flush_chars()
                self.skip_whitespace()
            # read this command fully to find out what's going on
            else:
                chars.append(self.take())

        self.take("}")

        flush_chars()
        chunks = clean_chunks(chunks)

        return ("DO", chunks)

    def skip(self, *chars):
        while self.check(*chars):
            self.take()

    def skip_whitespace(self):
        lines = 0

        while self.check(" ", "\t", "\n"):
            if self.check("\n"):
                lines += 1

            self.take()

        return lines

    def parse_list_entry(self):
        self.skip_whitespace()
        self.take("-")
        self.skip(" ", "\t")

        # after a newline it's a new thing if it starts with -

        chars = []
        chunks = []

        if self.check("\n"):
            self.take("\n")
            self.skip_whitespace()

            # no content in this section
            if self.check("-"):
                return ("DO", chunks)

        while not self.check("}"):
            if self.check("{"):
                chunks.append(make_say(chars))
                del chars[:]

                chunks.append(self.parse_code_block())
            elif self.check("\n"):
                self.take("\n")
                self.skip_whitespace()

                if self.check("-") or self.check("}"):
                    break
                else:
                    chars.append("\n")
            else:
                chars.append(self.take())

        chunks.append(make_say(chars))
        chunks = clean_chunks(chunks)

        return ("DO", chunks)

    def parse_list(self, command):
        self.take(command.lower())

        branches = []

        while not self.check("}"):
            branches.append(self.parse_list_entry())

        return (command, branches)

    def parse_if_condition(self):
        chars = []

        self.take("-")
        self.skip_whitespace()

        while not self.check("?"):
            chars.append(self.take())

        return self.parse_comparison("".join(chars))

    def parse_if_block(self):
        chars = []
        chunks = []

        if self.check("\n"):
            self.take("\n")
            self.skip(" ")

        while not self.check("}"):
            if self.check("{"):
                chunks.append(make_say(chars))
                del chars[:]

                chunks.append(self.parse_code_block())
            elif self.check("\n"):
                self.take("\n")
                self.skip(" ")

                if self.check("-") or self.check("}"):
                    break
                else:
                    chars.append("\n")
            else:
                chars.append(self.take())

        chunks.append(make_say(chars))
        chunks = clean_chunks(chunks)

        return ("DO", chunks)

    def parse_if(self):
        branches = []

        while not self.check("}"):
            condition = self.parse_if_condition()

            self.take("?")

            block = self.parse_if_block()

            branches.append((condition, block))

        return ("IF", branches)

    def parse_statement(self, text):
        text = text.strip()

        if len(text) == 0:
            return []
        elif text in TAGS:
            return (text.upper(),)
        elif text.startswith("say"):
            _, expression = text.split(" ", 1)
            return ("SAY", self.parse_expression(expression))

        destination, expression = text.split("=", 1)
        expression = self.parse_expression(expression)

        return ("SET", destination.strip(), expression)

    def parse_comparison(self, text):
        text = text.strip()

        if text == "else" or text == "default":
            return "ELSE"

        for comparison in COMPARISONS:
            if comparison in text:
                a, b = text.split(comparison, 1)
                
                return (comparison, self.parse_expression(a), self.parse_expression(b)) 

        return None

    def tokenise_expression(self, text):
        input = list(reversed(text))
        chars = []
        tokens = []

        def take_number():
            del chars[:]

            if input and input[-1] == "-":
                chars.append(input.pop())
            while input and input[-1].isdigit():
                chars.append(input.pop())

            value = float("".join(chars))
            tokens.append(("NUMBER", value))

        def is_variable_char(char):
            return char in VARIABLE_CHARS

        def take_variable():
            del chars[:]

            while input and is_variable_char(input[-1]):
                chars.append(input.pop())

            tokens.append(("VARIABLE", "".join(chars)))

        def take_string():
            del chars[:]

            input.pop()

            while input[-1] != '"':
                chars.append(input.pop())

            input.pop()

            string = "".join(chars)
            tokens.append(("STRING", string))

        def take_function():
            del chars[:]
            
            input.pop()
            depth = 1

            while input and depth > 0:
                char = input.pop()

                if char == "}":
                    depth -= 1
                elif char == "{":
                    depth += 1
                else:
                    chars.append(char)

            return tokens.append(("FUNCTION", "".join(chars))) 

        while input:
            if input[-1] == " ":
                input.pop()
            elif input[-1] == '"':
                take_string()
            elif input[-1].isdigit() or (input[-1] == "-" and input[-2].isdigit()):
                take_number()
            elif input[-1] in OPERATORS:
                tokens.append(("OPERATOR", input.pop()))
            elif input[-1] == "{":
                take_function()
            elif is_variable_char(input[-1]):
                take_variable()
            else:
                print("DUNNO: '%s' of '%s'" % (input.pop(), text) )

        return tokens

    def parse_expression(self, text):
        text = text.strip()
        """parts = []

        while any(operator in text for operator in OPERATORS):
            for i in xrange(len(text)):
                if text[i] in OPERATORS:
                    operator = text[i]

                    part, text = text.strip().split(operator, 1)
                    parts.append(part.strip())
                    parts.append(operator)
                    break

        parts.append(text.strip())"""

        parts = self.tokenise_expression(text)

        output = []
        operators = []
        parts.reverse()

        while parts:
            token = parts.pop()

            if token[0] != "OPERATOR":
                output.append(token)
            else:
                prec1 = OPERATORS.index(token[1])

                while operators and operators.index(operators[-1]) >= prec1:
                    output.append(operators.pop())

                operators.append(token)

        while operators:
            output.append(operators.pop())

        def combine():
            if output[-1][0] == "OPERATOR":
                _, operator = output.pop()

                return ["OPERATOR", operator, combine(), combine()]
            else:
                return output.pop()

        root = combine()

        return root

    def check(self, *args):
        if "}" in args and self.index == len(self.text):
            if self.debug is not None:
                print(self.debug, end=" ")
            print("WARNING: inserting final }")
            self.text += "}"
            return True

        for string in args:
            if string == self.text[self.index:self.index + len(string)]:
                return True

        return False

    def take(self, expected = None):
        if expected is "}" and self.index == len(self.text):
            if self.debug is not None:
                print(self.debug, end=" ")
            print("WARNING: inserting final }")
            return "}"

        if expected is not None:
            if not self.check(expected):
                raise Exception("Did not find expected '%s' in '%s'" % (expected, self.text[self.index:self.index+16]))
            else:
                string = self.text[self.index:self.index + len(expected)]
                self.index += len(expected)
        else:
            string = self.text[self.index]
            self.index += 1

        return string

class BitsyParser:
    def __init__(self, lines):
        self.lines = lines
        self.index = 0
        self.world = {
            "title": None,
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

    def try_parse(self, text):
        try:
            parser = DialogueParser(text)
            return parser.parse()
        except:
            return ("SAY", text)

    def parse(self, silent = False):
        if not any(line.strip() for line in self.lines):
            return

        if not self.peek_line().strip():
            self.take_line()

        self.world["title"] = self.try_parse(self.take_line())

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

        for id, count in self.world["sprites"]["A"]["items"].iteritems():
            variable = '{item "%s"}' % id
            self.world["variables"][variable] = count

        if "global_walls_mod" in self.world:
            for id in self.world["global_walls_mod"]:
                self.world["tiles"][id]["wall"] = True

        if self.world["sprites"]["A"]["room"] is None:
            self.world["sprites"]["A"]["room"] = "0"

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
        ending["text"] = self.try_parse(self.take_line())

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
        sprite["name"] = self.parse_name()

        if self.check_line("DLG "):
            _, sprite["dialogue"] = self.take_line().split(" ", 1)

        if self.check_line("POS "):
            _, sprite["room"], pos = self.take_split(" ") 
            sprite["x"], sprite["y"] = (int(c) for c in pos.split(","))

        while self.check_line("ITM "):
            _, id, count = self.take_split(" ")
            sprite["items"][id] = int(count)

        self.add_object("sprites", sprite)

    def parse_item(self):
        item = {
            "dialogue": None,
        }

        #print(self.peek_line())

        _, item["id"] = self.take_split(" ")
        item["graphic"] = self.parse_graphic()
        item["name"] = self.parse_name()

        if self.check_line("DLG "):
            _, item["dialogue"] = self.take_line().split(" ", 1)

        self.add_object("items", item)

    def major_version(self):
        version = self.world["version"]

        if version is None:
            return 0
        else:
            return int(version.split(".")[0])

    def parse_dialogue(self):
        dialogue = {
            "text": "",
            "root": None,
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

        if self.major_version() >= 4:
            parser = DialogueParser(dialogue["text"], debug = self.world["title"])
            try:
                dialogue["root"] = parser.parse()
            except:
                pass
                print("Couldn't parse:\n%s\n" % dialogue["text"])
                traceback.print_exc()

        #pprint.pprint(parser.parse())
        #print(dialogue["id"])
        #print_dialogue(parser.parse(), 1)
        #print("")

        self.add_object("dialogues", dialogue)

    def parse_variable(self):
        _, id = self.take_split(" ")
        value = self.take_line()

        try:
            value = float(value)
        except:
            pass

        self.world["variables"][id] = value

    def parse_graphic(self):
        graphic = [self.parse_frame()]

        if self.check_line(">"):
            self.take_line()
            graphic.append(self.parse_frame())

        while self.check_line(">"):
            self.take_line()
            self.parse_frame()
            #print("discarding extra frame")

        return graphic

    def parse_frame(self):
        return [[b == "1" for b in self.take_line()] for y in xrange(0, 8)]

    def parse_name(self):
        if self.check_line("NAME "):
            return self.take_split(" ")[1]
        else:
            return "unnamed"
