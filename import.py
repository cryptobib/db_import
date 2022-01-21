#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO
# - manage correctly tags inside tags ! (xml.etree.ElementTree.tostringlist(...)

# Parts of this file come from eprint-update.py from Paul Baecher



import os
import sys

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import xml.etree.ElementTree
from xml.etree import ElementTree
from xml.etree.ElementTree import XML
import urllib.request, urllib.error, urllib.parse
import re
import time
import sys
import logging
import logging_colorer
from unidecode import unidecode
import os.path
import argparse
import html.parser

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
    r"Shekh Faisal Abdul-Latip": (r"Shekh Faisal {Abdul-Latip}", r"Abdul-Latip"),
    r"Nael B. Abu-Ghazaleh": (r"Nael B. {Abu-Ghazaleh}", r"Abu-Ghazaleh"),
    r"Ruba Abu-Salma": (r"Ruba {Abu-Salma}", r"Abu-Salma"),
    r"Carlos Aguilar Melchor": (r"Carlos {Aguilar Melchor}", r"AguilarMelchor"),
    r"Mahdi Nasrullah Al-Ameen": (r"Mahdi Nasrullah {Al-Ameen}", r"Al-Ameen"),
    r"Mustafa Al-Bassam": (r"Mustafa {Al-Bassam}", r"Al-Bassam"),
    r"Sultan Al-Hinai": (r"Sultan {Al-Hinai}", r"Al-Hinai"),
    r"Mohamed Al-Ibrahim": (r"Mohamed {Al-Ibrahim}", r"Al-Ibrahim"),
    r"Naser Al-Ibrahim": (r"Naser {Al-Ibrahim}", r"Al-Ibrahim"),
    r"Noor R. Al-Kazaz": (r"Noor R. {Al-Kazaz}", r"Al-Kazaz"),
    r"Mohammed Ghazi Al-Obeidallah": (r"Mohammed Ghazi {Al-Obeidallah}", r"Al-Obeidallah"),
    r"Zakaria Al-Qudah": (r"Zakaria {Al-Qudah}", r"Al-Qudah"),
    r"Sattam S. Al-Riyami": (r"Sattam S. {Al-Riyami}", r"Al-Riyami"),
    r"Mohammed Al-Shaboti": (r"Mohammed {Al-Shaboti}", r"Al-Shaboti"),
    r"Ehab Al-Shaer": (r"Ehab {Al-Shaer}", r"Al-Shaer"),
    r"Said F. Al-Sarawi": (r"Said F. {Al-Sarawi}", r"Al-Sarawi"),
    r"Aisha I. Ali-Gombe": (r"Aisha I. {Ali-Gombe}", r"Ali-Gombe"),
    r"Nabil Alkeilani Alkadri": (r"Nabil {Alkeilani Alkadri}", r"AlkeilaniAlkadri"),
    r"Jacob Alperin-Sheriff": (r"Jacob {Alperin-Sheriff}", r"Alperin-Sheriff"),
    r"Estuardo Alpirez Bock": (r"Estuardo {Alpirez Bock}", r"AlpirezBock"),
    r"Dami[áa]n Aparicio-S[áa]nchez": (r"Dami{\'a}n {Aparicio-S{\'a}nchez}", r"Aparicio-Sanchez"),
    r"Enrique Argones-R[úu]a": (r"Enrique {Argones-R{\'u}a}", r"Argones-Rua"),
    r"Babak Azimi-Sadjadi": (r"Babak {Azimi-Sadjadi}", r"Azimi-Sadjadi"),

    r"Achiya Bar-On": (r"Achiya {Bar-On}", r"Bar-On"),
    r"Ahmad Baraani-Dastjerdi": (r"Ahmad {Baraani-Dastjerdi}", r"Baraani-Dastjerdi"),
    r"Pirouz Bazargan-Sabet": (r"Pirouz {Bazargan-Sabet}", r"Bazargan-Sabet"),
    r"Emmanuel Bello-Ogunu": (r"Emmanuel {Bello-Ogunu}", r"Bello-Ogunu"),
    r"Ishai Ben-Aroya": (r"Ishai {Ben-Aroya}", r"Ben-Aroya"),
    r"Hussain Ben-Azza": (r"Hussain {Ben-Azza}", r"Ben-Azza"),
    r"Assaf Ben-David": (r"Assaf {Ben-David}", r"Ben-David"),
    r"Shalev Ben-David": (r"Shalev {Ben-David}", r"Ben-David"),
    r"Aner Ben-Efraim": (r"Aner {Ben-Efraim}", r"Ben-Efraim"),
    r"Omri Ben-Eliezer": (r"Omri {Ben-Eliezer}", r"Ben-Eliezer"),
    r"In[èe]s Ben El Ouahma": (r"In{\`e}s {Ben El Ouahma}", r"BenElOuahma"),
    r"Raz Ben-Netanel": (r"Raz {Ben-Netanel}", r"Ben-Netanel"),
    r"Michael Ben-Or": (r"Michael {Ben-Or}", r"Ben-Or"),
    r"Eli Ben-Sasson": (r"Eli {Ben-Sasson}", r"Ben-Sasson"),
    r"Adi Ben-Zvi": (r"Adi {Ben-Zvi}", r"Ben-Zvi"),
    r"Noemie Beringuier-Boher": (r"Noemie {Beringuier-Boher}", r"Beringuier-Boher"),
    r"Abhilasha Bhargav-Spantzel": (r"Abhilasha {Bhargav-Spantzel}", r"Bhargav-Spantzel"),
    r"Alberto Blanco-Justicia": (r"Alberto {Blanco-Justicia}", r"Blanco-Justicia"),
    r"Imane Bouij-Pasquier": (r"Imane {Bouij-Pasquier}", r"Bouij-Pasquier"),
    r"Nora Boulahia-Cuppens": (r"Nora {Boulahia-Cuppens}", r"Boulahia-Cuppens"),
    r"Cristian Bravo-Lillo": (r"Cristian {Bravo-Lillo}", r"Bravo-Lillo"),
    r"Geeke Bruin-Muurling": (r"Geeke {Bruin-Muurling}", r"Bruin-Muurling"),

    r"C. Caballero-Gil": (r"C{\'a}ndido {Caballero-Gil}", r"Caballero-Gil"),
    r"C[áa]ndido Caballero-Gil": (r"C{\'a}ndido {Caballero-Gil}", r"Caballero-Gil"),
    r"Pino Caballero-Gil": (r"Pino {Caballero-Gil}", r"Caballero-Gil"),
    r"Jos[ée] Cabrero-Holgueras": (r"Jos{\'e} {Cabrero-Holgueras}", r"Cabrero-Holgueras"),
    r"C[ée]cile Canovas-Dumas": (r"C{\'e}cile {Canovas-Dumas}", r"Canovas-Dumas"),
    r"Keren Censor-Hillel": (r"Keren {Censor-Hillel}", r"Censor-Hillel"),
    r"Daniel Cervantes-V[áa]zquez": (r"Daniel {Cervantes-V{\'a}zquez}", r"Cervantes-Vazquez"),
    r"Eric Chan-Tin": (r"Eric {Chan-Tin}", r"Chan-Tin"),
    r"Beno[îi]t Chevallier-Mames": (r"Beno{\^\i}t {Chevallier-Mames}", r"Chevallier-Mames"),
    r"Jes[úu]s-Javier Chi-Dom[íi]nguez": (r"Jes{\'u}s-Javier {Chi-Dom{\'\i}nguez}", r"Chi-Dominguez"),
    r"Vincent Cohen-Addad": (r"Vincent {Cohen-Addad}", r"Cohen-Addad"),
    r"Katriel Cohn-Gordon": (r"Katriel {Cohn-Gordon}", r"Cohn-Gordon"),
    r"[ÉE]ric Colin de Verdi[èe]re": (r"{\'E}ric {Colin de Verdi{\`e}re}", r"ColindeVerdiere"),
    r"Hubert Comon-Lundh": (r"Hubert {Comon-Lundh}", r"Comon-Lundh"),
    r"Daniele Cono D'Elia": (r"Daniele {Cono D'Elia}", r"ConoDElia"),
    r"Henry Corrigan-Gibbs": (r"Henry {Corrigan-Gibbs}", r"Corrigan-Gibbs"),
    r"Masashi Crete-Nishihata": (r"Masashi {Crete-Nishihata}", r"Crete-Nishihata"),
    r"Nora Cuppens-Boulahia": (r"Nora {Cuppens-Boulahia}", r"Cuppens-Boulahia"),

    r"Dana Dachman-Soled": (r"Dana {Dachman-Soled}", r"Dachman-Soled"),
    r"Ugo Dal Lago": (r"Ugo {Dal Lago}", r"DalLago"),
    r"Paolo D'Arco": (r"Paolo {D'Arco}", r"DArco"),
    r"Koen [dD]e Boer": (r"Koen {de Boer}", r"deBoer"),
    r"Christophe [dD]e Canni[èe]re": (r"Christophe {De Canni{\`e}re}", r"DeCanniere"),
    r"Sabrina [dD]e Capitani [dD]i Vimercati": (r"Sabrina {De Capitani di Vimercati}", r"DeCapitanidiVimercati"),
    r"Angelo [dD]e Caro": (r"Angelo {De Caro}", r"DeCaro"),
    r" Jean-Lou [Dd]e Carufel": (r" Jean-Lou {De Carufel}", r"DeCarufel"),
    r"Eloi [dD]e Ch[ée]risey": (r"Eloi {de Ch{\'e}risey}", r"deCherisey"),
    r"Ruan [dD]e Clercq": (r"Ruan {de Clercq}", r"deClercq"),
    r"Emiliano [Dd]e Cristofaro": (r"Emiliano {De Cristofaro}", r"DeCristofaro"),
    r"Guerric Meurice [dD]e Dormale": (r"Guerric Meurice {de Dormale}", r"deDormale"),
    r"Luca [dD]e Feo": (r"Luca {De Feo}", r"DeFeo"),
    r"Jos[ée] Mar[íi]a [dD]e Fuentes": (r"Jos{\'e} Mar{\'\i}a {de Fuentes}", r"deFuentes"),
    r"Peter [Dd]e Gersem": (r"Peter {De Gersem}", r"DeGersem"),
    r"Jaybie A. [dD]e Guzman": (r"Jaybie A. {de Guzman}", r"deGuzman"),
    r"Wiebren [dD]e Jonge": (r"Wiebren {de Jonge}", r"deJonge"),
    r"Eduardo [dD]e [lL]a Torre": (r"Eduardo {de la Torre}", r"delaTorre"),
    r"Lauren [Dd]e Meyer": (r"Lauren {De Meyer}", r"DeMeyer"),
    r"Dieter [Dd]e Moitie": (r"Dieter {De Moitie}", r"DeMoitie"),
    r"Elke [Dd]e Mulder": (r"Elke {De Mulder}", r"DeMulder"),
    r"Roberto [dD]e Prisco": (r"Roberto {De Prisco}", r"DePrisco"),
    r"Joeri [dD]e Ruiter": (r"Joeri {de Ruiter}", r"deRuiter"),
    r"Alfredo [dD]e Santis": (r"Alfredo {De Santis}", r"DeSantis"),
    r"Fabrizio [Dd]e Santis": (r"Fabrizio {De Santis}", r"DeSantis"),
    r"Domenico [Dd]e Seta": (r"Domenico {De Seta}", r"DeSeta"),
    r"Marijke [Dd]e Soete": (r"Marijke {De Soete}", r"DeSoete"),
    r"Lorenzo [Dd]e Stefani": (r"Lorenzo {De Stefani}", r"DeStefani"),
    r"Dominique [dD]e Waleffe": (r"Dominique {de Waleffe}", r"deWaleffe"),
    r"Erik [Dd]e Win": (r"Erik {De Win}", r"DeWin"),
    r"Ronald [dD]e Wolf": (r"Ronald {de Wolf}", r"deWolf"),
    r"Thomas Debris-Alazard": (r"Thomas {Debris-Alazard}", r"Debris-Alazard"),
    r"Martin Dehnel-Wild": (r"Martin {Dehnel-Wild}", r"Dehnel-Wild"),
    r"Rafa[ëe]l del Pino": (r"Rafaël {del Pino}", r"delPino"),
    r"Romar B. dela Cruz": (r"Romar B. {dela Cruz}", r"delaCruz"),
    r"Antoine Delignat-Lavaud": (r"Antoine {Delignat-Lavaud}", r"Delignat-Lavaud"),
    r"Sergi Delgado-Segura": (r"Sergi {Delgado-Segura}", r"Delgado-Segura"),
    r"Bert [dD]en Boer": (r"Bert {den Boer}", r"denBoer"),
    r"Cyprien de Saint Guilhem": (r"Cyprien {de Saint Guilhem}", r"deSaintGuilhem"),
    r"Cyprien Delpech de Saint Guilhem": (r"Cyprien {de Saint Guilhem}", r"deSaintGuilhem"),
    r"Monika [Ddi] Angelo": (r"Monika {Di Angelo}", r"DiAngelo"),
    r"Giovanni [Dd]i Crescenzo": (r"Giovanni {Di Crescenzo}", r"DiCrescenzo"),
    r"Giorgio [Dd]i Natale": (r"Giorgio {Di Natale}", r"DiNatale"),
    r"Roberto [Dd]i Pietro": (r"Roberto {Di Pietro}", r"DiPietro"),
    r"Matteo [Dd]i Pirro": (r"Matteo {Di Pirro}", r"DiPirro"),
    r"Mario [Dd]i Raimondo": (r"Mario {Di Raimondo}", r"DiRaimondo"),
    r"Giorgio [Dd]i Tizio": (r"Giorgio {Di Tizio}", r"DiTizio"),
    r"Jerome [Dd]i-Battista": (r"Jerome {Di-Battista}", r"Di-Battista"),
    r"Guilherme [Dd]ias da Fonseca": (r"Guilherme {Dias da Fonseca}", r"DiasdaFonseca"),
    r"Jes[úu]s E. D[íi]az-Verdejo": (r"Jes{\'u}s E. {D{\'\i}az-Verdejo}", r"Diaz-Verdejo"),
    r"Brendan Dolan-Gavitt": (r"Brendan {Dolan-Gavitt}", r"Dolan-Gavitt"),
    r"Daniel Ricardo [dD]os Santos": (r"Daniel Ricardo {Dos Santos}", r"DosSantos"),
    r"Josep Domingo-Ferrer": (r"Josep {Domingo-Ferrer}", r"Domingo-Ferrer"),
    r"Agustin Dominguez-Oviedo": (r"Agustin {Dominguez-Oviedo}", r"Dominguez-Oviedo"),
    r"Dana Drachsler-Cohen": (r"Dana {Drachsler-Cohen}", r"Drachsler-Cohen"),
    r"Edouard Dufour Sans": (r"Edouard {Dufour Sans}", r"DufourSans"),

    r"Amr El Abbadi": (r"Amr {El Abbadi}", r"ElAbbadi"),
    r"Laila El Aimani": (r"Laila {El Aimani}", r"ElAimani"),
    r"Safwan El Assad": (r"Safwan {El Assad}", r"ElAssad"),
    r"Rachid El Bansarkhani": (r"Rachid {El Bansarkhani}", r"ElBansarkhani"),
    r"Karim El Defrawy": (r"Karim {El Defrawy}", r"ElDefrawy"),
    r"Abbas El Gamal": (r"Abbas {El Gamal}", r"ElGamal"),
    r"Said El Hajji": (r"Said {El Hajji}", r"ElHajji"),
    r"Noreddine El Janati El Idrissi": (r"Noreddine {El Janati El Idrissi}", r"ElJanatiElIdrissi"),
    r"Ali El Kaafarani": (r"Ali {El Kaafarani}", r"ElKaafarani"),
    r"Rami El Khatib": (r"Rami {El Khatib}", r"ElKhatib"),
    r"Nadia El Mrabet": (r"Nadia {El Mrabet}", r"ElMrabet"),
    r"El Mahdi El Mhamdi": (r"El Mahdi {El Mhamdi}", r"ElMhamdi"),
    r"Anas Abou El Kalam": (r"Anas Abou {El Kalam}", r"ElKalam"),
    r"Mohamed El Massad": (r"Mohamed {El Massad}", r"ElMassad"),
    r"Rachid El Kouch": (r"Rachid {El Kouch}", r"ElKouch"),
    r"Philippe Elbaz-Vincent": (r"Philippe {Elbaz-Vincent}", r"Elbaz-Vincent"),
    r"R. Marije Elkenbracht-Huizin": (r"R. Marije {Elkenbracht-Huizin}", r"Elkenbracht-Huizin"),

    r"Martin Farach-Colton": (r"Martin {Farach-Colton}", r"Farach-Colton"),
    r"Armando Faz-Hern[áa]ndez": (r"Armando {Faz-Hern{\'a}ndez}", r"Faz-Hernandez"),
    r"Eduardo Fern[áa]ndez-Medina": (r"Eduardo {Fern{\'a}ndez-Medina}", r"Fernandez-Medina"),
    r"Josep Llu[íi]s Ferrer-Gomila": (r"Josep Llu{\'\i}s {Ferrer-Gomila}", r"Ferrer-Gomila"),
    r"Christof Ferreira Torres": (r"Christof {Ferreira Torres}", r"FerreiraTorres"),
    r"Jonathan Fetter-Degges": (r"Jonathan {Fetter-Degges}", r"Fetter-Degges"),
    r"Aris Filos-Ratsikas": (r"Aris {Filos-Ratsikas}", r"Filos-Ratsikas"),
    r"Simone Fischer-H[üu]bner": (r"Simone {Fischer-Hübner}", r"Fischer-Hubner"),
    r"Beltran Borja Fiz Pontiveros": (r"Beltran Borja {Fiz Pontiveros}", r"FizPontiveros"),
    r"Eli Fox-Epstein": (r"Eli {Fox-Epstein}", r"Fox-Epstein"),
    r"Amparo F[úu]ster-Sabater": (r"Amparo {F{\'u}ster-Sabater}", r"Fuster-Sabater"),

    r"Emilio Jes[úu]s Gallego Arias": (r"Emilio Jes{\'u}s {Gallego Arias}", r"GallegoArias"),
    r"Joaqu[íi]n Garc[íi]a-Alfaro": (r"Joaqu{\'\i}n {Garc{\'\i}a-Alfaro}", r"Garcia-Alfaro"),
    r"Joan Garc[íi]a-Haro": (r"Joan {Garc{\'\i}a-Haro}", r"Garcia-Haro"),
    r"H. Garc[íi]a-Molina": (r"H{\'e}ctor {Garc{\'\i}a-Molina}", r"Garcia-Molina"),
    r"H[ée]ctor Garc[íi]a-Molina": (r"H{\'e}ctor {Garc{\'\i}a-Molina}", r"Garcia-Molina"),
    r"[ÓO]scar Garc[íi]a-Morch[óo]n": (r"{\'O}scar {Garc{\'\i}a-Morch{\'o}n}", r"Garcia-Morchon"),
    r"Francisco Javier Garc[íi]a-Salom[óo]n": (r"Francisco Javier {Garc{\'\i}a-Salom{\'o}n}", r"Garcia-Salomon"),
    r"Pedro Garc[íi]a-Teodoro": (r"Pedro {Garc{\'\i}a-Teodoro}", r"Garcia-Teodoro"),
    r"Jorge Garza-Vargas": (r"Jorge {Garza-Vargas}", r"Garza-Vargas"),
    r"Val[ée]rie Gauthier-Uma[ñn]a": (r"Val{\'e}rie {Gauthier-Uma{\~n}a}", r"Gauthier-Umana"),
    r"Domingo G[óo]mez-P[ée]rez": (r"Domingo {G{\'o}mez-P{\'e}rez}", r"Gomez-Perez"),
    r"Antonio F. G[óo]mez-Skarmeta": (r"Antonio F. {G{\'o}mez-Skarmeta}", r"Gomez-Skarmeta"),
    r"Mar[ií]a Isabel Gonz[aá]lez Vasco": (r"Mar{\'\i}a Isabel {Gonz{\'a}lez Vasco}", r"GonzalezVasco"),
    r"Juan Gonz[áa]lez Nieto": (r"Juan Manuel {Gonz{\\'a}lez Nieto}", r"GonzalezNieto"),
    r"Juan Manuel Gonz[aá]lez Nieto": (r"Juan Manuel {Gonz{\\'a}lez Nieto}", r"GonzalezNieto"),
    r"Juanma Gonz[áa]lez Nieto": (r"Juan Manuel {Gonz{\\'a}lez Nieto}", r"GonzalezNieto"),
    r"Ana Gonz[áa]lez-Marcos": (r"Ana {Gonz{\'a}lez-Marcos}", r"Gonzalez-Marcos"),
    r"Raouf N. Gorgui-Naguib": (r"Raouf N. {Gorgui-Naguib}", r"Gorgui-Naguib"),
    r"Ludovic Guillaume-Sage": (r"Ludovic {Guillaume-Sage}", r"Guillaume-Sage"),

    r"Sariel Har-Peled": (r"Sariel {Har-Peled}", r"Har-Peled"),
    r"Julio Hernandez-Castro": (r"Julio {Hernandez-Castro}", r"Hernandez-Castro"),
    r"Julio C[ée]sar Hern[áa]ndez-Castro": (r"Julio C{\'e}sar {Hern{\'a}ndez-Castro}", r"Hernandez-Castro"),
    r"Candelaria Hern[áa]ndez-Goya": (r"Candelaria {Hern{\'a}ndez-Goya}", r"Hernandez-Goya"),
    r"Jordi Herrera-Joancomart[íi]": (r"Jordi {Herrera-Joancomart{\'\i}}", r"Herrera-Joancomarti"),
    r"Thomas S. Heydt-Benjamin": (r"Thomas S. {Heydt-Benjamin}", r"Heydt-Benjamin"),
    r"Severin Holzer-Graf": (r"Severin {Holzer-Graf}", r"Holzer-Graf"),
    r"Nick Howgrave-Graham": (r"Nick {Howgrave-Graham}", r"Howgrave-Graham"),
    r"Dimitrios Hristu-Varsakelis": (r"Dimitrios {Hristu-Varsakelis}", r"Hristu-Varsakelis"),
    r"Lo[ïi]s Huguenin-Dumittan": (r"Loïs {Huguenin-Dumittan}", r"Huguenin-Dumittan"),

    r"Luis Irun-Briz": (r"Luis {Irun-Briz}", r"Irun-Briz"),

    r"Bastien Jacot-Guillarmod": (r"Bastien {Jacot-Guillarmod}", r"Jacot-Guillarmod"),

    r"Shabnam Kasra Kermanshahi": (r"Shabnam {Kasra Kermanshahi}", r"KasraKermanshahi"),
    r"S[áa]ndor Kisfaludi-Bak": (r"S{\'a}ndor {Kisfaludi-Bak}", r"Kisfaludi-Bak"),
    r"[ÇC]etin Kaya Ko[çc]": (r"{\c C}etin Kaya Ko{\c c}", r"Koc"),
    r"Eleftherios Kokoris-Kogias": (r"Eleftherios {Kokoris-Kogias}", r"Kokoris-Kogias"),
    r"Lauri Kort-Parn": (r"Lauri {Kort-Parn}", r"Kort-Parn"),
    r"Greg Kroah-Hartman": (r"Greg {Kroah-Hartman}", r"Kroah-Hartman"),
    r"Sophie Kuebler-Wachendorff": (r"Sophie {Kuebler-Wachendorff}", r"Kuebler-Wachendorff"),
    r"Young Kun-Ko": (r"Young {Kun-Ko}", r"Kun-Ko"),
    r"S[ée]bastien Kunz-Jacques": (r"S{\'e}bastien {Kunz-Jacques}", r"Kunz-Jacques"),

    r"H. Andr[ée]s Lagar-Cavilla": (r"H. Andr{\'e}s {Lagar-Cavilla}", r"Lagar-Cavilla"),
    r"Sophie Lambert-Lacroix": (r"Sophie {Lambert-Lacroix}", r"Lambert-Lacroix"),
    r"Rolando L. La Placa": (r"Rolando L. {La Placa}", r"LaPlaca"),
    r"Stevens Le Blond": (r"Stevens {Le Blond}", r"LeBlond"),
    r"Jean-Yves Le Boudec": (r"Jean-Yves {Le Boudec}", r"LeBoudec"),
    r"S[ée]bastien Le Henaff": (r"S{\'e}bastien {Le Henaff}", r"LeHenaff"),
    r"Fran[çc]ois Le Gall": (r"Fran{\c c}ois {Le Gall}", r"LeGall"),
    r"Victor Le Pochat": (r"Victor {Le Pochat}", r"LePochat"),
    r"Dat Le Tien": (r"Dat {Le Tien}", r"LeTien"),
    r"Erik G. Learned-Miller": (r"Erik G. {Learned-Miller}", r"Learned-Miller"),
    r"Kerstin Lemke-Rust": (r"Kerstin {Lemke-Rust}", r"Lemke-Rust"),
    r"Chris Lesniewski-Laas": (r"Chris {Lesniewski-Laas}", r"Lesniewski-Laas"),
    r"Fran[çc]oise Levy-dit-Vehel": (r"Fran{\c c}oise {Levy-dit-Vehel}", r"Levy-dit-Vehel"),
    r"Adriana L[óo]pez-Alt": (r"Adriana {L{\'o}pez-Alt}", r"Lopez-Alt"),
    r"Conrado Porto Lopes Gouv[êe]a": (r"Conrado Porto {Lopes Gouv{\^e}a}", r"LopesGouvea"),
    r"Julio L[óo]pez[- ]Hern[áa]ndez": (r"Julio Cesar {L{\'o}pez-Hern{\'a}ndez}", r"Lopez-Hernandez"),
    r"Julio L[óo]pez": (r"Julio Cesar {L{\'o}pez-Hern{\'a}ndez}", r"Lopez-Hernandez"),
    r"Julio Cesar L[óo]pez[- ]Hern[áa]ndez": (r"Julio Cesar {L{\'o}pez-Hern{\'a}ndez}", r"Lopez-Hernandez"),
    r"Emmanuel L[óo]pez-Trejo": (r"Emmanuel {L{\'o}pez-Trejo}", r"Lopez-Trejo"),
    r"Lesa Lorenzen-Huber": (r"Lesa {Lorenzen-Huber}", r"Lorenzen-Huber"),
    r"Philippe Loubet-Moundi": (r"Philippe {Loubet-Moundi}", r"Loubet-Moundi"),

    r"Gilles Macario-Rat": (r"Gilles {Macario-Rat}", r"Macario-Rat"),
    r"Malik Magdon-Ismail": (r"Malik {Magdon-Ismail}", r"Magdon-Ismail"),
    r"Mohammad Mahmoody-Ghidary": (r"Mohammad {Mahmoody-Ghidary}", r"Mahmoody-Ghidary"),
    r"Josemaria Malgosa-Sanahuja": (r"Josemaria {Malgosa-Sanahuja}", r"Malgosa-Sanahuja"),
    r"John Malone-Lee": (r"John {Malone-Lee}", r"Malone-Lee"),
    r"Cuauhtemoc Mancillas-L[óo]pez": (r"Cuauhtemoc {Mancillas-L{\'o}pez}", r"Mancillas-Lopez"),
    r"Pilar Manzanares-Lopez": (r"Pilar {Manzanares-Lopez}", r"Manzanares-Lopez"),
    r"Jos{\'e} Mar[íi]a Sierra": (r"Jos{\'e} {Mar{\'\i}a Sierra}", r"MariaSierra"),
    r"Morgan Marquis-Boire": (r"Morgan {Marquis-Boire}", r"Marquis-Boire"),
    r"Rafael Mar[íi]n L[óo]pez": (r"Rafael {Mar{\'\i}n L{\'o}pez}", r"MarinLopez"),
    r"Jaume Mart[íi]-Farr[ée]": (r"Jaume {Mart{\'\i}-Farr{\'e}}", r"Marti-Farre"),
    r"Consuelo Mart[íi]nez": (r"Consuelo Mart{\'\i}nez", r"Martinez"),
    r"Alberto F. Mart[íi]nez-Herrera": (r"Alberto F. {Mart{\'\i}nez-Herrera}", r"Martinez-Herrera"),
    r"J. L. Martinez-Hurtado": (r"Juan Leonardo {Martinez-Hurtado}", r"Martinez-Hurtado"),
    r"Juan Leonardo Martinez-Hurtado": (r"Juan Leonardo {Martinez-Hurtado}", r"Martinez-Hurtado"),
    r"E. Mart[íi]nez-Moro": (r"Edgar {Mart{\'\i}nez-Moro}", r"Martinez-Moro"),
    r"Edgar Mart[íi]nez-Moro": (r"Edgar {Mart{\'\i}nez-Moro}", r"Martinez-Moro"),
    r"Luis Mart[íi]nez-Ramos": (r"Luis {Mart{\'\i}nez-Ramos}", r"Martinez-Ramos"),
    r"Rita Mayer-Sommer": (r"Rita {Mayer-Sommer}", r"Mayer-Sommer"),
    r"Breno de Medeiros": (r"{Breno de} Medeiros", r"Medeiros"),
    r"Rafael Mendes de Oliveira": (r"Rafael {Mendes de Oliveira}", r"MendesDeOliveira"),
    r"Foteinos Mergoupis-Anagnou": (r"Foteinos {Mergoupis-Anagnou}", r"Mergoupis-Anagnou"),
    r"Santos Merino [Dd]el Pozo": (r"Santos {Merino Del Pozo}", r"MerinoDelPozo"),
    r"J. Carlos Mex-Perera": (r"Jorge Carlos {Mex-Perera}", r"Mex-Perera"),
    r"Jorge Carlos Mex-Perera": (r"Jorge Carlos {Mex-Perera}", r"Mex-Perera"),
    r"Jezabel Molina-Gil": (r"Jezabel {Molina-Gil}", r"Molina-Gil"),
    r"Pedro Moreno-Sanchez": (r"Pedro {Moreno-Sanchez}", r"Moreno-Sanchez"),
    r"Robert H. Morris Sr.": (r"Robert H. {Morris Sr.}", r"MorrisSr"),
    r"J. Mozo-Fern[áa]ndez": (r"Jorge {Mozo-Fern{\'a}ndez}", r"Mozo-Fernandez"),
    r"Jorge Mozo-Fern[áa]ndez": (r"Jorge {Mozo-Fern{\'a}ndez}", r"Mozo-Fernandez"),
    r"J[öo]rn M[üu]ller-Quade": (r"Jörn {Müller-Quade}", r"Muller-Quade"),
    r"Christian M[üu]ller-Schloer": (r"Christian {Müller-Schloer}", r"Muller-Schloer"),
    r"Juan Pedro Mu[ñn]oz-Gea": (r"Juan Pedro {Mu{\~n}oz-Gea}", r"Munoz-Gea"),
    r"Emerson R. Murphy-Hill": (r"Emerson R. {Murphy-Hill}", r"Murphy-Hill"),

    r"Guillermo Navarro-Arribas": (r"Guillermo {Navarro-Arribas}", r"Navarro-Arribas"),
    r"Mar[ií]a Naya-Plasencia": (r"Mar{\'\i}a {Naya-Plasencia}", r"Naya-Plasencia"),
    r"Cristina Nita-Rotaru": (r"Cristina {Nita-Rotaru}", r"Nita-Rotaru"),
    r"Juan Arturo Nolazco-Flores": (r"Juan Arturo {Nolazco-Flores}", r"Nolazco-Flores"),

    r"Eduardo Ochoa-Jim[ée]nez": (r"Eduardo {Ochoa-Jim{\'e}nez}", r"Ochoa-Jimenez"),

    r"Francesco Parisi-Presicce": (r"Francesco {Parisi-Presicce}", r"Parisi-Presicce"),
    r"Anat Paskin-Cherniavsky": (r"Anat {Paskin-Cherniavsky}", r"Paskin-Cherniavsky"),
    r"Beni Paskin-Cherniavsky": (r"Beni {Paskin-Cherniavsky}", r"Paskin-Cherniavsky"),
    r"Magdalena Payeras-Capell[àa]": (r"Magdalena {Payeras-Capell{\`a}}", r"Payeras-Capella"),
    r"F. Pebay-Peyroula": (r"F. {Pebay-Peyroula}", r"Pebay-Peyroula"),
    r"Micha[ëe]l Peeters": (r"Micha{\"e}l Peeters", r"Peeters"),
    r"Alice Pellet-Mary": (r"Alice {Pellet-Mary}", r"Pellet-Mary"),
    r"Fernando Pere[ñn]iguez-Garcia": (r"Fernando {Pere{\~n}iguez-Garcia}", r"Pereniguez-Garcia"),
    r"Angel L. P[ée]rez [dD]el Pozo": (r"Angel L. {P{\'e}rez del Pozo}", r"PerezdelPozo"),
    r"David P[ée]rez Garc[íi]a": (r"David {P{\'e}rez Garc{\'\i}a}", r"PerezGarcia"),
    r"Diego Perez-Botero": (r"Diego {Perez-Botero}", r"Perez-Botero"),
    r"Fernando P[ée]rez-Cruz": (r"Fernando {P{\'e}rez-Cruz}", r"Perez-Cruz"),
    r"Luis P[ée]rez-Freire": (r"Luis {P{\'e}rez-Freire}", r"Perez-Freire"),
    r"Fernando P[ée]rez-Gonz[áa]lez": (r"Fernando {P{\'e}rez-Gonz{\'a}lez}", r"Perez-Gonzalez"),
    r"Cristina P[ée]rez-Sol[àa]": (r"Cristina {P{\'e}rez-Sol{\`a}}", r"Perez-Sola"),
    r"Pedro Peris-Lopez": (r"Pedro {Peris-Lopez}", r"Peris-Lopez"),
    r"Fr[ée]d[ée]ric de Portzamparc": (r"{Fr{\'e}d{\'e}ric de} Portzamparc", r"Portzamparc"),
    r"Fr[ée]d[ée]ric de Portzamparc": (r"{Fr{\'e}d{\'e}ric de} Portzamparc", r"Portzamparc"),
    r"Fr[ée]d[ée]ric Urvoy de Portzamparc": (r"{Fr{\'e}d{\'e}ric de} Portzamparc", r"Portzamparc"),
    r"Deike Priemuth-Schmid": (r"Deike {Priemuth-Schmid}", r"Priemuth-Schmid"),

    r"I[ñn]igo Querejeta-Azurmendi": (r"I{\~n}igo {Querejeta-Azurmendi}", r"Querejeta-Azurmendi"),

    r"Andrew Read-McFarland": (r"Andrew {Read-McFarland}", r"Read-McFarland"),
    r"Arne Renkema-Padmos": (r"Arne {Renkema-Padmos}", r"Renkema-Padmos"),
    r"Arash Reyhani-Masoleh": (r"Arash {Reyhani-Masoleh}", r"Reyhani-Masoleh"),
    r"Francisco Rodr[íi]guez-Henr[íi]quez": (r"Francisco {Rodr{\'\i}guez-Henr{\'\i}quez}", r"Rodriguez-Henriquez"),
    r"Noga Ron-Zewi": (r"Noga {Ron-Zewi}", r"Ron-Zewi"),
    r"Lloren[çc] Huguet i Rotger": (r"{Lloren\c{c} Huguet i} Rotger", r"Rotger"),
    r"Adeline Roux-Langlois": (r"Adeline {Roux-Langlois}", r"Roux-Langlois"),

    r"Reihaneh Safavi-Naini": (r"Reihaneh {Safavi-Naini}", r"Safavi-Naini"),
    r"Juan Carlos S[áa]nchez[- ]Aarnoutse": (r"Juan Carlos {S{\'a}nchez-Aarnoutse}", r"Sanchez-Aarnoutse"),
    r"Carmen S[áa]nchez-[ÁA]vila": (r"Carmen {S{\'a}nchez-{\'A}vila}", r"Sanchez-Avila"),
    r"Raul S[áa]nchez-Reillo": (r"Raul {S{\'a}nchez-Reillo}", r"Sanchez-Reillo"),
    r"Iskander S[áa]nchez-Rola": (r"Iskander {S{\'a}nchez-Rola}", r"Sanchez-Rola"),
    r"Santiago S[áa]nchez-Solano": (r"Santiago {S{\'a}nchez-Solano}", r"Sanchez-Solano"),
    r"Anderson Santana de Oliveira": (r"Anderson {Santana de Oliveira}", r"SantanadeOliveira"),
    r"Ingrid Schaum[üu]ller-Bichl": (r"Ingrid {Schaumüller-Bichl}", r"Schaumuller-Bichl"),
    r"Ulrike Schmidt-Kraepelin": (r"Ulrike {Schmidt-Kraepelin}", r"Schmidt-Kraepelin"),
    r"Katja Schmidt-Samoa": (r"Katja {Schmidt-Samoa}", r"Schmidt-Samoa"),
    r"John Scott-Railton": (r"John {Scott-Railton}", r"Scott-Railton"),
    r"Abdelmalek Si-Merabet": (r"Abdelmalek {Si-Merabet}", r"Si-Merabet"),
    r"[Aa]bhi [Ss]helat": (r"{abhi} {shelat}", r"shelat"),
    r"Alexandra Shulman-Peleg": (r"Alexandra {Shulman-Peleg}", r"Shulman-Peleg"),
    r"Daniel Simmons-Marengo": (r"Daniel {Simmons-Marengo}", r"Simmons-Marengo"),
    r"Stelios Sidiroglou-Douskos": (r"Stelios {Sidiroglou-Douskos}", r"Sidiroglou-Douskos"),
    r"William E. Skeith III": (r"William E. {Skeith III}", r"SkeithIII"),
    r"Daniel Smith-Tone": (r"Daniel {Smith-Tone}", r"Smith-Tone"),
    r"Eduardo Soria-Vazquez": (r"Eduardo {Soria-Vazquez}", r"Soria-Vazquez"),
    r"Tage Stabell-Kul[øo]": (r"Tage {Stabell-Kul{\o}}", r"Stabell-Kulo"),
    r"Noah Stephens-Davidowitz": (r"Noah {Stephens-Davidowitz}", r"Stephens-Davidowitz"),
    r"Brett Stone-Gross": (r"Brett {Stone-Gross}", r"Stone-Gross"),
    r"Adriana Su[áa]rez Corona": (r"Adriana {Su{\'a}rez Corona}", r"SuarezCorona"),
    r"Guillermo Su[áa]rez[- ]Tangil": (r"Guillermo {Su{\'a}rez-Tangil}", r"SuarezTangil"),
    r"Guillermo Su[áa]rez [dD]e Tangil": (r"Guillermo {Su{\'a}rez-Tangil}", r"SuarezTangil"),

    r"Amnon Ta-Shma": (r"Amnon {Ta-Shma}", r"Ta-Shma"),
    r"Anne Tardy-Corfdir": (r"Anne {Tardy-Corfdir}", r"Tardy-Corfdir"),
    r"Herman [tT]e Riele": (r"Herman {te Riele}", r"teRiele"),
    r"Joan Tom[àa]s-Buliart": (r"Joan {Tom{\`a}s-Buliart}", r"Tomas-Buliart"),
    r"Nicole Tomczak-Jaegermann": (r"Nicole {Tomczak-Jaegermann}", r"Tomczak-Jaegermann"),
    r"Jorge Toro[- ]Pozo": (r"Jorge {Toro-Pozo}", r"Toro-Pozo"),
    r"Jose Luis Torre-Arce": (r"Jose Luis {Torre-Arce}", r"Torre-Arce"),
    r"Santiago Torres-Arias": (r"Santiago {Torres-Arias}", r"Torres-Arias"),
    r"Juan Ram[óo]n Troncoso-Pastoriza": (r"Juan Ram{\'o}n {Troncoso-Pastoriza}", r"Troncoso-Pastoriza"),
    r"Vladimir Trujillo-Olaya": (r"Vladimir {Trujillo-Olaya}", r"Trujillo-Olaya"),
    r"Rolando Trujillo-Ras[úu]a": (r"Rolando {Trujillo-Ras{\'u}a}", r"Trujillo-Rasua"),

    r"Nelufar Ulfat-Bunyadi": (r"Nelufar {Ulfat-Bunyadi}", r"Ulfat-Bunyadi"),

    r"Narseo Vallina-Rodriguez": (r"Narseo {Vallina-Rodriguez}", r"Vallina-Rodriguez"),
    r"Joran [vV]an Apeldoorn": (r"Joran {van Apeldoorn}", r"vanApeldoorn"),
    r"Jo [Vv]an Bulck": (r"Jo {Van Bulck}", r"VanBulck"),
    r"Jan [vV]an [dD]e Brand": (r"Jan {van de Brand}", r"vandeBrand"),
    r"Jeroen [vV]an [dD]e Graaf": (r"Jeroen {van de Graaf}", r"vandeGraaf"),
    r"Ivor [vV]an [dD]er Hoog": (r"Ivor {van der Hoog}", r"vanderHoog"),
    r"Tim [vV]an [dD]e Kamp": (r"Tim {van de Kamp}", r"vandeKamp"),
    r"Joachim [vV]an [dD]en Berg": (r"Joachim {van den Berg}", r"vandenBerg"),
    r"Robbert [vV]an [dD]en Berg": (r"Robbert {van den Berg}", r"vandenBerg"),
    r"Jan [Vv]an [dD]en Bussche": (r"Jan {Van den Bussche}", r"VandenBussche"),
    r"Jan [Vv]an [dD]en Herrewegen": (r"Jan {Van den Herrewegen}", r"VandenHerrewegen"),
    r"Vincent [vV]an [dD]er Leest": (r"Vincent {van der Leest}", r"vanderLeest"),
    r"Jan C. A. [vV]an [dD]er Lubbe": (r"Jan C. A. {van der Lubbe}", r"vanderLubbe"),
    r"Erik van der Sluis": (r"Erik {van der Sluis}", r"vanderSluis"),
    r"Daan [vV]an [dD]er Valk": (r"Daan {van der Valk}", r"vanderValk"),
    r"Victor [vV]an [dD]er Veen": (r"Victor {van der Veen}", r"vanderVeen"),
    r"Marten [vV]an Dijk": (r"Marten {van Dijk}", r"vanDijk"),
    r"Leendert [vV]an Doorn": (r"Leendert {van Doorn}", r"vanDoorn"),
    r"Michel [vV]an Eeten": (r"Michel {van Eeten}", r"vanEeten"),
    r"Bernard [vV]an Gastel": (r"Bernard {van Gastel}", r"vanGastel"),
    r"Tom [vV]an Goethem": (r"Tom {van Goethem}", r"vanGoethem"),
    r"Dirk [vV]an Gucht": (r"Dirk {van Gucht}", r"vanGucht"),
    r"Matthew [Vv]an Gundy": (r"Matthew {Van Gundy}", r"VanGundy"),
    r"Tim [Vv]an hamme": (r"Tim {Van hamme}", r"Vanhamme"),
    r"Eug[èe]ne [vV]an Heijst": (r"Eug{\`e}ne {van Heijst}", r"vanHeijst"),
    r"Anthony [Vv]an Herrewege": (r"Anthony {Van Herrewege}", r"VanHerrewege"),
    r"Iggy [Vv]an Hoof": (r"Iggy {Van Hoof}", r"VanHoof"),
    r"Erik Jan [vV]an Leeuwen": (r"Erik Jan {van Leeuwen}", r"vanLeeuwen"),
    r"Paul C. [Vv]an Oorschot": (r"Paul C. {van Oorschot}", r"vanOorschot"),
    r"Robbert [vV]an Renesse": (r"Robbert {van Renesse}", r"vanRenesse"),
    r"Bart [Vv]an Rompay": (r"Bart {Van Rompay}", r"VanRompay"),
    r"C{\'e}dric [Vv]an Rompay": (r"C{\'e}dric {Van Rompay}", r"VanRompay"),
    r"Peter [vV]an Rossum": (r"Peter {van Rossum}", r"vanRossum"),
    r"Stephan [vV]an Schaik": (r"Stephan {van Schaik}", r"vanSchaik"),
    r"Johan [vV]an Tilburg": (r"Johan {van Tilburg}", r"vanTilburg"),
    r"Christine [vV]an Vredendaal": (r"Christine {van Vredendaal}", r"vanVredendaal"),
    r"Rolf [vV]an Wegberg": (r"Rolf {van Wegberg}", r"vanWegberg"),
    r"Nicolas Veyrat-Charvillon": (r"Nicolas {Veyrat-Charvillon}", r"Veyrat-Charvillon"),
    r"Francisco Jos[ée] Vial Prado": (r"Francisco Jos{\'e} {Vial Prado}", r"VialPrado"),
    r"Ricardo Villanueva-Polanco": (r"Ricardo {Villanueva-Polanco}", r"Villanueva-Polanco"),
    r"Luis [vV]on Ahn": (r"Luis {von Ahn}", r"vonAhn"),
    r"Philipp [vV]on Styp-Rekowsky": (r"Philipp {von Styp-Rekowsky}", r"vonStyp-Rekowsky"),
    r"Emanuel [vV]on Zezschwitz": (r"Emanuel {von Zezschwitz}", r"vonZezschwitz"),

    r"Amaury de Wargny": (r"{Amaury de} Wargny", r"Wargny"),
    r"Benjamin M. M. [dD]e Weger": (r"{Benne de} Weger", r"Weger"),
    r"Benne [dD]e Weger": (r"{Benne de} Weger", r"Weger"),
    r"Christian Wenzel-Benner": (r"Christian {Wenzel-Benner}", r"Wenzel-Benner"),
    r"Ronny Wichers Schreur": (r"Ronny {Wichers Schreur}", r"WichersSchreur"),
    r"Zooko Wilcox-O'Hearn": (r"Zooko {Wilcox-O'Hearn}", r"Wilcox-OHearn"),
    r"John D. Wiltshire-Gordon": (r"John D. {Wiltshire-Gordon}", r"Wiltshire-Gordon"),
    r"Daniel Wolleb-Graf": (r"Daniel {Wolleb-Graf}", r"Wolleb-Graf"),
    r"Christian Wulff-Nilsen": (r"Christian {Wulff-Nilsen}", r"Wulff-Nilsen"),

    r"Irina Zachia-Zlatea": (r"Irina {Zachia-Zlatea}", r"Zachia-Zlatea"),
    r"Santiago Zanella[- ]B[ée]guelin": (r"Santiago {Zanella-B{\'e}guelin}", r"Zanella-Beguelin"),
    r"Rui Zhang II": (r"Rui {Zhang II}", r"ZhangII"),
    r"Leah Zhang-Kennedy": (r"Leah {Zhang-Kennedy}", r"Zhang-Kennedy"),

    r"Giuseppe Amato II": (r"Giuseppe {Amato II}", r"AmatoII"),
    r"Karel Culik II": (r"Karel {Culik II}", r"CulikII"),
    r"Markus Schneider II": (r"Markus {Schneider II}", r"SchneiderII"),
    r"Amitabh Sinha II": (r"Amitabh {Sinha II}", r"SinhaII"),
    r"William R. Speirs II": (r"William R. {Speirs II}", r"SpeirsII"),

    r"Hal Daum[ée] III": (r"Hal {Daum{\'e} III}", r"DaumeIII"),
    r"Robert L. (Scot) Drysdale III": (r"Robert L. (Scot) {Drysdale III}", r"DrysdaleIII"),
    r"Donald E. Eastlake III": (r"Donald E. {Eastlake III}", r"EastlakeIII"),
    r"William C. Garrison III": (r"William C. {Garrison III}", r"GarrisonIII"),
    r"James W. Gray III": (r"James W. {Gray III}", r"GrayIII"),
    r"Harry B. Hunt III": (r"Harry B. {Hunt III}", r"HuntIII"),
    r"Golden G. Richard III": (r"Golden G. {Richard III}", r"RichardIII"),
    r"William N. Scherer III": (r"William N. {Scherer III}", r"SchererIII"),

    r"Waldyr Benits Jr.": (r"Waldyr {Benits Jr.}", r"BenitsJr"),
    r"Edward G. Coffman Jr.": (r"Edward G. {Coffman Jr.}", r"CoffmanJr"),
    r"Jonathan L. Dautrich Jr.": (r"Jonathan L. {Dautrich Jr.}", r"DautrichJr"),
    r"D. Dellamonica Jr.": (r"Domingos {Dellamonica Jr.}", r"DellamonicaJr"),
    r"Domingos Dellamonica Jr.": (r"Domingos {Dellamonica Jr.}", r"DellamonicaJr"),
    r"Thomas W. Doeppner Jr.": (r"Thomas W. {Doeppner Jr.}", r"DoeppnerJr"),
    r"John E. Gaffney Jr.": (r"John E. {Gaffney Jr.}", r"GaffneyJr"),
    r"Gaspar Garcia Jr.": (r"Gaspar {Garcia Jr.}", r"GarciaJr"),
    r"Daniel E. Geer Jr.": (r"Daniel E. {Geer Jr.}", r"GeerJr"),
    r"Dennis M. Healy Jr.": (r"Dennis M. {Healy Jr.}", r"HealyJr"),
    r"M. J. Jacobson Jr.": (r"Michael J. {Jacobson Jr.}", r"JacobsonJr"),
    r"Michael J. Jacobson Jr.": (r"Michael J. {Jacobson Jr.}", r"JacobsonJr"),
    r"Robert J. Jenkins Jr.": (r"Robert J. {Jenkins Jr.}", r"JenkinsJr"),
    r"Burton S. Kaliski Jr.": (r"Burton S. {Kaliski Jr.}", r"KaliskiJr"),
    r"Thomas F. Knight Jr.": (r"Thomas F. {Knight Jr.}", r"KnightJr"),
    r"Hendrik W. Lenstra Jr.": (r"Hendrik W. {Lenstra Jr.}", r"LenstraJr"),
    r"Witold Lipski Jr.": (r"Witold {Lipski Jr.}", r"LipskiJr"),
    r"Juan Lopez Jr.": (r"Juan {Lopez Jr.}", r"Juan LopezJr"),
    r"David M. Martin Jr.": (r"David M. {Martin Jr.}", r"MartinJr"),
    r"William K. Moses Jr.": (r"William K. {Moses Jr.}", r"MosesJr"),
    r"Robert McNerney Jr.": (r"Robert {McNerney Jr.}", r"McNerneyJr"),
    r"Walter R. Mebane Jr.": (r"Walter R. {Mebane Jr.}", r"MebaneJr"),
    r"William K. Moses Jr.": (r"William K. {Moses Jr.}", r"MosesJr"),
    r"Jorge Nakahara Jr.": (r"Jorge {Nakahara Jr.}", r"NakaharaJr"),
    r"David B. Newman Jr.": (r"David B. {Newman Jr.}", r"NewmanJr"),
    r"Nick L. Petroni Jr.": (r"Nick L. {Petroni Jr.}", r"PetroniJr"),
    r"Marcos A. Simpl[íi]cio Jr.": (r"Marcos A. {Simpl{\'\i}cio Jr.}", r"SimplicioJr"),
    r"Guy L. Steele Jr.": (r"Guy L. {Steele Jr.}", r"SteeleJr"),
    r"Samuel S. Wagstaff Jr.": (r"Samuel S. {Wagstaff Jr.}", r"WagstaffJr"),
}

