from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QColor
import sys
import requests
from bs4 import BeautifulSoup

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi()  # UI 설정 초기화
        self.setupTimer()  # 타이머 설정 초기화
        self.watchlist = []  # 관심 종목 리스트 초기화

    def setupUi(self):
        from PyQt5 import uic
        uic.loadUi('tablewidgetTest.ui', self)  # UI 파일 로드
        
        self.tableWidget.setRowCount(0)  # 기존 테이블 행 제거
        self.dateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")  # 날짜 및 시간 형식 설정

        # 버튼 클릭 시 연결될 기능 설정
        self.pushButton_2.clicked.connect(self.addToWatchlist)  # '관심 종목 추가' 버튼 클릭 시, 관심 종목에 추가하는 기능 연결
        self.pushButton_3.clicked.connect(self.removeFromWatchlist)  # '관심 종목 제거' 버튼 클릭 시, 관심 종목에서 제거하는 기능 연결
        self.btn_removeItem.clicked.connect(self.viewWatchlist)  # '관심 종목 보기' 버튼 클릭 시, 관심 종목 리스트 보기 기능 연결
        self.btn_insertItem.clicked.connect(self.searchStock)  # '검색' 버튼 클릭 시, 주식 검색 기능 연결
        self.pushButton.clicked.connect(self.refreshDomesticMarket)  # '국내증시 새로고침' 버튼 클릭 시, 국내 주식 시장 정보 갱신 기능 연결

    def setupTimer(self):
        self.timer = QTimer(self)  # 타이머 객체 생성
        self.timer.timeout.connect(self.updateStockInformation)  # 타이머가 만료될 때 주식 정보 업데이트
        self.timer.timeout.connect(self.updateDateTime)  # 타이머가 만료될 때 날짜 및 시간 업데이트
        self.timer.start(10000)  # 30초마다 타이머 트리거
        self.updateStockInformation()  # 초기 주식 정보 업데이트
        self.updateDateTime()  # 초기 날짜 및 시간 업데이트

    def fetchStockData(self):
        # 네이버 금융 URL과 헤더 설정
        base_url = 'https://finance.naver.com/sise/sise_market_sum.naver'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

        all_stocks = []  # 모든 주식 정보를 담을 리스트 초기화

        # 페이지 1부터 4까지 주식 데이터를 가져옴
        for page in range(1, 5):
            url = f'{base_url}?&page={page}'  # 각 페이지의 URL 생성
        
            try:
                response = requests.get(url, headers=headers)  # 웹 페이지 요청
                response.raise_for_status()  # 오류가 있을 경우 예외 발생
            except requests.RequestException as e:
                # 주식 데이터를 가져오는 중 오류가 발생할 경우 메시지 박스 표시
                QMessageBox.critical(self, "오류", f"주식 데이터를 가져오는 중 오류가 발생했습니다: {e}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')  # 페이지 HTML 파싱
            table = soup.find('table', {'class': 'type_2'})  # 주식 데이터가 포함된 테이블 찾기
        
            if table:
                rows = table.find_all('tr')[2:]  # 헤더를 제외한 데이터 행들 찾기
                for row in rows:
                    cols = row.find_all('td')  # 각 행의 열들 찾기
                    if len(cols) >= 6:  # 필요한 데이터가 있는지 확인
                        stock_info = {
                            'name': cols[1].get_text(strip=True),  # 주식 이름
                            'symbol': cols[2].get_text(strip=True),  # 주식 심볼
                            'price': cols[3].get_text(strip=True),  # 주식 가격
                            'change': cols[4].get_text(strip=True),  # 가격 변동
                            'change_percent': cols[5].get_text(strip=True)  # 변동 퍼센트
                        }
                        all_stocks.append(stock_info)  # 주식 정보를 리스트에 추가
    
        return all_stocks  # 모든 주식 데이터 반환

    def updateStockInformation(self):
        stock_data = self.fetchStockData()  # 주식 데이터 가져오기
        if not stock_data:
            QMessageBox.warning(self, "정보", "현재 주식 데이터가 없습니다.")  # 데이터가 없을 경우 경고 메시지 표시
            return

        self.tableWidget.setRowCount(0)  # 테이블의 기존 행 초기화
        for stock in stock_data:
            row_position = self.tableWidget.rowCount()  # 현재 테이블의 행 수 가져오기
            self.tableWidget.insertRow(row_position)  # 새로운 행 추가

            # 주식 정보를 테이블에 추가
            name_item = QTableWidgetItem(stock['name'])
            symbol_item = QTableWidgetItem(stock['symbol'])
            price_item = QTableWidgetItem(stock['price'])
            change_item = QTableWidgetItem(stock['change'])
            change_percent_item = QTableWidgetItem(stock['change_percent'])

            self.tableWidget.setItem(row_position, 0, name_item)
            self.tableWidget.setItem(row_position, 1, symbol_item)
            self.tableWidget.setItem(row_position, 2, price_item)
            self.tableWidget.setItem(row_position, 3, change_item)
            self.tableWidget.setItem(row_position, 4, change_percent_item)

            # 상승과 하락에 따라 텍스트 색깔 설정
            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            if change.startswith('+'):  # 가격 상승
                color = QColor('red')
            elif change.startswith('-'):  # 가격 하락
                color = QColor('blue')
            else:
                color = QColor('black')  # 변동 없는 경우 기본 색상

            for column in range(self.tableWidget.columnCount()):
                self.tableWidget.item(row_position, column).setForeground(color)  # 각 셀에 색상 적용

    def updateDateTime(self):
        current_time = QDateTime.currentDateTime()  # 현재 시간 가져오기
        self.dateTimeEdit.setDateTime(current_time)  # UI에 시간 업데이트

    def addToWatchlist(self):
        stock_name = self.line_insertItem.text().strip()  # 사용자가 입력한 주식 이름 가져오기
        stock_data = self.fetchStockData()  # 현재 주식 데이터 가져오기

        # 관심 종목 목록에 추가할 주식 정보 찾기
        stock_info = next((item for item in stock_data if item['name'] == stock_name), None)

        if stock_name and stock_info:
            if not any(stock['name'] == stock_name for stock in self.watchlist):
                self.watchlist.append(stock_info)  # 관심 종목 리스트에 추가
                QMessageBox.information(self, "정보", f"{stock_name}이(가) 관심 종목 목록에 추가되었습니다.")
            else:
                QMessageBox.warning(self, "경고", f"{stock_name}은 이미 관심 종목 목록에 있습니다.")
        elif not stock_name:
            QMessageBox.warning(self, "경고", "관심 종목 이름을 입력해 주세요.")
        else:
            QMessageBox.warning(self, "경고", f"{stock_name}의 정보를 찾을 수 없습니다.")

    def removeFromWatchlist(self):
        stock_name = self.line_insertItem.text().strip()  # 사용자가 입력한 주식 이름 가져오기
        if stock_name:
            # 관심 종목 리스트에서 해당 주식 제거
            self.watchlist = [stock for stock in self.watchlist if stock['name'] != stock_name]
            QMessageBox.information(self, "정보", f"{stock_name}이(가) 관심 종목 목록에서 제거되었습니다.")
        else:
            QMessageBox.warning(self, "경고", "관심 종목 이름을 입력해 주세요.")

    def viewWatchlist(self):
        if not self.watchlist:
            QMessageBox.information(self, "정보", "관심 종목 목록이 비어 있습니다.")  # 관심 종목 목록이 비어 있을 경우 경고 메시지 표시
            return
        
        self.tableWidget.setRowCount(0)  # 테이블의 기존 행 초기화
        for stock in self.watchlist:
            row_position = self.tableWidget.rowCount()  # 현재 테이블의 행 수 가져오기
            self.tableWidget.insertRow(row_position)  # 새로운 행 추가
            self.tableWidget.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            # 상승과 하락에 따라 텍스트 색깔 설정
            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            if change.startswith('+'):  # 가격 상승
                color = QColor('red')
            elif change.startswith('-'):  # 가격 하락
                color = QColor('blue')
            else:
                color = QColor('black')  # 변동 없는 경우 기본 색상

            for column in range(self.tableWidget.columnCount()):
                self.tableWidget.item(row_position, column).setForeground(color)  # 각 셀에 색상 적용

    def searchStock(self):
        search_query = self.line_insertItem.text().strip()  # 사용자가 입력한 검색어 가져오기
        if not search_query:
            QMessageBox.warning(self, "경고", "검색어를 입력해 주세요.")  # 검색어가 없을 경우 경고 메시지 표시
            return
        
        stock_data = self.fetchStockData()  # 현재 주식 데이터 가져오기
        if not stock_data:
            QMessageBox.warning(self, "정보", "현재 주식 데이터가 없습니다.")  # 주식 데이터가 없을 경우 경고 메시지 표시
            return

        # 검색어로 주식 필터링
        filtered_stocks = [stock for stock in stock_data if search_query.lower() in stock['name'].lower()]

        self.tableWidget.setRowCount(0)  # 테이블의 기존 행 초기화
        for stock in filtered_stocks:
            row_position = self.tableWidget.rowCount()  # 현재 테이블의 행 수 가져오기
            self.tableWidget.insertRow(row_position)  # 새로운 행 추가
            self.tableWidget.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            # 상승과 하락에 따라 텍스트 색깔 설정
            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            if change.startswith('+'):  # 가격 상승
                color = QColor('red')
            elif change.startswith('-'):  # 가격 하락
                color = QColor('blue')
            else:
                color = QColor('black')  # 변동 없는 경우 기본 색상

            for column in range(self.tableWidget.columnCount()):
                self.tableWidget.item(row_position, column).setForeground(color)  # 각 셀에 색상 적용

    def refreshDomesticMarket(self):
        self.updateStockInformation()  # 국내증시 새로고침 시 주식 정보 업데이트

# 애플리케이션 실행
app = QApplication(sys.argv)
dialog = MyDialog()
dialog.show()
sys.exit(app.exec_())




