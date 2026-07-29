#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch (and keep up to date) a local copy of the DBLP XML dump.

import.py looks up publications in this local dump instead of hitting
the DBLP website once per publication, which is what used to get the
import script rate-limited/blocked on a heavily loaded DBLP.

Usage:
    python3 fetch_dblp_dump.py [--force] [--dir DIR]

See: https://dblp.org/faq/How+can+I+download+the+whole+dblp+dataset.html
"""

import argparse
import hashlib
import os
import sys
import urllib.request

DBLP_XML_URL = "https://dblp.org/xml/dblp.xml.gz"
DBLP_XML_MD5_URL = "https://dblp.org/xml/dblp.xml.gz.md5"
DBLP_DTD_URL = "https://dblp.org/xml/dblp.dtd"

USER_AGENT = "cryptobib import script 1.0"

scriptdir = os.path.dirname(os.path.realpath(__file__))
DEFAULT_DUMP_DIR = os.path.join(scriptdir, "dblp-dump")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as f:
        return f.read()


def fetch_to_file(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    tmp_path = path + ".part"
    with urllib.request.urlopen(req) as r, open(tmp_path, "wb") as out:
        total = int(r.headers.get("Content-Length", 0))
        read = 0
        chunk_size = 1024 * 1024
        while True:
            chunk = r.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            read += len(chunk)
            if total:
                print(
                    "\r  {} / {} MiB ({:.0%})".format(
                        read // (1024 * 1024), total // (1024 * 1024), read / total
                    ),
                    end="",
                    file=sys.stderr,
                )
        print(file=sys.stderr)
    os.replace(tmp_path, path)


def md5sum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def remote_md5():
    # format: "<md5>  dblp.xml.gz"
    return fetch(DBLP_XML_MD5_URL).decode("ascii").split()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        default=DEFAULT_DUMP_DIR,
        help="directory to store the dump in (default: {})".format(DEFAULT_DUMP_DIR),
    )
    parser.add_argument(
        "--force", action="store_true", help="redownload even if local copy looks current"
    )
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)
    gz_path = os.path.join(args.dir, "dblp.xml.gz")
    dtd_path = os.path.join(args.dir, "dblp.dtd")

    print("Checking remote dblp.xml.gz checksum...")
    want_md5 = remote_md5()

    if not args.force and os.path.exists(gz_path) and md5sum(gz_path) == want_md5:
        print("Local dump already up to date ({}).".format(gz_path))
    else:
        print("Downloading {} -> {}".format(DBLP_XML_URL, gz_path))
        fetch_to_file(DBLP_XML_URL, gz_path)
        got_md5 = md5sum(gz_path)
        if got_md5 != want_md5:
            os.remove(gz_path)
            sys.exit(
                "Checksum mismatch for dblp.xml.gz (expected {}, got {}); download removed, try again.".format(
                    want_md5, got_md5
                )
            )
        print("Checksum OK.")

    print("Downloading {} -> {}".format(DBLP_DTD_URL, dtd_path))
    fetch_to_file(DBLP_DTD_URL, dtd_path)

    print("Done. Dump ready in {}".format(args.dir))


if __name__ == "__main__":
    main()
