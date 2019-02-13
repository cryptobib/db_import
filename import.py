#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# TODO
# - manage correctly tags inside tags ! (xml.etree.ElementTree.tostringlist(...)

# Parts of this file come from eprint-update.py from Paul Baecher

from __future__ import print_function

import os
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
import logging
import logging_colorer
from unidecode import unidecode
import os.path
import argparse
import HTMLParser

from config import *

logging_colorer.init()
logging.basicConfig(level=logging.DEBUG)

# Fix for authors names (used by `get_author_name_and_for_key`)

# A dictionary of regex to fix authors names
# If the author matches the key, 
#   if the value is a string, it is replaced by it
#   otherwise, the value is a pair of two strings
#      the author is then replaced by the first part of the pair
#      and the second part of the pair is the last name used for the BibTeX key
author_subs_re = {
    ur"Shekh Faisal Abdul-Latip": (ur"Shekh Faisal {Abdul-Latip}", ur"Abdul-Latip"),
    ur"Ruba Abu-Salma": (ur"Ruba {Abu-Salma}", ur"Abu-Salma"),
    ur"Carlos Aguilar Melchor": (ur"Carlos {Aguilar Melchor}", ur"AguilarMelchor"),
    ur"Mahdi Nasrullah Al-Ameen": (ur"Mahdi Nasrullah {Al-Ameen}", ur"Al-Ameen"),
    ur"Sultan Al-Hinai": (ur"Sultan {Al-Hinai}", ur"Al-Hinai"),
    ur"Mohamed Al-Ibrahim": (ur"Mohamed {Al-Ibrahim}", ur"Al-Ibrahim"),
    ur"Naser Al-Ibrahim": (ur"Naser {Al-Ibrahim}", ur"Al-Ibrahim"),
    ur"Noor R. Al-Kazaz": (ur"Noor R. {Al-Kazaz}", ur"Al-Kazaz"),
    ur"Zakaria Al-Qudah": (ur"Zakaria {Al-Qudah}", ur"Al-Qudah"),
    ur"Sattam S. Al-Riyami": (ur"Sattam S. {Al-Riyami}", ur"Al-Riyami"),
    ur"Ehab Al-Shaer": (ur"Ehab {Al-Shaer}", ur"Al-Shaer"),
    ur"Said F. Al-Sarawi": (ur"Said F. {Al-Sarawi}", ur"Al-Sarawi"),
    ur"Jacob Alperin-Sheriff": (ur"Jacob {Alperin-Sheriff}", ur"Alperin-Sheriff"),
    ur"Enrique Argones-R[úu]a": (ur"Enrique {Argones-R{\'u}a}", ur"Argones-Rua"),
    ur"Babak Azimi-Sadjadi": (ur"Babak {Azimi-Sadjadi}", ur"Azimi-Sadjadi"),

    ur"Achiya Bar-On": (ur"Achiya {Bar-On}", ur"Bar-On"),
    ur"Ahmad Baraani-Dastjerdi": (ur"Ahmad {Baraani-Dastjerdi}", ur"Baraani-Dastjerdi"),
    ur"Emmanuel Bello-Ogunu": (ur"Emmanuel {Bello-Ogunu}", ur"Bello-Ogunu"),
    ur"Ishai Ben-Aroya": (ur"Ishai {Ben-Aroya}", ur"Ben-Aroya"),
    ur"Assaf Ben-David": (ur"Assaf {Ben-David}", ur"Ben-David"),
    ur"Shalev Ben-David": (ur"Shalev {Ben-David}", ur"Ben-David"),
    ur"Aner Ben-Efraim": (ur"Aner {Ben-Efraim}", ur"Ben-Efraim"),
    ur"Omri Ben-Eliezer": (ur"Omri {Ben-Eliezer}", ur"Ben-Eliezer"),
    ur"Michael Ben-Or": (ur"Michael {Ben-Or}", ur"Ben-Or"),
    ur"Eli Ben-Sasson": (ur"Eli {Ben-Sasson}", ur"Ben-Sasson"),
    ur"Adi Ben-Zvi": (ur"Adi {Ben-Zvi}", ur"Ben-Zvi"),
    ur"Imane Bouij-Pasquier": (ur"Imane {Bouij-Pasquier}", ur"Bouij-Pasquier"),
    ur"Nora Boulahia-Cuppens": (ur"Nora {Boulahia-Cuppens}", ur"Boulahia-Cuppens"),
    ur"Cristian Bravo-Lillo": (ur"Cristian {Bravo-Lillo}", ur"Bravo-Lillo"),
    ur"Geeke Bruin-Muurling": (ur"Geeke {Bruin-Muurling}", ur"Bruin-Muurling"),

    ur"C. Caballero-Gil": (ur"C{\'a}ndido {Caballero-Gil}", ur"Caballero-Gil"),
    ur"C[áa]ndido Caballero-Gil": (ur"C{\'a}ndido {Caballero-Gil}", ur"Caballero-Gil"),
    ur"Pino Caballero-Gil": (ur"Pino {Caballero-Gil}", ur"Caballero-Gil"),
    ur"C[ée]cile Canovas-Dumas": (ur"C{\'e}cile {Canovas-Dumas}", ur"Canovas-Dumas"),
    ur"Daniel Cervantes-V[áa]zquez": (ur"Daniel {Cervantes-V{\'a}zquez}", ur"Cervantes-Vazquez"),
    ur"Eric Chan-Tin": (ur"Eric {Chan-Tin}", ur"Chan-Tin"),
    ur"Beno[îi]t Chevallier-Mames": (ur"Beno{\^\i}t {Chevallier-Mames}", ur"Chevallier-Mames"),
    ur"Jes[úu]s-Javier Chi-Dom[íi]nguez": (ur"Jes{\'u}s-Javier {Chi-Dom{\'\i}nguez}", ur"Chi-Dominguez"),
    ur"Vincent Cohen-Addad": (ur"Vincent {Cohen-Addad}", ur"Cohen-Addad"),
    ur"Katriel Cohn-Gordon": (ur"Katriel {Cohn-Gordon}", ur"Cohn-Gordon"),
    ur"[ÉE]ric Colin de Verdi[èe]re": (ur"{\'E}ric {Colin de Verdi{\`e}re}", ur"ColindeVerdiere"),
    ur"Hubert Comon-Lundh": (ur"Hubert {Comon-Lundh}", ur"Comon-Lundh"),
    ur"Henry Corrigan-Gibbs": (ur"Henry {Corrigan-Gibbs}", ur"Corrigan-Gibbs"),
    ur"Nora Cuppens-Boulahia": (ur"Nora {Cuppens-Boulahia}", ur"Cuppens-Boulahia"),

    ur"Dana Dachman-Soled": (ur"Dana {Dachman-Soled}", ur"Dachman-Soled"),
    ur"Paolo D'Arco": (ur"Paolo {D'Arco}", ur"DArco"),
    ur"Christophe [dD]e Canni[èe]re": (ur"Christophe {De Canni{\`e}re}", ur"DeCanniere"),
    ur"Sabrina [dD]e Capitani [dD]i Vimercati": (ur"Sabrina {De Capitani di Vimercati}", ur"DeCapitanidiVimercati"),
    ur"Angelo [dD]e Caro": (ur"Angelo {De Caro}", ur"DeCaro"),
    ur" Jean-Lou [Dd]e Carufel": (ur" Jean-Lou {De Carufel}", ur"DeCarufel"),
    ur"Emiliano [Dd]e Cristofaro": (ur"Emiliano {De Cristofaro}", ur"DeCristofaro"),
    ur"Guerric Meurice [dD]e Dormale": (ur"Guerric Meurice {de Dormale}", ur"deDormale"),
    ur"Luca [dD]e Feo": (ur"Luca {De Feo}", ur"DeFeo"),
    ur"Peter [Dd]e Gersem": (ur"Peter {De Gersem}", ur"DeGersem"),
    ur"Wiebren [dD]e Jonge": (ur"Wiebren {de Jonge}", ur"deJonge"),
    ur"Roberto [dD]e Prisco": (ur"Roberto {De Prisco}", ur"DePrisco"),
    ur"Alfredo [dD]e Santis": (ur"Alfredo {De Santis}", ur"DeSantis"),
    ur"Fabrizio [Dd]e Santis": (ur"Fabrizio {De Santis}", ur"DeSantis"),
    ur"Domenico [Dd]e Seta": (ur"Domenico {De Seta}", ur"DeSeta"),
    ur"Marijke [Dd]e Soete": (ur"Marijke {De Soete}", ur"DeSoete"),
    ur"Lorenzo [Dd]e Stefani": (ur"Lorenzo {De Stefani}", ur"DeStefani"),
    ur"Dominique [dD]e Waleffe": (ur"Dominique {de Waleffe}", ur"deWaleffe"),
    ur"Erik [Dd]e Win": (ur"Erik {De Win}", ur"DeWin"),
    ur"Thomas Debris-Alazard": (ur"Thomas {Debris-Alazard}", ur"Debris-Alazard"),
    ur"Martin Dehnel-Wild": (ur"Martin {Dehnel-Wild}", ur"Dehnel-Wild"),
    ur"Rafa[ëe]l del Pino": (ur"Rafa{\"e}l {del Pino}", ur"delPino"),
    ur"Romar B. dela Cruz": (ur"Romar B. {dela Cruz}", ur"delaCruz"),
    ur"Antoine Delignat-Lavaud": (ur"Antoine {Delignat-Lavaud}", ur"Delignat-Lavaud"),
    ur"Sergi Delgado-Segura": (ur"Sergi {Delgado-Segura}", ur"Delgado-Segura"),
    ur"Bert [dD]en Boer": (ur"Bert {den Boer}", ur"denBoer"),
    ur"Giovanni [dD]i Crescenzo": (ur"Giovanni {Di Crescenzo}", ur"DiCrescenzo"),
    ur"Roberto [dD]i Pietro": (ur"Roberto {Di Pietro}", ur"DiPietro"),
    ur"Mario [dD]i Raimondo": (ur"Mario {Di Raimondo}", ur"DiRaimondo"),
    ur"Jerome Di-Battista": (ur"Jerome {Di-Battista}", ur"Di-Battista"),
    ur"Guilherme [Dd]ias da Fonseca": (ur"Guilherme {Dias da Fonseca}", ur"DiasdaFonseca"),
    ur"Jes[úu]s E. D[íi]az-Verdejo": (ur"Jes{\'u}s E. {D{\'\i}az-Verdejo}", ur"Diaz-Verdejo"),
    ur"Brendan Dolan-Gavitt": (ur"Brendan {Dolan-Gavitt}", ur"Dolan-Gavitt"),
    ur"Daniel Ricardo [dD]os Santos": (ur"Daniel Ricardo {Dos Santos}", ur"DosSantos"),
    ur"Josep Domingo-Ferrer": (ur"Josep {Domingo-Ferrer}", ur"Domingo-Ferrer"),
    ur"Dana Drachsler-Cohen": (ur"Dana {Drachsler-Cohen}", ur"Drachsler-Cohen"),
    ur"Edouard Dufour Sans": (ur"Edouard {Dufour Sans}", ur"DufourSans"),

    ur"Karim El Defrawy": (ur"Karim {El Defrawy}", ur"ElDefrawy"),
    ur"Anas Abou El Kalam": (ur"Anas Abou {El Kalam}", ur"ElKalam"),
    ur"Philippe Elbaz-Vincent": (ur"Philippe {Elbaz-Vincent}", ur"Elbaz-Vincent"),
    ur"R. Marije Elkenbracht-Huizin": (ur"R. Marije {Elkenbracht-Huizin}", ur"Elkenbracht-Huizin"),

    ur"Martin Farach-Colton": (ur"Martin {Farach-Colton}", ur"Farach-Colton"),
    ur"Armando Faz-Hern[áa]ndez": (ur"Armando {Faz-Hern{\'a}ndez}", ur"Faz-Hernandez"),
    ur"Eduardo Fern[áa]ndez-Medina": (ur"Eduardo {Fern{\'a}ndez-Medina}", ur"Fernandez-Medina"),
    ur"Josep Llu[íi]s Ferrer-Gomila": (ur"Josep Llu{\'\i}s {Ferrer-Gomila}", ur"Ferrer-Gomila"),
    ur"Jonathan Fetter-Degges": (ur"Jonathan {Fetter-Degges}", ur"Fetter-Degges"),
    ur"Eli Fox-Epstein": (ur"Eli {Fox-Epstein}", ur"Fox-Epstein"),
    ur"Amparo F[úu]ster-Sabater": (ur"Amparo {F{\'u}ster-Sabater}", ur"Fuster-Sabater"),

    ur"Emilio Jes[úu]s Gallego Arias": (ur"Emilio Jes{\'u}s {Gallego Arias}", ur"GallegoArias"),
    ur"Joaqu[íi]n Garc[íi]a-Alfaro": (ur"Joaqu{\'\i}n {Garc{\'\i}a-Alfaro}", ur"Garcia-Alfaro"),
    ur"Joan Garc[íi]a-Haro": (ur"Joan {Garc{\'\i}a-Haro}", ur"Garcia-Haro"),
    ur"H. Garc[íi]a-Molina": (ur"H{\'e}ctor {Garc{\'\i}a-Molina}", ur"Garcia-Molina"),
    ur"H[ée]ctor Garc[íi]a-Molina": (ur"H{\'e}ctor {Garc{\'\i}a-Molina}", ur"Garcia-Molina"),
    ur"[ÓO]scar Garc[íi]a-Morch[óo]n": (ur"{\'O}scar {Garc{\'\i}a-Morch{\'o}n}", ur"Garcia-Morchon"),
    ur"Francisco Javier Garc[íi]a-Salom[óo]n": (ur"Francisco Javier {Garc{\'\i}a-Salom{\'o}n}", ur"Garcia-Salomon"),
    ur"Pedro Garc[íi]a-Teodoro": (ur"Pedro {Garc{\'\i}a-Teodoro}", ur"Garcia-Teodoro"),
    ur"Domingo G[óo]mez-P[ée]rez": (ur"Domingo {G{\'o}mez-P{\'e}rez}", ur"Gomez-Perez"),
    ur"Antonio F. G[óo]mez-Skarmeta": (ur"Antonio F. {G{\'o}mez-Skarmeta}", ur"Gomez-Skarmeta"),
    ur"Mar[ií]a Isabel Gonz[aá]lez Vasco": (ur"Mar{\'\i}a Isabel {Gonz{\'a}lez Vasco}", ur"GonzalezVasco"),
    ur"Juan Gonz[áa]lez Nieto": (ur"Juan Manuel {Gonz{\\'a}lez Nieto}", ur"GonzalezNieto"),
    ur"Juan Manuel Gonz[aá]lez Nieto": (ur"Juan Manuel {Gonz{\\'a}lez Nieto}", ur"GonzalezNieto"),
    ur"Juanma Gonz[áa]lez Nieto": (ur"Juan Manuel {Gonz{\\'a}lez Nieto}", ur"GonzalezNieto"),
    ur"Ana Gonz[áa]lez-Marcos": (ur"Ana {Gonz{\'a}lez-Marcos}", ur"Gonzalez-Marcos"),
    ur"Raouf N. Gorgui-Naguib": (ur"Raouf N. {Gorgui-Naguib}", ur"Gorgui-Naguib"),

    ur"Sariel Har-Peled": (ur"Sariel {Har-Peled}", ur"Har-Peled"),
    ur"Julio Cesar Hernandez-Castro": (ur"Julio Cesar {Hernandez-Castro}", ur"Hernandez-Castro"),
    ur"Candelaria Hern[áa]ndez-Goya": (ur"Candelaria {Hern{\'a}ndez-Goya}", ur"Hernandez-Goya"),
    ur"Jordi Herrera-Joancomart[íi]": (ur"Jordi {Herrera-Joancomart{\'\i}}", ur"Herrera-Joancomarti"),
    ur"Thomas S. Heydt-Benjamin": (ur"Thomas S. {Heydt-Benjamin}", ur"Heydt-Benjamin"),
    ur"Severin Holzer-Graf": (ur"Severin {Holzer-Graf}", ur"Holzer-Graf"),
    ur"Nick Howgrave-Graham": (ur"Nick {Howgrave-Graham}", ur"Howgrave-Graham"),
    ur"Dimitrios Hristu-Varsakelis": (ur"Dimitrios {Hristu-Varsakelis}", ur"Hristu-Varsakelis"),

    ur"Luis Irun-Briz": (ur"Luis {Irun-Briz}", ur"Irun-Briz"),

    ur"M. J. Jacobson Jr.": (ur"Michael J. {Jacobson Jr.}", ur"JacobsonJr"),
    ur"Michael J. Jacobson Jr.": (ur"Michael J. {Jacobson Jr.}", ur"JacobsonJr"),

    ur"Burton S. Kaliski Jr.": (ur"Burton S. {Kaliski Jr.}", ur"KaliskiJr"),
    ur"S[áa]ndor Kisfaludi-Bak": (ur"S{\'a}ndor {Kisfaludi-Bak}", ur"Kisfaludi-Bak"),
    ur"Thomas F. Knight Jr.": (ur"Thomas F. {Knight Jr.}", ur"KnightJr"),
    ur"Eleftherios Kokoris-Kogias": (ur"Eleftherios {Kokoris-Kogias}", ur"Kokoris-Kogias"),
    ur"S[ée]bastien Kunz-Jacques": (ur"S{\'e}bastien {Kunz-Jacques}", ur"Kunz-Jacques"),

    ur"Hendrik W. Lenstra Jr.": (ur"Hendrik W. {Lenstra Jr.}", ur"LenstraJr"),
    ur"Adriana L[óo]pez-Alt": (ur"Adriana {L{\'o}pez-Alt}", ur"Lopez-Alt"),

    ur"Gilles Macario-Rat": (ur"Gilles {Macario-Rat}", ur"Macario-Rat"),
    ur"Jaume Mart[íi]-Farr[ée]": (ur"Jaume {Mart{\'\i}-Farr{\'e}}", ur"Marti-Farre"),
    ur"Breno de Medeiros": (ur"{Breno de} Medeiros", ur"Medeiros"),
    ur"Santos Merino [Dd]el Pozo": (ur"Santos {Merino Del Pozo}", ur"MerinoDelPozo"),
    ur"Pedro Moreno-Sanchez": (ur"Pedro {Moreno-Sanchez}", ur"Moreno-Sanchez"),
    ur"William K. Moses Jr.": (ur"William K. {Moses Jr.}", ur"MosesJr"),

    ur"Jorge Nakahara Jr.": (ur"Jorge {Nakahara Jr.}", ur"NakaharaJr"),
    ur"Guillermo Navarro-Arribas": (ur"Guillermo {Navarro-Arribas}", ur"Navarro-Arribas"),
    ur"Mar[ií]a Naya-Plasencia": (ur"Mar{\'\i}a {Naya-Plasencia}", ur"Naya-Plasencia"),
    ur"Cristina Nita-Rotaru": (ur"Cristina {Nita-Rotaru}", ur"Nita-Rotaru"),

    ur"Eduardo Ochoa-Jim[ée]nez": (ur"Eduardo {Ochoa-Jim{\'e}nez}", ur"Ochoa-Jimenez"),

    ur"Anat Paskin-Cherniavsky": (ur"Anat {Paskin-Cherniavsky}", ur"Paskin-Cherniavsky"),
    ur"Beni Paskin-Cherniavsky": (ur"Beni {Paskin-Cherniavsky}", ur"Paskin-Cherniavsky"),
    ur"Magdalena Payeras-Capell[àa]": (ur"Magdalena {Payeras-Capell{\`a}}", ur"Payeras-Capella"),
    ur"Angel L. P[ée]rez [dD]el Pozo": (ur"Angel L. {P{\'e}rez del Pozo}", ur"PerezdelPozo"),
    ur"David P[ée]rez Garc[íi]a": (ur"David {P{\'e}rez Garc{\'\i}a}", ur"PerezGarcia"),
    ur"Cristina P[ée]rez-Sol[àa]": (ur"Cristina {P{\'e}rez-Sol{\`a}}", ur"Perez-Sola"),
    ur"Nick L. Petroni Jr.": (ur"Nick L. {Petroni Jr.}", ur"PetroniJr"),

    ur"Francisco Rodr[íi]guez-Henr[íi]quez": (ur"Francisco {Rodr{\'\i}guez-Henr{\'\i}quez}", ur"Rodriguez-Henriquez"),
    ur"Noga Ron-Zewi": (ur"Noga {Ron-Zewi}", ur"Ron-Zewi"),
    ur"Lloren[çc] Huguet i Rotger": (ur"{Lloren\c{c} Huguet i} Rotger", ur"Rotger"),

    ur"Reihaneh Safavi-Naini": (ur"Reihaneh {Safavi-Naini}", ur"Safavi-Naini"),
    ur"Iskander S[áa]nchez-Rola": (ur"Iskander {S{\'a}nchez-Rola}", ur"Sanchez-Rola"),
    ur"Katja Schmidt-Samoa": (ur"Katja {Schmidt-Samoa}", ur"Schmidt-Samoa"),
    ur"[Aa]bhi [Ss]helat": (ur"{abhi} {shelat}", ur"shelat"),
    ur"Marcos A. Simpl[íi]cio Jr.": (ur"Marcos A. {Simpl{\'\i}cio Jr.}", ur"SimplicioJr"),
    ur"Daniel Smith-Tone": (ur"Daniel {Smith-Tone}", ur"Smith-Tone"),
    ur"Eduardo Soria-Vazquez": (ur"Eduardo {Soria-Vazquez}", ur"Soria-Vazquez"),
    ur"Noah Stephens-Davidowitz": (ur"Noah {Stephens-Davidowitz}", ur"Stephens-Davidowitz"),

    ur"Herman [tT]e Riele": (ur"Herman {te Riele}", ur"teRiele"),
    ur"Nicole Tomczak-Jaegermann": (ur"Nicole {Tomczak-Jaegermann}", ur"Tomczak-Jaegermann"),

    ur"Jeroen [vV]an [dD]e Graaf": (ur"Jeroen {van de Graaf}", ur"vandeGraaf"),
    ur"Tim [vV]an [dD]e Kamp": (ur"Tim {van de Kamp}", ur"vandeKamp"),
    ur"Robbert van den Berg": (ur"Robbert {van den Berg}", ur"vandenBerg"),
    ur"Vincent [vV]an [dD]er Leest": (ur"Vincent {van der Leest}", ur"vanderLeest"),
    ur"Jan C. A. [vV]an [dD]er Lubbe": (ur"Jan C. A. {van der Lubbe}", ur"vanderLubbe"),
    ur"Erik van der Sluis": (ur"Erik {van der Sluis}", ur"vanderSluis"),
    ur"Victor [vV]an [dD]er Veen": (ur"Victor {van der Veen}", ur"vanderVeen"),
    ur"Marten [vV]an Dijk": (ur"Marten {van Dijk}", ur"vanDijk"),
    ur"Matthew [Vv]an Gundy": (ur"Matthew {Van Gundy}", ur"VanGundy"),
    ur"Eug[èe]ne [vV]an Heijst": (ur"Eug{\`e}ne {van Heijst}", ur"vanHeijst"),
    ur"Anthony [Vv]an Herrewege": (ur"Anthony {Van Herrewege}", ur"VanHerrewege"),
    ur"Erik Jan [vV]an Leeuwen": (ur"Erik Jan {van Leeuwen}", ur"vanLeeuwen"),
    ur"Paul C. [Vv]an Oorschot": (ur"Paul C. {van Oorschot}", ur"vanOorschot"),
    ur"Peter [vV]an Rossum": (ur"Peter {van Rossum}", ur"vanRossum"),
    ur"Johan [vV]an Tilburg": (ur"Johan {van Tilburg}", ur"vanTilburg"),
    ur"Nicolas Veyrat-Charvillon": (ur"Nicolas {Veyrat-Charvillon}", ur"Veyrat-Charvillon"),
    ur"Francisco Jos[ée] Vial Prado": (ur"Francisco Jos{\'e} {Vial Prado}", ur"VialPrado"),
    ur"Luis [vV]on Ahn": (ur"Luis {von Ahn}", ur"vonAhn"),

    ur"Samuel S. Wagstaff Jr.": (ur"Samuel S. {Wagstaff Jr.}", ur"WagstaffJr"),
    ur"Ronny Wichers Schreur": (ur"Ronny {Wichers Schreur}", ur"WichersSchreur"),
    ur"Zooko Wilcox-O'Hearn": (ur"Zooko {Wilcox-O'Hearn}", ur"Wilcox-OHearn"),

    ur"Santiago Zanella[- ]B[ée]guelin": (ur"Santiago {Zanella-B{\'e}guelin}", ur"Zanella-Beguelin"),
    ur"Rui Zhang II": (ur"Rui {Zhang II}", ur"ZhangII"),
}

