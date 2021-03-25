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
        self.__anchors = []
        self.__badsites = []
        self.__ranksites = []
        self.__refined_anchors = []

    def collect_goodsites(self):
        query = "토렌트 순위"
        for g in search(query, tld='com', num=5, stop=2):
            self.__ranksites.append(g)
        for ranksite in self.__ranksites:
            try:
                with urlopen(ranksite) as response:
                    soup = BeautifulSoup(response, 'html.parser')
                    for anchor in soup.find_all('a'):
                        self.__anchors.append(anchor.get('href'))
                    anchors_http = [
                        x for x in self.__anchors if x.startswith('http')]
                    exclude = 'http://jaewook.net', 'https://lsrank.com/'
                    anchors_exclude = [
                        x for x in anchors_http if not x.startswith(exclude)]
                    for anchor in anchors_exclude:
                        if not anchor.endswith('/'):
                            anchor = anchor + '/'
                        self.__refined_anchors.append(anchor)
            except:
                pass
        df = pd.read_csv(self.__badsites_file, names=['badsite'])
        self.__badsites = df.badsite.to_list()
        goodsites = list(set(self.__refined_anchors)-set(self.__badsites))
        print("{} torrent sites are founded.".format(len(goodsites)+1))
        return goodsites

    def add_failsite_to_badsites(self, goodsite):
        with open(self.__badsites_file, 'a+', encoding='utf-8', newline='') as write_obj:
            badsite = [[goodsite]]
            csv_writer = writer(write_obj)
            csv_writer.writerow(badsite[0])
            print("\tThis site will be delisted.")
