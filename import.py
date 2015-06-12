#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# TODO
# - manage correctly tags inside tags ! (xml.etree.ElementTree.tostringlist(...)

from __future__ import print_function

import sys
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import xml.etree.ElementTree
from xml.etree import ElementTree
from xml.etree.ElementTree import XML
import urllib2
import re
import time
import sys
import unicodedata
import logging
import logging_colorer
from unidecode import unidecode
from string import Template
import os.path
import argparse
import subprocess
import HTMLParser

from config import *

logging.basicConfig(level=logging.DEBUG)

# Remove accents
# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents(s):
    return unidecode(s)
    #return ''.join((c for c in unicodedata.normalize('NFD', unicode(s)) if unicodedata.category(c) != 'Mn'))

# Translation table from UTF8 to pure latex symbols
# http://stackoverflow.com/questions/4578912/replace-all-accented-characters-by-their-latex-equivalent
translation_table = {}
for line in open('utf8ienc.dtx'):
    m = re.match(r'%.*\DeclareUnicodeCharacter\{(\w+)\}\{(.*)\}', line)
    if m:
        codepoint, latex = m.groups()
        latex = latex.replace('@tabacckludge', '') # remove useless (??) '@tabacckludge'
        translation_table[int(codepoint, 16)] = "{"+unicode(latex)+"}"

def unicode_to_latex(s):
    """ transform a unicode string to a ascii string with latex symbols """
    s = unicode(s).translate(translation_table)
    s = s.replace(u"\x96", u"---")
    s = s.replace(u"\u200e", u"")
    s = s.replace(u"\x92", u"'")
    s = s.replace(u"\x93", u"``")
    s = s.replace(u"\x94", u"''")
    s = s.replace(u"\u03a3", u"$\Sigma$")
    s = s.replace(u"z\u030c", u"{\v{z}}")
    return s

def get_url(url, exit_on_failure=True, encoding="utf-8"):
    """ return the content of the url (in unicode) """
    waitsec = 60
    while True:
        try:
            f = urllib2.urlopen(url)
            content = f.read().decode(encoding)
            return content
        except urllib2.HTTPError, e:
            if e.code == 429:
                logging.warning("Error 429 on URL: \"{}\"\n\tReason: {}\n\tWait {}s".format(url, e.reason, waitsec))
                time.sleep(waitsec)
                waitsec *= 2
            elif exit_on_failure:
                logging.exception("Error {} on URL: \"{}\"".format(e.code, url))
                sys.exit(1)

def split_authors(s):
    """ return a list of others from an author string from EPRINT - from eprint-update.py """
    names = re.split('( and |,  ?and|, )', s);
    nn = []
    for i,n in enumerate(names):
        if i % 2 == 0:
            nn.append(n.strip())
    return nn

def make_brackets_balanced(s):
    """ balance the brackets - from eprint-update.py """
    level = 0
    delete = []
    for i in range(len(s)):
        if s[i] == '{':
            level += 1
        elif s[i] == '}': 
            if level == 0:
                delete.append(i)
            else:
                level -= 1

    o = 0
    for d in delete:
        s = s[0:d+o] + s[d+o+1:]
        o -= 1

    return s + '}' * level


def clean_author(author):
    """ clean author name given by DBLP (remove last numbers if multiple authors) """
    if author.split(" ")[-1].isdigit():
        return u" ".join(author.split(" ")[:-1])
    else:
        return author

def get_author_name(author):
    """ return the author last name """
    # TODO: this is not always OK, we should use pybtex.Person...
    return author.split(" ")[-1]

def authors_to_key(authors, confkey, short_year):
    """ return the author bibtext key part """
    if len(authors) <= 0:
        logging.error("Entry with no author => replaced by ???")
        return confkey + ":" + "???" + str(short_year)
    elif len(authors)==1:
        return confkey + ":" + strip_accents(get_author_name(authors[0])) + str(short_year)
    elif len(authors)<=3:
        return confkey + ":" + "".join((get_author_name(strip_accents(a))[:3] for a in authors)) + str(short_year)
    else:
        if len(authors)>=6:
            authors = authors[:6]
        return confkey + ":" + "".join((get_author_name(strip_accents(a))[0] for a in authors)) + str(short_year)

