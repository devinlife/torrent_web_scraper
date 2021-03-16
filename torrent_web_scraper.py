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

    sys.exit()


if __name__ == '__main__':
    main()
