from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QColor
import sys
import requests
from bs4 import BeautifulSoup

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setupTimer()
        self.watchlist = []  # 관심 종목 리스트 초기화

    def setupUi(self):
        from PyQt5 import uic
        uic.loadUi('tablewidgetTest.ui', self)
        
        self.tableWidget.setRowCount(0)  # 기존 행 제거
        self.dateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        # 버튼 클릭 시 기능 연결
        self.pushButton_2.clicked.connect(self.addToWatchlist)
        self.pushButton_3.clicked.connect(self.removeFromWatchlist)
        self.btn_removeItem.clicked.connect(self.viewWatchlist)
        self.btn_insertItem.clicked.connect(self.searchStock)  # 검색 버튼 클릭 시 기능 연결
        self.pushButton.clicked.connect(self.refreshDomesticMarket)  # 국내증시 버튼 클릭 시 기능 연결

    def setupTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateStockInformation)
        self.timer.timeout.connect(self.updateDateTime)
        self.timer.start(30000)  # 1초마다 타이머 트리거
        self.updateStockInformation()
        self.updateDateTime()

    def fetchStockData(self):
    # URL과 헤더 설정
        base_url = 'https://finance.naver.com/sise/sise_market_sum.naver'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

        all_stocks = []

    # 첫 번째 페이지 데이터 가져오기
        for page in range(1, 5):  # 페이지 1과 2를 가져오기 위해 range(1, 3)
            url = f'{base_url}?&page={page}'
        
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.RequestException as e:
                QMessageBox.critical(self, "오류", f"주식 데이터를 가져오는 중 오류가 발생했습니다: {e}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'type_2'})
        
            if table:
                rows = table.find_all('tr')[2:]  # 헤더를 제외한 데이터 행들
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        stock_info = {
                            'name': cols[1].get_text(strip=True),
                            'symbol': cols[2].get_text(strip=True),
                            'price': cols[3].get_text(strip=True),
                            'change': cols[4].get_text(strip=True),
                            'change_percent': cols[5].get_text(strip=True)
                    }
                        all_stocks.append(stock_info)
    
        return all_stocks

    
    from PyQt5.QtGui import QColor  # QColor을 import 해야 함

    def updateStockInformation(self):
        stock_data = self.fetchStockData()
        if not stock_data:
            QMessageBox.warning(self, "정보", "현재 주식 데이터가 없습니다.")
            return

        self.tableWidget.setRowCount(0)
        for stock in stock_data:
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)

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
            if change.startswith('+'):  # 상승
                color = QColor('red')
            elif change.startswith('-'):  # 하락
                color = QColor('blue')
            else:
                color = QColor('black')  # 변동 없는 경우 기본 색상

            for column in range(self.tableWidget.columnCount()):
                self.tableWidget.item(row_position, column).setForeground(color)


    def updateDateTime(self):
        current_time = QDateTime.currentDateTime()
        self.dateTimeEdit.setDateTime(current_time)

    def addToWatchlist(self):
        stock_name = self.line_insertItem.text().strip()
        stock_data = self.fetchStockData()

        # 관심 종목 목록에 추가할 주식 정보 찾기
        stock_info = next((item for item in stock_data if item['name'] == stock_name), None)

        if stock_name and stock_info:
            if not any(stock['name'] == stock_name for stock in self.watchlist):
                self.watchlist.append(stock_info)
                QMessageBox.information(self, "정보", f"{stock_name}이(가) 관심 종목 목록에 추가되었습니다.")
            else:
                QMessageBox.warning(self, "경고", f"{stock_name}은 이미 관심 종목 목록에 있습니다.")
        elif not stock_name:
            QMessageBox.warning(self, "경고", "관심 종목 이름을 입력해 주세요.")
        else:
            QMessageBox.warning(self, "경고", f"{stock_name}의 정보를 찾을 수 없습니다.")

    def removeFromWatchlist(self):
        stock_name = self.line_insertItem.text().strip()
        if stock_name:
            self.watchlist = [stock for stock in self.watchlist if stock['name'] != stock_name]
            QMessageBox.information(self, "정보", f"{stock_name}이(가) 관심 종목 목록에서 제거되었습니다.")
        else:
            QMessageBox.warning(self, "경고", "관심 종목 이름을 입력해 주세요.")

    def viewWatchlist(self):
        if not self.watchlist:
            QMessageBox.information(self, "정보", "관심 종목 목록이 비어 있습니다.")
            return
        
        self.tableWidget.setRowCount(0)
        for stock in self.watchlist:
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)
            self.tableWidget.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            if change.startswith('+'):  # 상승
                color = QColor('red')
            elif change.startswith('-'):  # 하락
                color = QColor('blue')
            else:
                color = QColor('black')  # 변동 없는 경우 기본 색상

            for column in range(self.tableWidget.columnCount()):
                self.tableWidget.item(row_position, column).setForeground(color)

    def searchStock(self):
        search_query = self.line_insertItem.text().strip()
        if not search_query:
            QMessageBox.warning(self, "경고", "검색어를 입력해 주세요.")
            return
        
        stock_data = self.fetchStockData()
        if not stock_data:
            QMessageBox.warning(self, "정보", "현재 주식 데이터가 없습니다.")
            return

        filtered_stocks = [stock for stock in stock_data if search_query.lower() in stock['name'].lower()]

        self.tableWidget.setRowCount(0)
        for stock in filtered_stocks:
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)
            self.tableWidget.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            if change.startswith('+'):  # 상승
                color = QColor('red')
            elif change.startswith('-'):  # 하락
                color = QColor('blue')
            else:
                color = QColor('black')  # 변동 없는 경우 기본 색상

            for column in range(self.tableWidget.columnCount()):
                self.tableWidget.item(row_position, column).setForeground(color)


    def refreshDomesticMarket(self):
        self.updateStockInformation()

app = QApplication(sys.argv)
dialog = MyDialog()
dialog.show()
sys.exit(app.exec_())




