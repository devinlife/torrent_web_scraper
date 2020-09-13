import sys
from utils.json_parser import JsonParser

class ConfigManager():
    def __init__(self, setfileName):
        self.__config_file = setfileName

        #TO-DO: 다른 확장자들도 지원하면 interface 추가 필요
        file_ext = self.__config_file.partition(".")[-1]
        if file_ext == 'json':
            self.__delegate = JsonParser(self.__config_file)
        else:
            print("File extention, %s is not support." % file_ext)
            sys.exit()

    #TO-DO: property 사용하려면 작업 필요
    #def __getattr__(self, attr_string):
    #def __setattr__(self, attr_string, value):

    def get_attr_config(self, key):
        return self.__delegate.get_key_value(key)

    def set_attr_config(self, key, value):
        return self.__delegate.set_key_value(key, value)
