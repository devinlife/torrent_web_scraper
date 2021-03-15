#!/usr/bin/env python3
import os
import sys
from scraper.scraper_torrentmax import ScraperTorrentmax
from scraper.scraper_torrentsir import ScraperTorrentsir
from utils.file_move import FileMover


def main():

    root_path = os.path.abspath(os.path.dirname(__file__)) + '/'
    local_machine_status_file = root_path + \
        'local_config/local_machine_configuration.json'
    local_machine_history_file = root_path + 'local_config/magnet_history.csv'
    scraper_configuration_file = root_path + 'scraper/scraper_configuration.json'

    scrapers = []

    # Torrentmax
    scraper = ScraperTorrentmax(scraper_configuration_file,
                                local_machine_status_file, local_machine_history_file)
    scrapers.append(scraper)

    # Torrentsir
    scraper = ScraperTorrentsir(scraper_configuration_file,
                                local_machine_status_file, local_machine_history_file)
    scrapers.append(scraper)

    for scraper in scrapers:
        print("Scraper for %s!!!" % scraper.name)
        ret = scraper.check_site_alive()
        if not ret:
            ret = scraper.correct_url()

        if ret:
            scraper.aggregation_categories()
            scraper.execute_scraper()

    # local_machine에 다운로드 폴더 및 플렉스 티비 폴더 작성
    # 플렉스 티비 폴더 하에 program_list의 제목과 동일한 폴더 생성 후 파일 정리
    # 다운로드 폴더에 있는 폴더 중에 program_list의 제목과 동일한 폴더는 '하위 폴더' 포함하여 삭제 (보통 파일 옮기고 난 후 남는 껍데기 폴더 및 광고 HTML 삭제를 위하여 사용함)
    # 트랜스미션 incomplete-dir-enabled 옵션으로 temp폴더를 사용해야지 사용 가능함 (다운로드 중에 옮길 수도 있기 때문임)
    FileMover(local_machine_status_file)

    sys.exit()


if __name__ == '__main__':
    main()
