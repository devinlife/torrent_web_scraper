import os
import shutil


class FileMover():
    def __init__(self, media_folder, tvlist):
        self.__tvtitles = tvlist
        self.__media_folder = media_folder
        self.__folders_to_delete = []

    def arrange_files(self):
        try:
            for tvtitle in self.__tvtitles:
                target_folder = os.path.join(self.__media_folder, tvtitle)
                for path, dirs, files in os.walk(target_folder):
                    if files:
                        for file in files:
                            if (file.endswith('mp4')) and (file.find(tvtitle) > -1) and (path != target_folder):
                                os.rename(path + '/' + file,
                                          target_folder + '/' + file)
                                self.__folders_to_delete.append(path)

                for path, dirs, files in os.walk(target_folder):
                    if files:
                        for file in files:
                            if file.startswith('[방영중]') and file.endswith('mp4'):
                                tmp = file.split(']')[1].strip()
                                os.rename(path + '/' + file, path + '/' + tmp)

        except Exception as e:
            print(e)

    def delete_folders(self):
        try:
            if self.__folders_to_delete != []:
                for folder in list(set(self.__folders_to_delete)):
                    shutil.rmtree(folder)

        except Exception as e:
            print(e)
