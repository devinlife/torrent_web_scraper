from abc import ABCMeta, abstractmethod
from utils.magnet_info import MagnetInfo
from utils.title_checker import TitleChecker
from utils.web_delegate import WebDelegate
from utils.history_delegate import HistoryDelegate
from utils.transmission_delegate import TransmissionDelegate

from scraper.board_item_iterator import BoardItemIterator
from scraper.board_page_iterator import BoardPageIterator
from scraper.system_config import SystemConfig
from scraper.scraper_config import ScraperConfig
from scraper.category_config import CategoryConfig

import re

class ScraperTemplate(metaclass=ABCMeta):
    def __init__(self, name, scraper_configuration_file,
            local_machine_status_file, local_machine_history_file):
        self.name = name
        self.__categories = []
        self.__title_checker = TitleChecker()
        self.__web_delegate = WebDelegate()

        self.__scraper_configuration_file = scraper_configuration_file
        self.__local_machine_status_file = local_machine_status_file
        self.__system_config = SystemConfig(self.__scraper_configuration_file,
                self.__local_machine_status_file)
        self.__scraper_config = ScraperConfig(self.name,
                self.__scraper_configuration_file, self.__local_machine_status_file)
        self.__local_machine_history_file = local_machine_history_file
        self.__history_delegate = HistoryDelegate(self.__local_machine_history_file)

        trans_id = self.__system_config.get_config_local("trans-id")
        trans_pw = self.__system_config.get_config_local("trans-pw")
        trans_host = self.__system_config.get_config_local("trans-host")
        trans_port = self.__system_config.get_config_local("trans-port")

        self.__transmission_delegate = TransmissionDelegate(trans_id, trans_pw,
                trans_host, trans_port, self.history_delegate)

    def __str__(self):
        return self.name

    @property
    def categories(self):
        return self.__categories

    @property
    def web_delegate(self):
        return self.__web_delegate

    @property
    def history_delegate(self):
        return self.__history_delegate

    def check_site_alive(self):
        '''각 site가 살아있는지 확인'''
        return self.web_delegate.check_url_alive(self.__scraper_config.get_config_scraper('url'))

    def correct_url(self):
        '''접속불가 토렌트 사이트 URL 순회 접속시도'''
        base = self.__scraper_config.get_config_scraper('url')
        start_num = int(re.findall(r'\d+', base)[0])
        for num in range(start_num, start_num+5):
            try_url = re.sub('[0-9]+', str(num), base)
            print("Looking for.. ", try_url)
            if self.web_delegate.check_url_alive(try_url):
                print('The new torrent site found!!.\n')
                self.__scraper_config.set_base_url(try_url)
                return True

        print('Fail to find a new torrent site.')           
        return False

    def aggregation_categories(self):
        '''json parsing으로 site 내의 categories 생성'''
        categories = [x.strip() for x in
                self.__scraper_config.get_config_scraper('categories').split(',')]

        if len(categories) == 1 and categories[0] is "":
            print("Scrapping for this site is disabled.")
            categories = []

        for category_name in categories:
            _ = CategoryConfig(self.name, category_name,
                    self.__scraper_configuration_file,
                    self.__local_machine_status_file,
                    self.__scraper_config.get_base_url())
            self.__categories.append(_)

        print("Aggregation categories for : " + str(self))
        for category in self.categories:
            print("\t" + category.get_category() + " : " + category.get_url())

    @abstractmethod
    def parse_page_data(self, url):
        pass

    @abstractmethod
    def parse_magnet_from_page_url(self, url):
        pass

    @abstractmethod
    def get_board_id_num(self, url):
        pass

    def execute_scraper(self):
        for category in self.__categories:
            self.__execute_scraper_for_category(category)

    def __execute_scraper_for_category(self, category):
        '''category는 class CategoryConfig()가 전달된 것임'''

        base = category.get_base_url()
        url = category.get_config_scraper('url')
        strt_index = int(self.__scraper_config.get_config_scraper('start-index'))
        max_page = int(self.__scraper_config.get_config_scraper('max-page'))
        page_iterator = BoardPageIterator(base + url, strt_index, max_page)
        _ = category.get_config_local('history')

        ''' new_latest_id은 게시물을 순회하면서 최신 id로 업데이트됨.
        config_latest_id은 업데이트 되면 안됨. 지난 history 확인 용임. '''
        new_latest_id = 0 if _ is None else _
        config_latest_id = new_latest_id
        print("read new_latest_id : %d" % new_latest_id)

        '''웹사이트의 page 별로 iter 순회'''
        for page in page_iterator:
            board_list = self.parse_page_data(page)
            item_iterator = BoardItemIterator(board_list)

            '''한 page 내의 list item을  iter 순회'''
            for title, href in item_iterator:
                """board_id_num을 만들어내는 방법이 web별로 달라서 iterator에서
                할 수 없음."""

                board_id_num = self.get_board_id_num(href)
                #print("DEBUG : %d, %s" % (board_id_num, title))

                if board_id_num > 0:
                    if board_id_num > new_latest_id:
                        new_latest_id = board_id_num
                    if board_id_num < config_latest_id:
                        page_iterator.mark_for_early_stop()
                        item_iterator.mark_for_early_stop()
                else:
                    print("board_id_num is wrong, can't update latest ID - %d." % board_id_num)

                #print("info: parse info=\t[%s][%s][%d] - %s"
                #        % (self.name, category.get_category(), board_id_num, title))

                matched_name = self.__title_checker.validate_board_title(title)
                if not matched_name:
                    #print("Not matched_name ", title)
                    continue

                magnet = self.parse_magnet_from_page_url(href)
                if magnet is None:
                    continue

                magnet_info = MagnetInfo(title, magnet, matched_name, self.name)
                ret = self.__transmission_delegate.add_magnet_transmission_remote(magnet_info)
                if not ret:
                    continue

                #TODO: remove_transmission_remote method는 pass 상태임
                self.__transmission_delegate.remove_transmission_remote(matched_name)

        category.set_config_local('history', new_latest_id)