author_subs_re_compiled = {
    re.compile(r): s
    for r, s in author_subs_re.iteritems()
}
author_subs_re_all = re.compile("^" + "|".join(author_subs_re.keys()) + "$")


def get_author_name_for_key(author):
    """ return the author last name for key """
    # TODO: this is not always OK, we should use pybtex.Person...
    last_name = author.split(" ")[-1]
    if last_name == "Jr." and len(author) > 1:
        last_name = "".join(author.split(" ")[-2:])
    # remove "." from the name if any as it is not allowed by pybtex in keys
    return last_name.replace(".", "").replace("{", "").replace("}", "").replace("'", "")


def get_author_name_and_for_key(author):
    """ 
    Return a pair (author, last_name_bibtex) where 
    - name is the cleaned author name using author_subs_re
    - name_for_key is the last name to be used to generate BibTeX keys
      it is either computed using author_subs_re or generated by get_author_name_for_key
    """

    # For efficiency, we first use author_subs_re_all to find the places to
    # replace, but then manually sub
    def get_match(text):
        for r, s in author_subs_re_compiled.iteritems():
            if r.match(text):
                return s

    if author_subs_re_all.match(author):
        s = get_match(author)
        if isinstance(s, basestring):
            return (s, get_author_name_for_key(s))
        else:
            return s
    
    return (author, get_author_name_for_key(author))


