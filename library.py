#!/usr/bin/env python
import os
import re
import json
import urllib2
import csv
import webbrowser
import traceback
from datetime import datetime
from StringIO import StringIO
from parsing import BitsyParser
from rendering import Renderer
from collections import OrderedDict

ROOT = os.path.dirname(__file__)

def read_index(file):
    index = OrderedDict()

    reader = csv.reader(file)
    reader.next()

    for row in reader:
        boid, published, title, author, url, jam, notes = row[:7]

        index[boid] = {
            "boid": boid,
            "date": datetime.strptime(published, "%d/%m/%Y"),
            "title": title,
            "credit": author,
            "url": url,
            "jam": jam,
            "notes": notes,
        }

    return index

def world(boid):
    entry = index[boid]

    try:
        dest = os.path.join(ROOT, "library", "%s.bitsy.txt" % boid)

        with open(dest, "rb") as file:
            data = file.read().replace("\r\n", "\n")
            lines = data.split("\n")
            parser = BitsyParser(lines)
            parser.parse(silent = True)
            return parser.world
    except Exception as e:
        print("Couldn't parse '%s' (%s)" % (entry["title"], entry["boid"]))
        traceback.print_exc()

    return None

def worlds(index):
    for entry in index.itervalues():
        world = world(entry["boid"])

        if world is not None:
            yield world

def download(index):
    for entry in sorted(index.itervalues(), key=lambda x: x["date"]):
        dest = os.path.join(root, "library", "%s.bitsy.txt" % entry["boid"])

        blank = True

        try:
            file = open(dest, "rb")
            blank = len(file.read().strip()) == 0
            file.close()
        except Exception as e:
            print(e)

        if blank and entry["notes"] != "no longer available":
            file = open(dest, "ab+")
            file.close()
            os.system(dest)
            webbrowser.open(entry["url"])
            raw_input(entry["title"] + ":")
            file = open(dest, "rb")
            data = file.read().replace(r'\"', r'"').replace(r"\n", "\n")
            file.close()
            print(len(data))
            open(dest, "wb").write(data)

def validate(index):
    for entry in sorted(index.itervalues(), key=lambda x: x["date"]):
        try:
            dest = os.path.join(root, "library", "%s.bitsy.txt" % entry["boid"])

            with open(dest, "rb") as file:
                data = file.read().replace("\r\n", "\n")
                lines = data.split("\n")
                parser = BitsyParser(lines)
                parser.parse(silent = True)
        except Exception as e:
            print("Couldn't parse '%s' (%s)" % (entry["title"], entry["boid"]))
            traceback.print_exc()