pattern_white_car = re.compile(r'(\W+)')
pattern_normal_case =       re.compile(r'^(\W*|[0-9_]+|[a-z0-9_]|[A-Za-z0-9_][a-z_]+)$')
pattern_normal_case_first = re.compile(r'^(\W*|[0-9_]+|[A-Za-z0-9_]|[A-Za-z0-9_][a-z_]+)$')

html_parser = HTMLParser.HTMLParser()

def html_to_bib_value(s,title=False):
    """ transform an xml string into a bib value (add {,}, transform html tags, ...) """
    if title:
        s = pattern_white_car.split(s)
        for i in range(len(s)):
            if i==0:
                if not pattern_normal_case_first.search(s[i]):
                    s[i] = "{" + s[i] + "}"
            else:
                if not pattern_normal_case.search(s[i]):
                    s[i] = "{" + s[i] + "}"
        s = "".join(s)
    s = unicode_to_latex(s.replace(' "',"``").replace('"',"''"))
    if s.isdigit():
        return s
    else:
        return '"' + s + '"'

def xml_get_value(e):
    """ get the value of the tag "e" (including subtags) """
    return (e.text or '') + ''.join(xml.etree.ElementTree.tostring(ee) for ee in e)

re_pages = re.compile(r'^(\d*)(-(\d*))?$')

def xml_to_entry(xml, confkey, entry_type, fields, short_year):
    """ transform a DBLP xml entry of type "entry_type" into a dictionnary ready to be output as bibtex """
    try:
        tree = XML(xml)
    except ElementTree.ParseError, e:
        logging.exception("XML Parsing Error")
        return None, None
    elt = tree.find(entry_type.lower())
    if elt is None:
        logging.warning('Entry type is not "{0}"'.format(entry_type))
        return None, None

    entry = {}
    authors = []
    pages_error = None
    for e in elt:
        if e.tag == "author":
            authors.append(clean_author(unicode(e.text)))
        elif e.tag in fields:
            val = xml_get_value(e)#e.text
            if e.tag == "pages":
                r = re_pages.match(val)
                if r==None:
                    pages_error = val
                else:
                    a = r.group(1)
                    b = r.group(2)
                    c = r.group(3)
                    if a=="" or (b!=None and c==""):
                        pages_error = val
                    if b==None:
                        val = a
                    else:
                        val = a + "--" + c
            elif e.tag == "title":
                if val[-1]==".":
                    val = val[:-1]
            entry[e.tag] = html_to_bib_value(val, title = (e.tag == "title"))
        if e.tag == "ee" and "doi" in fields:
            doi_ee_url = "http://dx.doi.org/"
            if e.text.startswith(doi_ee_url):
                if "doi" not in entry:
                    entry["doi"] = html_to_bib_value(e.text[len(doi_ee_url):])

    entry["author"] = html_to_bib_value((u" and \n"+" "*18).join(authors))
    key = authors_to_key(authors, confkey, short_year)
    
    if pages_error != None:
        logging.error("Entry \"{}\": error in pages (\"{}\")".format(key, pages_error))

    return (key, entry)

