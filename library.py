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

def read_index(file):
    index = {}

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
    from parsing import BitsyParser

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
