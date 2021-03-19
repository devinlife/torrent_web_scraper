from scraper.scraper import ScraperTemplate
import re


class ScraperTorrent(ScraperTemplate):
    def __init__(self, local_machine_status_file, local_machine_badsites_file, local_machine_history_file):
        super().__init__(local_machine_status_file, local_machine_badsites_file, local_machine_history_file)

    def collect_goodsites(self):
        return self.torrent_sites_delegate.collect_goodsites()

    def parse_page_data(self, url):
        bs_obj = self.web_delegate.get_web_data(url)
        #name_list = bs_obj.find('ul', attrs={'class' : 'list-body'}).find_all('a', href=re.compile(".*page.*"))
        _ = bs_obj.find('ul', attrs={'class': 'list-body'})
        _list = _.find_all('div', attrs={'class': 'wr-subject'})
        name_list = []
        href_list = ['.*wr_id.*', '.*page.*']
        for item in _list:
            a_tag = item.find('a', href=re.compile('|'.join(href_list)))
            title = a_tag.get_text().strip()
            href = a_tag['href']
            # name_list는 title과 href 리스트의 리스트로 구성
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