author_subs_re_compiled = {
    re.compile(r): s
    for r, s in author_subs_re.items()
}
author_subs_re_all = re.compile("^" + "|".join(list(author_subs_re.keys())) + "$")


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
        for r, s in author_subs_re_compiled.items():
            if r.match(text):
                return s

    if author_subs_re_all.match(author):
        s = get_match(author)
        if isinstance(s, str):
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
        translation_table[int(codepoint, 16)] = "{" + str(latex) + "}"
# remove \i which is no more used and create issues https://tex.stackexchange.com/a/385250/34384
# https://github.com/cryptobib/db/issues/96
translation_table[0x00ec] = r"{\`i}"
translation_table[0x00ed] = r"{\'i}"
translation_table[0x00ee] = r"{\^i}"
translation_table[0x00ef] = r"{\"i}"

def unicode_to_latex(s):
    """ transform a unicode string to a ascii string with latex symbols """
    s = str(s).translate(translation_table)
    s = s.replace("\x96", "---")
    s = s.replace("\u200e", "")
    s = s.replace("\x92", "'")
    s = s.replace("\x93", "``")
    s = s.replace("\x94", "''")
    s = s.replace("\u03a3", r"$\Sigma$")
    s = s.replace("z\u030c", r"{\v{z}}")
    return s


