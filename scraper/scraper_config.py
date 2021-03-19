from utils.config_manager import ConfigManager

class ScraperConfig():
    def __init__(self, local_machine):
        "scraper_configuration은 static, local_machine은 dynamic 성격을 가짐."
        self.__file_local_machine = local_machine
        self.__manager_local_machine = ConfigManager(self.__file_local_machine)
        self.__url_updated = None
        # self.__url = self.get_base_url()

    # def get_base_url(self):
    #     if self.__url_updated is None:
    #         ret = self.get_config_scraper('url')
    #     else:
    #         ret = self.__url_updated

    #     return ret

    # def set_base_url(self, base_url):
    #     ''' 이것은 임시 설정임. persistent data가 아님
    #     url 숫자 올라갔을때, 임시로 변경하기 위한 설정. '''
    #     self.__url_updated = base_url
    #     self.__url = self.get_base_url()

    # def get_url(self):
    #     return self.__url

    # def get_site(self):
    #     return self.__site

    # def get_config_local(self, attr):
    #     attr = "%s-%s" % (self.__site, attr)
    #     return self.__manager_local_machine.get_attr_config(attr)

    # def set_config_local(self, attr, value):
    #     attr = "%s-%s" % (self.__site, attr)
    #     self.__manager_local_machine.set_attr_config(attr, value)

    # def get_config_scraper(self, attr):
    #     attr = "%s-%s" % (self.__site, attr)
    #     return self.__manager_scraper_configuration.get_attr_config(attr)

    # def set_config_scraper(self, attr, value):
    #     attr = "%s-%s" % (self.__site, attr)
    #     self.__manager_scraper_configuration.set_attr_config(attr, value)