def write_entry(f, key, entry, entry_type):
    """ write the bibtex entry "entry" with key "key" in file "f" """
    def key_sort(key):
        if key in first_keys:
            return "{0:03d}:{1}".format(first_keys.index(key),key)
        else:
            return "{0:03d}:{1}".format(len(first_keys),key)
    try:
        f.write("@{0}{{{1},\n".format(entry_type, key))
        for k in sorted(entry.iterkeys(), key=key_sort):
            v = entry[k]
            try:
                venc = v.encode("ascii")
            except UnicodeEncodeError, ex:
                logging.warning("Problem of encoding in entry \"{0}\", key \"{1}\", value \"{2}\" -> replace bad caracter(s) with '?'".format(key,k,repr(v)))
                venc = v.encode("ascii", "replace")
            if ("<" in venc) or (">" in venc) or ("&" in venc):
                logging.warning("Caracter <, >, or & in entry \"{0}\", key \"{1}\", value \"{2}\"".format(key,k,repr(v)))
            f.write("  {0:<15}{1},\n".format((k + " ="), venc))
        f.write("}\n\n")
    except UnicodeEncodeError, ex:
        logging.exception("Problem of encoding of:\n" + repr((key,entry)))

def can_write(filename, overwrite = False):
    """ check whether we can write to the file (ask the user if overwrite=False and the file already exists) """
    if overwrite == False and os.path.exists(filename):
        print("File \"{0}\" already exists. Do you want to delete it (Y/N) ?".format(filename))
        rep = ""
        while rep.lower() not in ["y","n","yes","no"]:
            rep = raw_input()
        if rep.lower()[0]!="y":
            return False
    return True

