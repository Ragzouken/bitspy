#!/usr/bin/env python
import os
import json
import urllib2
import csv
import webbrowser
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

if __name__ == "__main__":
    root = os.path.dirname(__file__)

    url = r"http://api.github.com/gists/1b7cc99139948d1f908962e4ef39b7fb"
    url = r"https://docs.google.com/spreadsheets/d/1eBUgCYOnMJ9REHuZdTodc6Ft2Vs6JXbH4K-bIgL9TPc/gviz/tq?tqx=out:csv&sheet=Bitsy"
    #data = json.load(urllib2.urlopen(url))

    content = urllib2.urlopen(url).read()
    open(os.path.join(root, "library", "index.txt"), "wb").write(content)

    reader = csv.reader(StringIO(content))
    reader.next()

    for row in reader:
        boid, release, title, author, url, jam, notes = row[:7]

        dest = os.path.join(root, "library", boid + ".bitsy.txt")

        file = open(dest, "rb")
        if not file.read().strip() and notes != "no longer available":
            webbrowser.open(url)
            os.system(dest)
            raw_input(title + ":")
            file = open(dest, "rb")
            data = file.read().replace(r'\"', r'"').replace(r"\n", "\n")
            file.close()
            print(len(data))
            open(dest, "wb").write(data)

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
