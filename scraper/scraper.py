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
from scraper.scraper_config import ScraperConfig
from scraper.category_config import CategoryConfig

import re


class ScraperTemplate(metaclass=ABCMeta):
    def __init__(self, local_machine_status_file, local_machine_badsites_file, local_machine_history_file):
        self.__categories = []
        self.__web_delegate = WebDelegate()    
        
        self.__local_machine_status_file = local_machine_status_file
        self.__local_machine_badsites_file = local_machine_badsites_file
        self.__system_config = SystemConfig(self.__local_machine_status_file)
        self.__scraper_config = ScraperConfig(self.__local_machine_status_file)
        self.__local_machine_history_file = local_machine_history_file
        self.__history_delegate = HistoryDelegate(self.__local_machine_history_file)

        trans_id = self.__system_config.get_config_local("trans-id")
        trans_pw = self.__system_config.get_config_local("trans-pw")
        trans_host = self.__system_config.get_config_local("trans-host")
        trans_port = self.__system_config.get_config_local("trans-port")
        media_folder = self.__system_config.get_config_local("media-folder")

        self.__title_checker = TitleChecker(media_folder)   
        self.__transmission_delegate = TransmissionDelegate(trans_id, trans_pw, trans_host, trans_port, media_folder, self.history_delegate)
        self.__torrent_sites_delegate = TorrentSitesDelegate(self.__local_machine_badsites_file)
        self.__file_move=FileMover(media_folder, self.__title_checker.tvlist())
        self.failtoconnect=None

        _ = self.__aggregation_categories__()

    @property
    def categories(self):
        return self.__categories

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

    def __aggregation_categories__(self):
        '''json parsing으로 site 내의 categories 생성'''
        head = '/bbs/board.php?bo_table='
        tail = '&page='
        categories = ['drama', 'enter', 'entertain', 'tv', 'sisa']

        for category in categories:
            self.__categories.append(head + category + tail)

        # if len(categories) == 1 and categories[0] is "":
        #     print("Scrapping for this site is disabled.")
        #     categories = []

    @abstractmethod
    def parse_page_data(self, url):
        pass

    @abstractmethod
    def parse_magnet_from_page_url(self, url):
        pass

    def execute_scraper(self, goodsite):
        self.failtoconnect = 0
        for category in self.__categories:
            self.__execute_scraper_for_category(category, goodsite)
                # 카테고리 중에 4개 이상 접속불가 사이트 badsites에 추가
        if self.failtoconnect >= 4:
            self.__torrent_sites_delegate.add_failsite_to_badsites(goodsite)

    def __execute_scraper_for_category(self, category, goodsite):
        page_iterator = BoardPageIterator(goodsite + category, int(1), int(5))

        try:
            for page in page_iterator:
                board_list = self.parse_page_data(page)
                item_iterator = BoardItemIterator(board_list)

                '''한 page 내의 list item을  iter 순회'''
                for title, href in item_iterator:
                    matched_name = self.__title_checker.validate_board_title(title)
                    if not matched_name:
                        #print("Not matched_name ", title)
                        continue
                    magnet = self.parse_magnet_from_page_url(href)
                    if magnet is None:
                        continue

                    magnet_info = MagnetInfo(title, magnet, matched_name)
                    ret = self.__transmission_delegate.add_magnet_transmission_remote(magnet_info)
                    if not ret:
                        continue

                    # TODO: remove_transmission_remote method는 pass 상태임
                    self.__transmission_delegate.remove_transmission_remote(matched_name)
        except:
            self.failtoconnect = self.failtoconnect + 1

        # category.set_config_local('history', new_latest_id)
