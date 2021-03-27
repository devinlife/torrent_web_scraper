# Torrent_web_scraper: 토렌트 자동 다운로드 프로젝트

torrent_web_scraper는 토렌트 파일을 자동으로 다운로드 해주는 웹크롤러 파이썬
스크립트입니다. TV 프로그램을 다운로드 받기 위해 매번 토렌트 사이트를 접속하며
토렌트 시드 파일 다운로드 받기가 귀찮아서 시작한 토이프로젝트입니다.

torrent_web_scraper를 설정해두면, 토렌트 다운로드를 위해 토렌트 사이트를
방문할 필요가 없어지며, 자동으로 TV 프로그램을 다운로드 해줘서 편리하다.

자세한 소개와 설치 방법은 아래 페이지를 참고하자.  
[Torrent_web_scraper: 토렌트 자동 다운로드 프로젝트 소개/설치](https://devinlife.com/project%20torrnet_web_scraper/torrent-web-scraper/)


# 다른점

1. local_config/local_machine_configuration.json 에서 트랜스미션 항목 작성, 필요 파이썬 라이브러리 설치. // 이상하게 저는 쉘스크립트가 잘 안되네요;
 
2. local_config/local_machine_configuration.json 에서 media-folder 항목에 '폴더'를 지정
    
    지정된 폴더 아래에 예) '순풍산부인과' 폴더를 작성하면 자동으로 검색해서 해당 폴더에 다운로드. // 저작권을 염두해두시고 다운로드 하세요!
    
    폴더 삭제 시에는 더이상 다운로드를 하지 않음
    
    $python3 torrent_web_scraper.py
    
    $python3 torrent_web_scraper.py 1       // cron 사용시에는 뒤에 띄어쓴 후 1을 추가해주면 1 페이지 씩만 검색합니다. 기본은 3 페이지.

3. 구글링해서 토렌트 사이트를 찾아줍니다. 

4. 폴더가 씌워진 파일은 원래 위치로 옮겨준 후 껍데기 폴더를 삭제함 (HTML 광고 파일 폴더 제거용)

5. 다운로드 상태가 100.0% 토렌트 리스트에서 제거합니다. // 원작자 분이 주석 처리해놓은 것 풀었습니다. isFinished > percentDone으로 조건 변경


