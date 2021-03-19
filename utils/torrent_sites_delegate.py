import os
import sys
import pandas as pd

from csv import writer
from bs4 import BeautifulSoup
from urllib.request import urlopen
from googlesearch import search

class TorrentSitesDelegate:
    def __init__(self, local_machine_badsites_file):
        self.__badsites_file = local_machine_badsites_file
        self.__anchors =[]
        self.__badsites=[]
        self.__ranksites=[]
        self.__refined_anchors=[]

    def collect_goodsites(self):
        query = "토렌트 순위"
        for g in search(query, tld='com', num=10, stop=5, pause=1.0):
            self.__ranksites.append(g)
        for ranksite in self.__ranksites:
            try:
                with urlopen(ranksite) as response:
                    soup = BeautifulSoup(response, 'html.parser')
                    for anchor in soup.find_all('a'):
                        self.__anchors.append(anchor.get('href'))
                    anchors_http = [x for x in self.__anchors if x.startswith('http')]
                    for anchor in anchors_http:
                        if anchor.endswith('/'):
                            anchor=anchor[:-1]
                        self.__refined_anchors.append(anchor)
            except:
                pass
        df = pd.read_csv(self.__badsites_file, names=['badsite'])
        self.__badsites = df.badsite.to_list()
        goodsites = list(set(self.__refined_anchors)-set(self.__badsites))
        return goodsites

    def add_failsite_to_badsites(self, goodsite):
        with open(self.__badsites_file, 'a+', encoding='utf-8', newline='') as write_obj:
            badsite = [[goodsite]]
            csv_writer = writer(write_obj)
            csv_writer.writerow(badsite[0])
            print("\tThis site will be delisted.")   