# Remove accents
# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents(s):
    return unidecode(s)
    # return ''.join((c for c in unicodedata.normalize('NFD', unicode(s)) if unicodedata.category(c) != 'Mn'))


# Translation table from UTF8 to pure latex symbols
# http://stackoverflow.com/questions/4578912/replace-all-accented-characters-by-their-latex-equivalent
translation_table = {}
for line in open('utf8ienc.dtx'):
    m = re.match(r'%.*\DeclareUnicodeCharacter\{(\w+)\}\{(.*)\}', line)
    if m:
        codepoint, latex = m.groups()
        latex = latex.replace('@tabacckludge', '')  # remove useless (??) '@tabacckludge'
        translation_table[int(codepoint, 16)] = "{" + unicode(latex) + "}"


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
    s = s.replace(u"\u2208", u"$\epsilon$")
    return s


def get_url(url, exit_on_failure=True, encoding="utf-8"):
    """ return the content of the url (in unicode) """
    waitsec = 60
    while True:
        try:
            f = urllib2.urlopen(url)
            content = f.read().decode(encoding)
            return content
        except urllib2.HTTPError as e:
            if e.code == 429:
                logging.warning("Error 429 on URL: \"{}\"\n\tReason: {}\n\tWait {}s".format(url, e.reason, waitsec))
                time.sleep(waitsec)
                waitsec *= 2
            else:
                logging.exception("Error {} on URL: \"{}\"".format(e.code, url))
                if exit_on_failure:
                    sys.exit(1)
                else:
                    return None


