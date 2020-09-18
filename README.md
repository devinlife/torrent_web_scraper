# torrent_web_scraper

## 1. git clone

git clone https://github.com/devinlife/torrent_web_scraper.git

## 2. 초기 설정

$ cd torrent_web_scraper
$ setup_script.sh

setup_script.sh 스크립트 파일을 실행하면 초기 설정을 자동으로 수행하도록
작성하였습니다. 파이썬을 사용하기 위해서 python3.7, virtualenv, pip를
사용합니다.

## 3. 개인 컴퓨터 환경 설정

local_config/local_machine_configuration.json 파일을 열어서 transmission 관련한
ip, port, id, pw를 기재합니다.

local_config/program_list.py 파일을 열어서 다운로드할 프로그램의 제목을
기재합니다. 샘플로 제공한 리스트에서 원치않는 프로그램은 삭제하세요.

## 4. 크롤링 실행

$ execute_scrapers.sh

execute_scrapers.sh 파일을 실행하면 크롤링 파이썬 스크립트를 호출하여
크롤링을 수행합니다.
