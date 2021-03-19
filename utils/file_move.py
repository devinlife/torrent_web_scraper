import os
import shutil


class FileMover():
    def __init__(self, media_folder, tvlist):
        self.__tvlist = tvlist
        self.__media_folder = media_folder
        self.__tvtitles = []
        self.__folders_to_delete = []
        # self.__folderlist = []
        # self.__filelist = []

        for tvtitle in self.__tvlist:
            tmp=" ".join(tvtitle.title)
            self.__tvtitles.append(tmp)

    def arrange_files(self):
        try:
            for tvtitle in self.__tvtitles:
                target_folder = os.path.join(self.__media_folder, tvtitle)
                for path, dirs, files in os.walk(target_folder):
                    if files:
                        for file in files:
                            if (file.endswith('mp4')) and (file.find(tvtitle) > -1) and (path != target_folder):
                                os.rename(path + '/' + file, target_folder + '/' + file)
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
                for folder in self.__folders_to_delete:
                    shutil.rmtree(folder)

        except Exception as e:
            print(e)              
        # for dirs in os.walk(target_folder):
        #     if dirs:
        #         for d in dirs[1]:
        #             full_path = os.path.join(dirs[0], d)
        #             if d.find(tvtitle) > -1:
        #                 shutil.rmtree(full_path)

    # def move_file(self, file, media_folder):
    #     tmp_file = os.path.basename(file)
    #     tmp_file = media_folder + '/' + tmp_file
    #     if os.path.exists(tmp_file):
    #         os.remove(file)
    #     else:
    #         shutil.move(file, media_folder)

    # def move_files(self):
    #     try:
    #         filenames = os.listdir(self.__media_folder)
    #         for filename in filenames:
    #             full_filename = os.path.join(self.__media_folder, filename)
    #             if os.path.isdir(full_filename):
    #                 self.__folderlist.append(full_filename)
    #                 continue
    #             else:
    #                 self.__filelist.append(full_filename)
    #     except PermissionError:
    #         pass

    #     for file in self.__filelist:
    #         for tvtitle in self.__tvtitles:
    #             if file.find(tvtitle) > -1:
    #                 media_folder = os.path.join(self.__media_folder, tvtitle)
    #                 try:
    #                     if not os.path.isdir(media_folder):
    #                         os.mkdir(media_folder)
    #                 except:
    #                     break
    #                 self.move_file(file, media_folder)
    #                 break
