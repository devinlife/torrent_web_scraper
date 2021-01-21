from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

class WebDelegate:
    def __init__(self, parser_engine=BeautifulSoup):
        #TO-DO: default parser engine은 BeautifulSoup. 필요시 추가.
        self.__parser_engine=parser_engine

    def get_web_data(self, addr):
        req = Request(addr, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req).read().decode('utf-8','replace')
        data = self.__parser_engine(html, "html.parser")
        return data

    def check_url_alive(self, addr):
        try:
            req = Request(addr, headers={'User-Agent': 'Mozilla/5.0'})
            html = urlopen(req)
            if html.status >= 300: # 3xx Redirection부터 에러 처리
                return False
            self.get_web_data(addr)
        except Exception as e:
            print("Exception access url : %s" % e)
            print("We can not scrap %s, something wrong.\n" % addr)
            return False

        return True
