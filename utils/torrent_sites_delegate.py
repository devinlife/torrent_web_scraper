import os
import sys
import pandas as pd

from csv import writer
from googlesearch import search


class TorrentSitesDelegate:
    def __init__(self, local_machine_badsites_file, web_delegate):
        self.__web_delegate = web_delegate
        self.__badsites_file = local_machine_badsites_file
        self.__anchors = []
        self.__badsites = []
        self.__ranksites = []

    def collect_goodsites(self):
        query = "토렌트 순위"
        for g in search(query, tld='co.kr', num=10, stop=3):
            self.__ranksites.append(g)
        for ranksite in self.__ranksites:
            try:
                soup = self.__web_delegate.get_web_data(ranksite)
                exclude = 'http://jaewook.net', 'https://lsrank.com', \
                    'https://twitter.com', 'https://ps.devbj.com', \
                    'https://torrentrank.net', 'https://github.com', \
                    'https://www.torrentdia', 'https://www.instagram.com'
                for anchor in soup.find_all('a'):
                    if anchor.get('href').startswith('http') and not anchor.get('href').startswith(exclude):
                        if not anchor.get('href').endswith('/'):
                            tmp = anchor.get('href') + '/'
                            self.__anchors.append(tmp)
                        else:
                            self.__anchors.append(anchor.get('href'))
            except:
                pass

        df = pd.read_csv(self.__badsites_file, names=['badsite'])
        self.__badsites = df.badsite.to_list()
        goodsites = list(set(self.__anchors)-set(self.__badsites))

        print("{} torrent sites are founded.".format(len(goodsites)))
        return goodsites

    def add_failsite_to_badsites(self, goodsite):
        with open(self.__badsites_file, 'a+', encoding='utf-8', newline='') as write_obj:
            badsite = [[goodsite]]
            csv_writer = writer(write_obj)
            csv_writer.writerow(badsite[0])
            print("\tThis site will be delisted.")
