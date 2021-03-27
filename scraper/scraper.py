from abc import ABCMeta, abstractmethod
from utils.magnet_info import MagnetInfo
from utils.title_checker import TitleChecker
from utils.title_checker import Item
from utils.web_delegate import WebDelegate
from utils.history_delegate import HistoryDelegate
from utils.transmission_delegate import TransmissionDelegate
from utils.torrent_sites_delegate import TorrentSitesDelegate
from utils.file_move import FileMover

from scraper.board_item_iterator import BoardItemIterator
from scraper.board_page_iterator import BoardPageIterator
from scraper.system_config import SystemConfig

import re


class ScraperTemplate(metaclass=ABCMeta):
    def __init__(self, local_machine_status_file, local_machine_badsites_file, local_machine_history_file, pages_to_scrap):
        self.__web_delegate = WebDelegate()
        self.__local_machine_status_file = local_machine_status_file
        self.__local_machine_badsites_file = local_machine_badsites_file
        self.__pages_to_scrap = pages_to_scrap
        self.__system_config = SystemConfig(self.__local_machine_status_file)
        self.__local_machine_history_file = local_machine_history_file
        self.__history_delegate = HistoryDelegate(
            self.__local_machine_history_file)

        trans_id = self.__system_config.get_config_local("trans-id")
        trans_pw = self.__system_config.get_config_local("trans-pw")
        trans_host = self.__system_config.get_config_local("trans-host")
        trans_port = self.__system_config.get_config_local("trans-port")
        media_folder = self.__system_config.get_config_local("media-folder")

        self.__title_checker = TitleChecker(media_folder)
        self.__transmission_delegate = TransmissionDelegate(
            trans_id, trans_pw, trans_host, trans_port, media_folder, self.history_delegate)
        self.__torrent_sites_delegate = TorrentSitesDelegate(
            self.__local_machine_badsites_file, self.web_delegate)
        self.__file_move = FileMover(
            media_folder, self.__title_checker.tvlist())

    @property
    def torrent_sites_delegate(self):
        return self.__torrent_sites_delegate

    @property
    def filemove(self):
        return self.__file_move

    @property
    def web_delegate(self):
        return self.__web_delegate

    @property
    def history_delegate(self):
        return self.__history_delegate

    # def check_site_alive(self):
    #     '''각 site가 살아있는지 확인'''
    #     return self.web_delegate.check_url_alive(self.__scraper_config.get_config_scraper('url'))

    def aggregation_categories(self, goodsite):

        categories = []
        categories_return = []

        try:
            soup = self.web_delegate.get_web_data(goodsite)
            categories_list = ['예능', '드라마', '영화', '시사', '방송', 'TV프로', '다큐']

            for item in soup.find_all('a'):
                try:
                    for category in categories_list:
                        if (category in item.text):
                            href = item.get("href")
                            h = re.compile(
                                "bbs[/]board[.]php[?]bo[_]table[=](?!basic$|review$|board[0-9]$)[a-z]+[0-9]?$")
                            h_tail = h.findall(href)
                            if h_tail is not []:
                                href = goodsite + h_tail[0] + '&page='
                                categories.append(href)
                except:
                    pass
        except:
            pass

        if len(categories) is 0:
            self.__torrent_sites_delegate.add_failsite_to_badsites(goodsite)
            return

        else:
            for a in categories:
                categories_return.append(a)
            categories_return = list(set(categories))
        return categories_return

    @ abstractmethod
    def parse_page_data(self, url):
        pass

    @ abstractmethod
    def parse_magnet_from_page_url(self, url):
        pass

    def execute_scraper(self, categories):

        for category in categories:
            self.__execute_scraper_for_category(category)

    def __execute_scraper_for_category(self, category):
        page_iterator = BoardPageIterator(
            category, int(1), self.__pages_to_scrap)

        try:
            for page in page_iterator:
                # print(page)
                board_list = self.parse_page_data(page)
                item_iterator = BoardItemIterator(board_list)

                '''한 page 내의 list item을  iter 순회'''
                for title, href in item_iterator:
                    matched_name = self.__title_checker.validate_board_title(
                        title)
                    if not matched_name:
                        continue
                    magnet = self.parse_magnet_from_page_url(href)
                    if magnet is None:
                        continue
                    magnet_info = MagnetInfo(title, magnet, matched_name)
                    ret = self.__transmission_delegate.add_magnet_transmission_remote(
                        magnet_info)
                    if not ret:
                        continue

        except:
            pass

    def end(self):
        self.__file_move.arrange_files()

        try:
            for tvtitle in self.__title_checker.tvlist():
                self.__transmission_delegate.remove_transmission_remote(
                    tvtitle)
        except:
            pass

        self.__file_move.delete_folders()