pattern_split_authors = re.compile(r'\s+and\s+|,\s+and|,\s+')
pattern_multiple_spaces = re.compile(r' +')


def split_authors(s):
    """ return a list of others from an author string from EPRINT - from eprint-update.py """
    names = pattern_split_authors.split(s)
    names = [n.strip() for n in names]
    return names


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
        s = s[0:d + o] + s[d + o + 1:]
        o -= 1

    return s + '}' * level


def fix_eprint_spaces(s):
    """ fix spaces used by eprint html (multiple spaces instead of just 1) """
    return pattern_multiple_spaces.sub(" ", s)


def clean_author(author):
    """ clean author name given by DBLP (remove last numbers if multiple authors) """
    if author.split(" ")[-1].isdigit():
        return u" ".join(author.split(" ")[:-1])
    else:
        return author


def authors_to_key(authors_last_names, confkey, short_year):
    """ return the author bibtext key part """
    if len(authors_last_names) <= 0:
        logging.error("Entry with no author => replaced by ???")
        return confkey + ":" + "???" + str(short_year)
    elif len(authors_last_names) == 1:
        # the key contains the last name
        return confkey + ":" + strip_accents(authors_last_names[0]) + str(short_year)
    elif len(authors_last_names) <= 3:
        # the key contains the first three letters of each last name
        return confkey + ":" + "".join(strip_accents(a)[:3] for a in authors_last_names) + str(short_year)
    else:
        # the key contains the first letter of the first siz authors
        if len(authors_last_names) >= 6:
            authors = authors_last_names[:6]
        return confkey + ":" + "".join(strip_accents(a)[0] for a in authors_last_names) + str(short_year)


