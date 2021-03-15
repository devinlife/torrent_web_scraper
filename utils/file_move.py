import os
import shutil
import json
from local_config.program_list import title_list


class FileMover():
    def __init__(self, scraper_configuration_file):
        self.__tvtitles = []
        self.__folderlist = []
        self.__filelist = []

        for tvtitle in title_list:
            self.__tvtitles.append(tvtitle[0].strip())

        with open(scraper_configuration_file, 'r') as f:
            self.__datafile = json.load(f)
        self.__download_folder = self.__datafile['download-folder']
        self.__plex_folder = self.__datafile['plex-folder']

        self.collect_files()
        self.delete_folders()
        self.move_files()

    def collect_files(self):
        try:
            for path, dirs, files in os.walk(self.__download_folder):
                if files:
                    for file in files:
                        for tvtitle in self.__tvtitles:
                            if file.find(tvtitle) > -1:
                                if not os.path.isfile(self.__plex_folder + file):
                                    os.rename(path + '/' + file,
                                              self.__plex_folder + '/' + file)
        except Exception as e:
            print(e)

    def delete_folders(self):
        try:
            for dirs in os.walk(self.__download_folder):
                for tvtitle in self.__tvtitles:
                    if dirs[0].find(tvtitle) > -1:
                        shutil.rmtree(dirs[0])
        except Exception as e:
            print(e)

    def move_file(self, file, media_folder):
        tmp_file = os.path.basename(file)
        tmp_file = media_folder + '/' + tmp_file
        if os.path.exists(tmp_file):
            os.remove(file)
        else:
            shutil.move(file, media_folder)

    def move_files(self):
        try:
            filenames = os.listdir(self.__plex_folder)
            for filename in filenames:
                full_filename = os.path.join(self.__plex_folder, filename)
                if os.path.isdir(full_filename):
                    self.__folderlist.append(full_filename)
                    continue
                else:
                    self.__filelist.append(full_filename)
        except PermissionError:
            pass

        for file in self.__filelist:
            for tvtitle in self.__tvtitles:
                if file.find(tvtitle) > -1:
                    media_folder = os.path.join(self.__plex_folder, tvtitle)
                    try:
                        if not os.path.isdir(media_folder):
                            os.mkdir(media_folder)
                    except:
                        break
                    self.move_file(file, media_folder)
                    break