def median(lst):
    n = len(lst)
    if n < 1:
        return None
    if n % 2 == 1:
        return sorted(lst)[n//2]
    else:
        return sum(sorted(lst)[n//2-1:n//2+1])/2.0

def mode(lst):
    n = {}

    for v in lst:
        if not v in n:
            n[v] = 1
        else:
            n[v] += 1

    tiles = n.keys()
    tiles.sort(key = lambda x: n[x])

    return tiles[-1]

def world_contains_frame(world, frame):
    for tile in world["tiles"].itervalues():
        if graphic_contains_frame(tile["graphic"], frame):
            return True

    for sprite in world["sprites"].itervalues():
        if graphic_contains_frame(sprite["graphic"], frame):
            return True

    return False

def graphic_contains_frame(graphic, frame):
    for i in xrange(len(graphic)):
        f = graphic[i]

        match = True

        for y, row in enumerate(frame):
            for x, value in enumerate(row):
                if f[y][x] != value:
                    match = False
                    break

    return match

def get_avatar():
    pass

def get_cat():
    dest = os.path.join(root, "library", "%s.bitsy.txt" % "0FF04B41")

    with open(dest, "rb") as file:
        data = file.read().replace("\r\n", "\n")
        lines = data.split("\n")
        parser = BitsyParser(lines)
        parser.parse(silent = True)
        return parser.world["sprites"]["C"]["graphic"][0]

def stats(index):
    values = []

    target = "endings"
    cat = get_cat()

    for entry in sorted(index.itervalues(), key=lambda x: x["date"]):
        try:
            dest = os.path.join(root, "library", "%s.bitsy.txt" % entry["boid"])

            with open(dest, "rb") as file:
                data = file.read().replace("\r\n", "\n")
                lines = data.split("\n")
                parser = BitsyParser(lines)
                parser.parse(silent = True)
                if len(parser.world[target]) > 0:
                   values.append(len(parser.world[target]))
                #if len(parser.world["tiles"]) > 0:
                #    values.append(world_contains_frame(parser.world, cat))
        except Exception as e:
            print("Couldn't parse '%s' (%s)" % (entry["title"], entry["boid"]))
            traceback.print_exc()

    total = sum(1 if inc else 0 for inc in values)

    print("%s games, %s of which contain the bitsy cat (%s%%)" % (len(values), total, 100 * total / len(values)))

    """
    print("%s games total %s %s\nmin: %s\nmax: %s\nmean: %s\nmode: %s\nmedian: %s" % (
        len(values), 
        sum(values), 
        target,
        min(values),
        max(values),
        sum(values) / len(values), 
        mode(values), 
        median(values)))
    """

def get_version(entry):
    dest = os.path.join(root, "library", "%s.bitsy.txt" % entry["boid"])

    with open(dest, "rb") as f:
        for line in f:
            if line.startswith("# BITSY VERSION"):
                return line.rsplit(" ", 1)[1].strip()

    return "0"

def draw_avatars():
    import pygame
    pygame.init()

    renderer = Renderer()

    width = 35
    height = 13

    gap = 0

    page1 = pygame.Surface((width * (8 * 2 + gap) + gap, height * (8 * 2 + gap) + gap))
    page2 = pygame.Surface((width * (8 * 2 + gap) + gap, height * (8 * 2 + gap) + gap))

    values1 = []
    values2 = []

    for entry in sorted(index.itervalues(), key=lambda x: x["date"]):
        try:
            dest = os.path.join(ROOT, "library", "%s.bitsy.txt" % entry["boid"])

            with open(dest, "rb") as file:
                data = file.read().replace("\r\n", "\n")
                lines = data.split("\n")
                parser = BitsyParser(lines)
                parser.parse(silent = True)
                if len(parser.world["tiles"]) > 0:
                    graphic = parser.world["sprites"]["A"]["graphic"]
                    frame1, frame2 = pygame.Surface((16, 16)), pygame.Surface((16, 16))

                    renderer.render_frame_to_surface(frame1, graphic[ 0], renderer.SPR, renderer.BGR)
                    renderer.render_frame_to_surface(frame2, graphic[-1], renderer.SPR, renderer.BGR)
                    renderer.recolor_surface(frame1, parser.world["palettes"]["0"]["colors"])
                    renderer.recolor_surface(frame2, parser.world["palettes"]["0"]["colors"])
                    values1.append(frame1)
                    values2.append(frame2)
                #if len(parser.world["tiles"]) > 0:
                #    values.append(world_contains_frame(parser.world, cat))
        except Exception as e:
            print("Couldn't parse '%s' (%s)" % (entry["title"], entry["boid"]))
            traceback.print_exc()

    for y in xrange(height):
        for x in xrange(width):
            if y * width + x >= len(values1):
                break
            page1.blit(values1[y * width + x], (x * (8 * 2 + gap) + gap, y * (8 * 2 + gap) + gap))
            page2.blit(values2[y * width + x], (x * (8 * 2 + gap) + gap, y * (8 * 2 + gap) + gap))

    pygame.image.save(page1, "avatars1.png")
    pygame.image.save(page2, "avatars2.png")

def print_dialogues():
    with open("dialogues.txt", "w") as file:
        for world in worlds(index):
            for dialogue in world["dialogues"].itervalues():
                file.write(dialogue["text"])
                file.write("\n\n")

if __name__ == "__main__":
    root = os.path.dirname(__file__)

    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--update', '-u', dest='update', action='store_true',
                        help='update the list of known bitsy games from the online omnibus')
    parser.add_argument('--validate', '-v', dest='validate', action='store_true',
                        help='try to parse all stored gamedata to find problems')
    parser.add_argument('--download', '-d', dest='download', action='store_true',
                        help='semi-automated download process for missing games')
    parser.add_argument('--stats', '-s', dest='stats', action='store_true',
                        help='some stats')
    parser.add_argument('--versions', dest='versions', action='store_true',
                        help='print all bitsy versions')
    parser.add_argument('--avatars', '-a', dest='avatars', action='store_true',
                        help='generate avatar collage')
    parser.add_argument('--dialogues', dest='dialogues', action='store_true',
                        help='output all dialogues')
    parser.add_argument('--test', '-t', dest='test', action='store_true',
                        help='test flotsam parsing...')

    args = parser.parse_args()
    
    index = os.path.join(root, "library", "index.txt")
    content = open(index, "r+").read()

    if args.update:
        print("updating index...")
        url = r"https://docs.google.com/spreadsheets/d/1eBUgCYOnMJ9REHuZdTodc6Ft2Vs6JXbH4K-bIgL9TPc/gviz/tq?tqx=out:csv&sheet=Bitsy"
        content = urllib2.urlopen(url).read()
        open(index, "wb").write(content)

    index = read_index(StringIO(content))

    if args.validate:
        validate(index)

    if args.download:
        download(index)

    if args.stats:
        stats(index)

    if args.versions:
        for entry in index.itervalues():
            print("%s // %s" % (entry["title"], get_version(entry)))

    if args.avatars:
        draw_avatars()

    if args.dialogues:
        print_dialogues()

    if args.test:
        world("010BEB39")

    """
    for row in reader:
        boid, release, title, author, url, jam, notes = row

        dest = os.path.join(root, "library", boid + ".html")
        page = urllib2.urlopen(url).read()

        if not "<iframe" in page:
            open(dest, "wb").write(page)
        else:
            print("IFRAME")
    """

#    for name, entry in data["files"].iteritems():
#        dest = os.path.join(root, "games", name)
#        print(dest)
#        open(dest, "wb").write(entry["content"])
