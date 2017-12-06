#!/usr/bin/env python
import os
import json
import urllib2
import csv

if __name__ == "__main__":
    root = os.path.dirname(__file__)

    url = r"http://api.github.com/gists/1b7cc99139948d1f908962e4ef39b7fb"
    url = r"https://docs.google.com/spreadsheets/d/1eBUgCYOnMJ9REHuZdTodc6Ft2Vs6JXbH4K-bIgL9TPc/gviz/tq?tqx=out:csv&sheet=Bitsy"
    #data = json.load(urllib2.urlopen(url))

    reader = csv.reader(urllib2.urlopen(url))
    reader.next()

    for row in reader:
        boid, release, title, author, url, jam, notes = row

        dest = os.path.join(root, "library", boid + ".bitsy.txt")
        open(dest, "ab").write("")

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
