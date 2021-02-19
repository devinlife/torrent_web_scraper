import os
import shutil
import json
from local_config.program_list import title_list

tvtitles = []
for tvtitle in title_list:
    tvtitles.append(tvtitle[0].strip().lower())


def collect_files(download_folder, plex_folder):
    try:
        for path, dirs, files in os.walk(download_folder):
            if files:
                for file in files:
                    for tvtitle in tvtitles:
                        if file.find(tvtitle) > -1:
                            if not os.path.isfile(plex_folder + file):
                                os.rename(path + '/' + file,
                                          plex_folder + '/' + file)
    except Exception as e:
        print(e)


def delete_folders(download_folder):
    try:
        for dirs in os.walk(download_folder):
            for tvtitle in tvtitles:
                if dirs[0].find(tvtitle) > -1:
                    shutil.rmtree(dirs[0])
    except Exception as e:
        print(e)


def filemove(file, mediaFolder):
    tmp_file = os.path.basename(file)
    tmp_file = mediaFolder + '/' + tmp_file
    if os.path.exists(tmp_file):
        os.remove(file)
    else:
        shutil.move(file, mediaFolder)


def sort(plex_folder):
    folderlist = []
    filelist = []

    try:
        filenames = os.listdir(plex_folder)
        for filename in filenames:
            full_filename = os.path.join(plex_folder, filename)
            if os.path.isdir(full_filename):
                folderlist.append(full_filename)

                continue
            else:
                filelist.append(full_filename)
    except PermissionError:
        pass

    for file in filelist:
        for tvtitle in tvtitles:
            if file.find(tvtitle) > -1:
                media_folder = os.path.join(plex_folder, tvtitle)
                try:
                    if not os.path.isdir(media_folder):
                        os.mkdir(media_folder)
                except:
                    break
                filemove(file, media_folder)
                break


def sorting(scraper_configuration_file):
    with open(scraper_configuration_file, 'r') as f:
        datafile = json.load(f)
    download_folder = datafile['download-folder']
    plex_folder = datafile['plex-folder']
    collect_files(download_folder, plex_folder)
    delete_folders(download_folder)
    sort(plex_folder)