def get_url(url, exit_on_failure=True, encoding="utf-8"):
    """ return the content of the url (in unicode) """
    waitsec = 60
    while True:
        try:
            f = urllib.request.urlopen(url)
            content = f.read().decode(encoding)
            return content
        except urllib.error.HTTPError as e:
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
    names = [n.strip() for n in pattern_split_authors.split(s)]
    names = [n for n in names if n != '']
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
        return " ".join(author.split(" ")[:-1])
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

html_parser = html.parser.HTMLParser()


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
    s = unicode_to_latex(s.replace(' "', " ``").replace('"', "''"))
    if s.isdigit():
        return s
    else:
        return '"' + s + '"'


def xml_get_value(e):
    """ get the value of the tag "e" (including subtags) """
    return (e.text or '') + ''.join(xml.etree.ElementTree.tostring(ee, encoding="unicode") for ee in e)


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
            authors.append(get_author_name_and_for_key(clean_author(str(e.text))))
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
    entry["author"] = html_to_bib_value((" and \n" + " " * 18).join(authors_bibtex))

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
        for k in sorted(iter(entry.keys()), key=key_sort):
            v = entry[k]
            try:
                v_ascii = v.encode("ascii").decode()
            except UnicodeEncodeError as ex:
                logging.warning(
                    "Problem of encoding in entry \"{0}\", key \"{1}\", value \"{2}\" -> replace bad caracter(s) with '?'".format(
                        key, k, repr(v)))
                v_ascii = v.encode("ascii", "replace").decode()
            if ("<" in v_ascii) or (">" in v_ascii) or ("&" in v_ascii):
                logging.warning(
                    "Character <, >, or & in entry \"{0}\", key \"{1}\", value \"{2}\"".format(key, k, repr(v)))
            f.write("  {0:<15}{1},\n".format((k + " ="), v_ascii))
        f.write("}\n\n")
    except UnicodeEncodeError as ex:
        logging.exception("Problem of encoding of:\n" + repr((key, entry)))