pattern_non_alphanum = re.compile(r'(\W+)')
pattern_normal_case = re.compile(r'^(\W*|[0-9_]+|[a-z0-9_]|[A-Za-z0-9_][a-z_]+)$')
pattern_normal_case_first = re.compile(r'^(\W*|[0-9_]+|[A-Za-z0-9_]|[A-Za-z0-9_][a-z_]+)$')
punctuation_followed_by_upper_case = re.compile(r'^\s*[?!]\s*')
# we do not include "." because it is mostly used with "vs." and "et al."

html_parser = HTMLParser.HTMLParser()


def html_to_bib_value(s, title=False):
    """ transform an xml string into a bib value (add {,}, transform html tags, ...) """
    if title:
        s = pattern_non_alphanum.split(s)
        for i in range(len(s)):
            if i == 0:
                if not pattern_normal_case_first.search(s[i]):
                    s[i] = "{" + s[i] + "}"
            else:
                if not pattern_normal_case.search(s[i]):
                    s[i] = "{" + s[i] + "}"
                elif len(s[i]) > 0 and \
                        punctuation_followed_by_upper_case.search(s[i - 1]) and \
                        s[i][0].isalpha() and s[i][0].isupper():
                    # Protect the first letter after . or ? or !
                    s[i] = "{" + s[i][0] + "}" + s[i][1:]
                elif i == 2 and s[i - 1] in ["(", '"'] and s[i][0].isalpha() and s[i][0].isupper():
                    # Protect the first letter of the first word if the title starts with a parenthesis or a quote
                    # in that case s[0] = "" and s[1] = "("
                    s[i] = "{" + s[i][0] + "}" + s[i][1:]
        s = "".join(s)
    if len(s) > 0 and s[0] == '"':
        s = "``" + s[1:]
    s = unicode_to_latex(s.replace(' "', "``").replace('"', "''"))
    if s.isdigit():
        return s
    else:
        return '"' + s + '"'