def run(confkey, year, dis, overwrite=False):
    """ overwrite: if True, overwrite files """

    short_year = "{0:02d}".format(year % 100)
    if year < 2000:
        url_year = short_year
    else:
        url_year = year
    conf_dict = confs[confkey]
    if conf_dict["type"] == "journal":
        volume = year - conf_dict["first_year"] + 1
    else:
        volume = None

    def subs(s):
        """ replace ${...} in confs information """
        return Template(s).substitute(
            year = year,
            confkey = confkey,
            short_year = short_year,
            url_year = url_year,
            volume = volume,
            dis = dis
        )

    entry_type = conf_dict["entry_type"]
    fields_dblp = conf_dict["fields_dblp"]
    fields_add = dict(((key, subs(value)) for key, value in conf_dict["fields_add"].iteritems()))


    if conf_dict["type"] == "misc":
        encoding = "iso-8859-1"
    else:
        encoding = "utf-8"

    html_conf = None
    for url in confs[confkey]["url"]:
        logging.info("Parse: <{}>".format(subs(url)))
        html_conf = get_url(subs(url), False, encoding = encoding)
        if html_conf != None:
            break
    if html_conf == None:
        logging.exception("No valid URL")
        sys.exit(1)
    entries = {}
    multiple_entries = {}

    # retrieve entries
    if conf_dict["type"] == "misc":
        # EPRINT
        for pub in reversed(list(re.finditer('^<a href="[^"]*">([0-9]{4})/([0-9]{3,})</a>.*\n<dd><b>(.*?)</b>\n<dd><em>(.*?)</em>$', html_conf, re.MULTILINE))) :
            # reversed = to have the a/b/c in the correct order
            entry = {}
            entry["year"] = pub.group(1)
            eprint_id = pub.group(2)
            entry["title"] = html_to_bib_value(
                make_brackets_balanced(html_parser.unescape(pub.group(3))), 
                True
            )
            authors = split_authors(html_parser.unescape(pub.group(4)))

            entry["howpublished"] = '"Cryptology ePrint Archive, Report {}/{}"'.format(entry["year"], eprint_id)
            entry["note"] = '"\url{{http://eprint.iacr.org/{}/{}}}"'.format(entry["year"], eprint_id)
            entry["author"] = html_to_bib_value((u" and \n"+" "*18).join(authors))
            key = authors_to_key(authors, confkey, short_year)

            if key in entries:
                multiple_entries[key] = 1
                entries[key + "a"] = entries[key]
                del entries[key]

            if key in multiple_entries:
                i = multiple_entries[key]
                multiple_entries[key]+=1
                entries[key+chr(ord('a')+i)] = entry
            else:
                entries[key] = entry
    else:
        # DBLP
        for pub in re.finditer(r'href="(http://dblp.uni-trier.de/rec/(?:bibtex|xml)/(?:conf|journals)/[^"]*.xml)"', html_conf):
            url_pub = pub.group(1)
            logging.info("Parse: <{}>".format(url_pub))
            xml = get_url(url_pub)
            key, entry = xml_to_entry(xml, confkey, entry_type, fields_dblp, short_year)

            if key==None:
                continue

            if key in entries:
                multiple_entries[key] = 1
                entries[key + "a"] = entries[key]
                del entries[key]

            if key in multiple_entries:
                i = multiple_entries[key]
                multiple_entries[key]+=1
                entries[key+chr(ord('a')+i)] = entry
            else:
                entries[key] = entry

    # write result !
    filename = "{}{}{}.bib".format(confkey, short_year, dis)
    logging.info("Write \"{0}\"".format(filename))
    if not can_write(filename, overwrite):
        return
    f = file(filename, "w")
    def sort_pages((k,e)):
        if "howpublished" in e:
            howpublished = e["howpublished"]
        else:
            howpublished = ""
        if "number" in e:
            num = 99999-int(e["number"])
        else:
            num = 0
        if "pages" in e:
            if e["pages"].isdigit():
                pages = int(e["pages"])
            else:
                pages = int(e["pages"][1:-1].split("--")[0])
        else:
            pages = 0
        return "{:0>5d}-{:0>10d}-{}".format(num, pages, howpublished)
    for (key,e) in sorted(entries.iteritems(), key=sort_pages):
        fields_add_cur = fields_add.copy()
        if "month" in fields_add_cur and fields_add_cur["month"]=="%months":
            fields_add_cur["month"] = conf_dict["months"][int(e["number"]) - 1]
        write_entry(f, key, dict(fields_add_cur, **e), entry_type)
    f.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", dest="overwrite", action="store_true", help="overwrite existing files")
    parser.add_argument("-e", "--extract-bib", metavar="database.bib", dest="extract_bib", default=[], action="append", type=str, help="extract the conference from the provided bibfile in confyear_extract_database.bib")
    parser.add_argument("-c", "--clean", dest="clean", action="store_true", help="output clean version _clean.bib of all bib files")
    parser.add_argument("confyears", metavar="confyear", type=str, help="list of conferences (ex.: C2012 ac11 stoc95 c2013-1)", nargs="*")
    args = parser.parse_args()

    for conf_year in args.confyears:
        res = re.search(r'^([a-zA-Z]+)([0-9]{2,4})([a-zA-A0-9_-]*)$', conf_year)
        if res == None:
            logging.error("bad format for conference \"{0}\" (ex.: crypto2012 crypto11 stoc95 crypto13-1)".format(conf_year))
            sys.exit(1)
        confkey = res.group(1).upper()
        year = int(res.group(2))
        dis = res.group(3)
        if year < 50:
            year += 2000
        elif year < 100:
            year += 1900
        short_year = "{0:02d}".format(year % 100)

        run(confkey, year, dis, overwrite = args.overwrite)

        for ext in args.extract_bib:
            filename = "{0}{1}_extract_{2}".format(confkey, short_year, os.path.basename(ext))
            logging.info("Write \"{0}\"".format(filename))
            if not can_write(filename, args.overwrite):
                continue
            f = file(filename, "w")
            cmd = ["./clean_bib.sh", ext, confkey, short_year]
            logging.info("run: ")
            subprocess.call(cmd, stdout=f)
            f.close()

        if args.clean:
            for name, fields in fields_add.iteritems():
                filename = "{0}{1}_{2}_clean.bib".format(confkey, short_year, name)
                logging.info("Write \"{0}\"".format(filename))
                if not can_write(filename, args.overwrite):
                    continue
                f = file(filename, "w")
                subprocess.call(["./clean_bib.sh", "{0}{1}_{2}.bib".format(confkey, short_year, name)], stdout=f)
                f.close()

if __name__ == "__main__":
    main()
