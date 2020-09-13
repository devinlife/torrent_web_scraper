#!/usr/bin/env python3
import sys
from scraper.scraper_torrentmax import ScraperTorrentmax
from scraper.scraper_torrentsir import ScraperTorrentsir

def main():

    local_machine_status_file = 'local_config/local_machine_configuration.json'
    scraper_configuration_file = 'scraper/scraper_configuration.json'

    # Torrentmax
    scraper = ScraperTorrentmax(scraper_configuration_file, local_machine_status_file)
    scraper.aggregation_categories()

    if scraper.check_site_alive():
        scraper.execute_scraper()

    # Torrentsir
    scraper = ScraperTorrentsir(scraper_configuration_file, local_machine_status_file)
    scraper.aggregation_categories()

    if scraper.check_site_alive():
        scraper.execute_scraper()

    sys.exit()

if __name__ == '__main__':
    main()
