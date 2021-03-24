#!/usr/bin/env python3
import os
import sys
import time
from scraper.scraper_torrent import ScraperTorrent


def main():

    root_path = os.path.abspath(os.path.dirname(__file__)) + '/'
    local_machine_status_file = root_path + \
        'local_config/local_machine_configuration.json'
    local_machine_history_file = root_path + 'local_config/magnet_history.csv'
    local_machine_badsites_file = root_path + 'local_config/badsites.csv'

    print("\n{}".format(time.ctime()))

    scraper = ScraperTorrent(local_machine_status_file,
                             local_machine_badsites_file, local_machine_history_file)
    goodsites = scraper.collect_goodsites()
    scraper.filemove.arrange_files()

    times = 0
    for goodsite in goodsites:
        print("Scraper for {}".format(goodsite))
        categories = scraper.aggregation_categories(goodsite)

        if categories is not None:
            scraper.execute_scraper(categories)

        if times == 1:
            break
        times += 1

    scraper.filemove.delete_folders()
    sys.exit()


if __name__ == '__main__':
    main()