def xml_get_value(e):
    """ get the value of the tag "e" (including subtags) """
    return (e.text or '') + ''.join(xml.etree.ElementTree.tostring(ee) for ee in e)


re_pages = re.compile(r'^([0-9:]*)(--?([0-9:]*))?$')  # LIPIcs uses pages of the form "5:1-5:10"


def xml_to_entry(xml, confkey, entry_type, fields, short_year):
    """ transform a DBLP xml entry of type "entry_type" into a dictionnary ready to be output as bibtex """
    try:
        tree = XML(xml)
    except ElementTree.ParseError as e:
        logging.exception("XML Parsing Error")
        return None, None
    elt = tree.find(entry_type.lower())
    if elt is None:
        logging.warning('Entry type is not "{0}"'.format(entry_type))
        return None, None

    entry = {}
    authors = [] # list of pairs (full author name, last name for BibTeX key)
    pages_error = None
    for e in elt:
        if e.tag == "author":
            authors.append(get_author_name_and_for_key(clean_author(unicode(e.text))))
        elif e.tag in fields:
            val = xml_get_value(e)  # e.text
            if e.tag == "pages":
                r = re_pages.match(val)
                if r is None:
                    pages_error = val
                else:
                    a = r.group(1)
                    b = r.group(2)
                    c = r.group(3)
                    if a == "" or (b is not None and c == ""):
                        pages_error = val
                    if b is None:
                        val = a
                    else:
                        val = a + "--" + c
            elif e.tag == "title":
                if val[-1] == ".":
                    val = val[:-1]
            entry[e.tag] = html_to_bib_value(val, title=(e.tag == "title"))
        if e.tag == "ee" and "doi" in fields:
            doi_ee_re = re.compile(r"^https?://(?:(?:dx.)?doi.org|doi.acm.org)/(.*)$")
            p = doi_ee_re.match(e.text)
            if p:
                if "doi" not in entry:
                    entry["doi"] = html_to_bib_value(p.group(1))

    authors_bibtex = [a[0] for a in authors]
    entry["author"] = html_to_bib_value((u" and \n" + " " * 18).join(authors_bibtex))

    authors_last_names = [a[1] for a in authors]
    key = authors_to_key(authors_last_names, confkey, short_year)

    if pages_error is not None:
        logging.error("Entry \"{}\": error in pages (\"{}\")".format(key, pages_error))

    return key, entry


