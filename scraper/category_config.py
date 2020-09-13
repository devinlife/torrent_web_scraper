from utils.config_manager import ConfigManager

class CategoryConfig():
    def __init__(self, site, category, scraper_configuration, local_machine):
        "scraper_configuration은 static, local_machine은 dynamic 성격을 가짐."
        self.__site = site
        self.__category = category
        self.__file_scraper_configuration = scraper_configuration
        self.__manager_scraper_configuration = ConfigManager(self.__file_scraper_configuration)
        self.__file_local_machine = local_machine
        self.__manager_local_machine = ConfigManager(self.__file_local_machine)
        self.__url = self.get_base_url() + self.get_config_scraper('url')

    def get_base_url(self):
        return self.__manager_scraper_configuration.get_attr_config('%s-url' % self.__site)

    def get_url(self):
        return self.__url

    def get_site(self):
        return self.__site

    def get_category(self):
        return self.__category

    def get_config_local(self, attr):
        attr = "%s-%s-%s" % (self.__site, self.__category, attr)
        return self.__manager_local_machine.get_attr_config(attr)

    def set_config_local(self, attr, value):
        attr = "%s-%s-%s" % (self.__site, self.__category, attr)
        self.__manager_local_machine.set_attr_config(attr, value)

    def get_config_scraper(self, attr):
        attr = "%s-%s-%s" % (self.__site, self.__category, attr)
        return self.__manager_scraper_configuration.get_attr_config(attr)

    def set_config_scraper(self, attr, value):
        attr = "%s-%s-%s" % (self.__site, self.__category, attr)
        self.__manager_scraper_configuration.set_attr_config(attr, value)