def can_write(filename, overwrite=False):
    """ check whether we can write to the file (ask the user if overwrite=False and the file already exists) """
    if overwrite == False and os.path.exists(filename):
        print("File \"{0}\" already exists. Do you want to delete it (Y/N) ?".format(filename))
        rep = ""
        while rep.lower() not in ["y", "n", "yes", "no"]:
            rep = input()
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
    fields_add = dict(((key, subs(value)) for key, value in conf_dict["fields_add"].items()))

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
                make_brackets_balanced(fix_eprint_spaces(html.unescape(pub.group(3)))),
                True
            )
            authors = split_authors(fix_eprint_spaces(html.unescape(pub.group(4))))
            authors = [get_author_name_and_for_key(a) for a in authors] # list of pairs (full author name, last name for BibTeX key)

            entry["howpublished"] = '"Cryptology ePrint Archive, Report {}/{}"'.format(entry["year"], eprint_id)
            entry["note"] = '"\\url{{https://eprint.iacr.org/{}/{}}}"'.format(entry["year"], eprint_id)
            entry["author"] = html_to_bib_value((" and \n" + " " * 18).join(a[0] for a in authors))

            key = authors_to_key([a[1] for a in authors], confkey, short_year)

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
        for pub in re.finditer(r'href="(https://dblp.uni-trier.de/rec/(?:bibtex/|xml/|)(?:conf|journals)/[^"]*.xml)"',
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
    f = open(filename, "w")

    pattern_eprint = re.compile(r"^\"Cryptology ePrint Archive, Report (\d*)/(\d*)\"")

    def sort_pages(xxx_todo_changeme):
        (k, e) = xxx_todo_changeme
        if "howpublished" in e:
            howpublished = e["howpublished"]

            match_eprint = pattern_eprint.match(e["howpublished"])
            if match_eprint:
                # special case for eprint:
                # we cannot use directly howpublished for eprint because of eprint number > 1000
                # as the format is "Cryptology ePrint Archive, Report yyyy/xxx"
                howpublished = "{:0>4d}/{:0>5d}".format(
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

    for (key, e) in sorted(iter(entries.items()), key=sort_pages):
        fields_add_cur = fields_add.copy()
        if "month" in fields_add_cur and fields_add_cur["month"] == "%months":
            fields_add_cur["month"] = conf_dict["months"][int(e["number"]) - 1]
        write_entry(f, key, dict(fields_add_cur, **e), entry_type)
    f.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", dest="overwrite", action="store_true", help="overwrite existing files")
    parser.add_argument("confyears", metavar="confyear", type=str,
                        help="list of conferences (ex.: C2012 AC11 STOC95 C2013-1)", nargs="*")
    args = parser.parse_args()

    for conf_year in args.confyears:
        res = re.search(r'^([a-zA-Z]+)([0-9]{2,4})([a-zA-Z0-9_-]*)$', conf_year)
        if res is None:
            logging.error(
                "bad format for conference \"{0}\" (ex.: C2012 AC11 STOC95 C2013-1)".format(conf_year))
            sys.exit(1)
        confkey = res.group(1)
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
