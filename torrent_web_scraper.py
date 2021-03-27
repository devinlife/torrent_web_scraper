#!/usr/bin/env python3
import os
import sys
import time
from scraper.scraper_torrent import ScraperTorrent
pages_to_scrap = int(sys.argv[1]) if len(sys.argv) >= 2 else 3


def main():
    root_path = os.path.abspath(os.path.dirname(__file__)) + '/'
    local_machine_status_file = root_path + \
        'local_config/local_machine_configuration.json'
    local_machine_history_file = root_path + 'local_config/magnet_history.csv'
    local_machine_badsites_file = root_path + 'local_config/badsites.csv'
    scraper = ScraperTorrent(local_machine_status_file, local_machine_badsites_file,
                             local_machine_history_file, pages_to_scrap)

    print("\n{}".format(time.ctime()))
    goodsites = scraper.collect_goodsites()

    for i, goodsite in enumerate(goodsites):
        print("Scraper for {}".format(goodsite))
        categories = scraper.aggregation_categories(goodsite)
        if categories is not None:
            scraper.execute_scraper(categories)
        if i == 1:
            break

    scraper.end()
    sys.exit()


if __name__ == '__main__':
    main()