def write_entry(f, key, entry, entry_type):
    """ write the bibtex entry "entry" with key "key" in file "f" """

    def key_sort(key):
        if key in first_keys:
            return "{0:03d}:{1}".format(first_keys.index(key), key)
        else:
            return "{0:03d}:{1}".format(len(first_keys), key)

    try:
        f.write("@{0}{{{1},\n".format(entry_type, key))
        for k in sorted(entry.iterkeys(), key=key_sort):
            v = entry[k]
            try:
                venc = v.encode("ascii")
            except UnicodeEncodeError, ex:
                logging.warning(
                    "Problem of encoding in entry \"{0}\", key \"{1}\", value \"{2}\" -> replace bad caracter(s) with '?'".format(
                        key, k, repr(v)))
                venc = v.encode("ascii", "replace")
            if ("<" in venc) or (">" in venc) or ("&" in venc):
                logging.warning(
                    "Caracter <, >, or & in entry \"{0}\", key \"{1}\", value \"{2}\"".format(key, k, repr(v)))
            f.write("  {0:<15}{1},\n".format((k + " ="), venc))
        f.write("}\n\n")
    except UnicodeEncodeError, ex:
        logging.exception("Problem of encoding of:\n" + repr((key, entry)))


def can_write(filename, overwrite=False):
    """ check whether we can write to the file (ask the user if overwrite=False and the file already exists) """
    if overwrite == False and os.path.exists(filename):
        print("File \"{0}\" already exists. Do you want to delete it (Y/N) ?".format(filename))
        rep = ""
        while rep.lower() not in ["y", "n", "yes", "no"]:
            rep = raw_input()
        if rep.lower()[0] != "y":
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
            year=year,
            confkey=confkey,
            short_year=short_year,
            url_year=url_year,
            volume=volume,
            dis=dis
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
        html_conf = get_url(subs(url), False, encoding=encoding)
        if html_conf is not None:
            break
    if html_conf is None:
        logging.exception("No valid URL")
        sys.exit(1)
    entries = {}
    multiple_entries = {}

    # retrieve entries
    if conf_dict["type"] == "misc":
        # EPRINT
        for pub in reversed(list(
                re.finditer('^<a href="[^"]*">([0-9]{4})/([0-9]{3,})</a>.*\n<dd><b>(.*?)</b>\n<dd><em>(.*?)</em>$',
                            html_conf, re.MULTILINE))):
            # reversed = to have the a/b/c in the correct order
            entry = {"year": pub.group(1)}
            eprint_id = pub.group(2)
            entry["title"] = html_to_bib_value(
                make_brackets_balanced(fix_eprint_spaces(html_parser.unescape(pub.group(3)))),
                True
            )
            authors = split_authors(fix_eprint_spaces(html_parser.unescape(pub.group(4))))

            entry["howpublished"] = '"Cryptology ePrint Archive, Report {}/{}"'.format(entry["year"], eprint_id)
            entry["note"] = '"\url{{https://eprint.iacr.org/{}/{}}}"'.format(entry["year"], eprint_id)
            entry["author"] = html_to_bib_value((u" and \n" + " " * 18).join(authors))
            key = authors_to_key(authors, confkey, short_year)

            if key in entries:
                multiple_entries[key] = 1
                entries[key + "a"] = entries[key]
                del entries[key]

            if key in multiple_entries:
                i = multiple_entries[key]
                multiple_entries[key] += 1
                entries[key + chr(ord('a') + i)] = entry
            else:
                entries[key] = entry
    else:
        # DBLP
        for pub in re.finditer(r'href="(https://dblp.uni-trier.de/rec/(?:bibtex|xml)/(?:conf|journals)/[^"]*.xml)"',
                               html_conf):
            url_pub = pub.group(1)
            logging.info("Parse: <{}>".format(url_pub))
            xml = get_url(url_pub)
            key, entry = xml_to_entry(xml, confkey, entry_type, fields_dblp, short_year)

            if key is None:
                continue

            if key in entries:
                multiple_entries[key] = 1
                entries[key + "a"] = entries[key]
                del entries[key]

            if key in multiple_entries:
                i = multiple_entries[key]
                multiple_entries[key] += 1
                entries[key + chr(ord('a') + i)] = entry
            else:
                entries[key] = entry

    # write result !
    filename = "{}{}{}.bib".format(confkey, short_year, dis)
    logging.info("Write \"{0}\"".format(filename))
    if not can_write(filename, overwrite):
        return
    f = file(filename, "w")

    pattern_eprint = re.compile(r"^\"Cryptology ePrint Archive, Report (\d*)/(\d*)\"")

    def sort_pages((k, e)):
        if "howpublished" in e:
            howpublished = e["howpublished"]

            match_eprint = pattern_eprint.match(e["howpublished"])
            if match_eprint:
                # special case for eprint:
                # we cannot use directly howpublished for eprint because of eprint number > 1000
                # as the format is "Cryptology ePrint Archive, Report yyyy/xxx"
                howpublished = u"{:0>4d}/{:0>5d}".format(
                    int(match_eprint.group(1)),
                    int(match_eprint.group(2))
                )
        else:
            howpublished = ""
        if "number" in e:
            num = 99999 - int(e["number"])
        else:
            num = 0
        if "pages" in e:
            if e["pages"].isdigit():
                pages = e["pages"]
            else:
                pages = e["pages"][1:-1].split("--")[0]
        else:
            pages = "0"
        return "{:0>5d}-{:>10}-{}".format(num, pages, howpublished)

    for (key, e) in sorted(entries.iteritems(), key=sort_pages):
        fields_add_cur = fields_add.copy()
        if "month" in fields_add_cur and fields_add_cur["month"] == "%months":
            fields_add_cur["month"] = conf_dict["months"][int(e["number"]) - 1]
        write_entry(f, key, dict(fields_add_cur, **e), entry_type)
    f.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", dest="overwrite", action="store_true", help="overwrite existing files")
    parser.add_argument("confyears", metavar="confyear", type=str,
                        help="list of conferences (ex.: C2012 ac11 stoc95 c2013-1)", nargs="*")
    args = parser.parse_args()

    for conf_year in args.confyears:
        res = re.search(r'^([a-zA-Z]+)([0-9]{2,4})([a-zA-Z0-9_-]*)$', conf_year)
        if res is None:
            logging.error(
                "bad format for conference \"{0}\" (ex.: crypto2012 crypto11 stoc95 crypto13-1)".format(conf_year))
            sys.exit(1)
        confkey = res.group(1).upper()
        year = int(res.group(2))
        dis = res.group(3)
        if year < 50:
            year += 2000
        elif year < 100:
            year += 1900
        short_year = "{0:02d}".format(year % 100)

        run(confkey, year, dis, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
