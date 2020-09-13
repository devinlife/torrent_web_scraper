import json

class JsonParser:
    def __init__(self, setfileName):
        self.__json_file = setfileName
        self.__data = {}

    def __get_json_data(self):
        try:
            data_file = open(self.__json_file, 'r')
        except FileNotFoundError as e:
            self.__data = {}
        else:
            self.__data = json.load(data_file)
            data_file.close()

        return self.__data

    def get_key_value(self, key):
        self.__get_json_data()
        if key in self.__data:
            return self.__data[key]
        return None

    def set_key_value(self, key, value):
        self.__get_json_data()
        try:
            with open(self.__json_file, 'w', encoding='utf-8') as data_file:
                self.__data[key] = value
                json.dump(self.__data, data_file, sort_keys = True, ensure_ascii=False, indent=4)
        except:
            print("JsonParser set_key_value Exception!!")
            return False
        return True

    def dump(self):
        data_file = open(self.__json_file, 'r')
        _data = json.load(data_file)

        for key in _data.keys():
            print("{} : {}".format(key, _data[key]))
