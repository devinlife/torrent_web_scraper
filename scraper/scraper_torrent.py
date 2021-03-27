from scraper.scraper import ScraperTemplate
import re


class ScraperTorrent(ScraperTemplate):
    def __init__(self, local_machine_status_file, local_machine_badsites_file, local_machine_history_file, pages_to_scrap):
        super().__init__(local_machine_status_file,
                         local_machine_badsites_file, local_machine_history_file, pages_to_scrap)

    def collect_goodsites(self):
        return self.torrent_sites_delegate.collect_goodsites()

    def parse_page_data(self, url):

        try:
            soup = self.web_delegate.get_web_data(url)
            _ = soup.find('div', attrs={'class': 'list-board'})
            _list = _.find_all('div', attrs={'class': 'wr-subject'})
            name_list = []
            for item in _list:
                a_tag = item.find('a', href=re.compile('.*wr_id.*'))
                title = a_tag.get_text().strip()
                href = a_tag['href']
                name_list.append([title, href])
            return name_list

        except:
            _ = soup.find('div', attrs={'class': 'tbl_head01 tbl_wrap'})
            _list = _.find_all('div', attrs={'class': 'bo_tit'})
            name_list = []
            for item in _list:
                a_tag = item.find('a', href=re.compile('.*wr_id.*'))
                title = a_tag.get_text().strip()
                href = a_tag['href']
                name_list.append([title, href])
            return name_list

    def parse_magnet_from_page_url(self, url):
        bs_obj = self.web_delegate.get_web_data(url)
        magnet = None
        if not bs_obj == None:
            magnet_item = bs_obj.find('a', href=re.compile(".*magnet.*"))
            if not magnet_item == None:
                magnet = magnet_item.get('href')
        return magnet
