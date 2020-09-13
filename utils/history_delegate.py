import csv
import os.path

class HistoryDelegate:
    def __init__(self, historyFile):
        self.__csv_file = historyFile

        #if not os.path.isfile(self.__csv_file):
        if not self.__exist_history_file():
            try:
                open(self.__csv_file, 'x')
            except:
                print("HistoryDelegate: __init__ Exception!!")

    def __exist_history_file(self):
        if os.path.isfile(self.__csv_file):
            return True
        return False

    def check_magnet_history(self, magnet):
        if not self.__exist_history_file():
            return False

        with open(self.__csv_file, 'r', encoding="utf-8") as f:
            ff = csv.reader(f)
            for row in ff:
                if magnet == row[3]:
                    print("Fail to add magnet for [%s] which was already downloaded." % row[2])
                    return True
        return False

    def add_magnet_info_to_history(self, magnet_story):
        "magnet_story는 magnet 정보를 담은 list"
        with open(self.__csv_file, 'a', newline = '\n', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(magnet_story)
        f.close()
        return
