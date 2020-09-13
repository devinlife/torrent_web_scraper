from utils.config_manager import ConfigManager

class SystemConfig():
    def __init__(self, scraper_configuration, local_machine):
        "scraper_configuration은 static, local_machine은 dynamic 성격을 가짐."
        self.__file_scraper_configuration = scraper_configuration
        self.__manager_scraper_configuration = ConfigManager(self.__file_scraper_configuration)
        self.__file_local_machine = local_machine
        self.__manager_local_machine = ConfigManager(self.__file_local_machine)

    def get_config_local(self, attr):
        return self.__manager_local_machine.get_attr_config(attr)

    def set_config_local(self, attr, value):
        self.__manager_local_machine.set_attr_config(attr, value)

    def get_config_scraper(self, attr):
        return self.__manager_scraper_configuration.get_attr_config(attr)

    def set_config_scraper(self, attr, value):
        self.__manager_scraper_configuration.set_attr_config(attr, value)
