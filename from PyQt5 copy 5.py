from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QMessageBox, QCheckBox
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QColor, QFontDatabase, QFont
from PyQt5 import QtWidgets, uic
import sys
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QHBoxLayout, QWidget

CheckBoxBoolean = [False] * 200


class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setupTimer()
        self.watchlist = []  # 관심 종목 리스트 초기화

    def setupUi(self):
        uic.loadUi('tablewidgetTest.ui', self)
        
        self.tableWidget.setRowCount(0)  # 기존 행 제거
        self.dateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        # 버튼 클릭 시 기능 연결
        self.pushButton_2.clicked.connect(self.addToWatchlist)
        self.pushButton_3.clicked.connect(self.removeFromWatchlist)
        self.btn_removeItem.clicked.connect(self.viewWatchlist)
        self.btn_insertItem.clicked.connect(self.searchStock)  # 검색 버튼 클릭 시 기능 연결
        self.pushButton.clicked.connect(self.refreshDomesticMarket)  # 국내증시 버튼 클릭 시 기능 연결
        self.tableWidget.cellClicked.connect(self.checkBoxStateChanged)  # 체크박스 클릭 시 기능 연결
        self.tableWidget.setColumnWidth(5,20) #첫번째 열 크기 고정
        self.tableWidget.setColumnWidth(0,200) #첫번째 열 크기 고정

    def setupTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateStockInformation)
        self.timer.timeout.connect(self.updateDateTime)
        self.timer.start(5000)  # 30초마다 타이머 트리거
        self.updateStockInformation()
        self.updateDateTime()

    def fetchStockData(self):
        base_url = 'https://finance.naver.com/sise/sise_market_sum.naver'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        all_stocks = []

        for page in range(1, 5):  # 페이지 1~4을 가져오기
            url = f'{base_url}?&page={page}'
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
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
            except requests.RequestException as e:
                QMessageBox.critical(self, "오류", f"주식 데이터를 가져오는 중 오류가 발생했습니다: {e}")
                return []
        return all_stocks

    def updateStockInformation(self):
        stock_data = self.fetchStockData()
        if not stock_data:
            QMessageBox.warning(self, "정보", "현재 주식 데이터가 없습니다.")
            return

        self.tableWidget.setRowCount(0)
        for stock in stock_data:
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)
            self.tableWidget.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            color = QColor('red') if change.startswith('+') else QColor('blue') if change.startswith('-') else QColor('black')

            for column in range(self.tableWidget.columnCount() - 1):  # 마지막 열을 제외한 모든 열에 색상 적용
                item = self.tableWidget.item(row_position, column)
                if item is None:
                    item = QTableWidgetItem()  # 빈 아이템 생성
                    self.tableWidget.setItem(row_position, column, item)
                item.setForeground(color)

        self.addCheckBoxesToTable()  # 체크박스 추가
    
    def updateDateTime(self):
        current_time = QDateTime.currentDateTime()
        self.dateTimeEdit.setDateTime(current_time)

    def addCheckBoxesToTable(self):
        for row in range(self.tableWidget.rowCount()):
            checkbox = QCheckBox()
            if CheckBoxBoolean[row]:
                checkbox.setChecked(True)  # 체크박스를 기본적으로 체크된 상태로 설정
            checkbox.stateChanged.connect(self.checkBoxStateChanged)  # 체크박스 상태 변경 시 기능 연결

            # 레이아웃을 사용하여 체크박스를 중앙에 배치
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)  # 중앙 정렬
            layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
            widget.setLayout(layout)

            self.tableWidget.setCellWidget(row, 5, widget)  # 체크박스는 6번째 열에 추가

    def checkBoxStateChanged(self, state):
        sender_checkbox = self.sender()  # 신호를 보낸 체크박스를 확인
        for row in range(self.tableWidget.rowCount()):
            widget = self.tableWidget.cellWidget(row, 5)
            if widget is not None:
                checkbox = widget.findChild(QCheckBox)
                if checkbox == sender_checkbox:
                    stock_name = self.tableWidget.item(row, 0).text()
                    if state == Qt.Checked:
                        CheckBoxBoolean[row] = True
                        print(f"{row} : {CheckBoxBoolean[row]}")
                        self.addToWatchlist(stock_name)
                    else:
                        CheckBoxBoolean[row] = False
                        print(f"{row} : {CheckBoxBoolean[row]}")
                        self.removeFromWatchlist(stock_name)
                    break


    def addToWatchlist(self, stock_name=None):
        if stock_name is None:
            stock_name = self.line_insertItem.text().strip()
        stock_data = self.fetchStockData()
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

    def removeFromWatchlist(self, stock_name=None):
        if stock_name is None:
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

        self.tableWidget_2.setRowCount(0)
        for stock in self.watchlist:
            row_position = self.tableWidget_2.rowCount()
            self.tableWidget_2.insertRow(row_position)
            self.tableWidget_2.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget_2.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget_2.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget_2.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget_2.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            color = QColor('red') if change.startswith('+') else QColor('blue') if change.startswith('-') else QColor('black')

            for column in range(self.tableWidget_2.columnCount()):
                item = self.tableWidget_2.item(row_position, column)
                if item is None:
                    item = QTableWidgetItem()  # 빈 아이템 생성
                    self.tableWidget_2.setItem(row_position, column, item)
                item.setForeground(color)

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

        self.tableWidget_2.setRowCount(0)
        for stock in filtered_stocks:
            row_position = self.tableWidget_2.rowCount()
            self.tableWidget_2.insertRow(row_position)
            self.tableWidget_2.setItem(row_position, 0, QTableWidgetItem(stock['name']))
            self.tableWidget_2.setItem(row_position, 1, QTableWidgetItem(stock['symbol']))
            self.tableWidget_2.setItem(row_position, 2, QTableWidgetItem(stock['price']))
            self.tableWidget_2.setItem(row_position, 3, QTableWidgetItem(stock['change']))
            self.tableWidget_2.setItem(row_position, 4, QTableWidgetItem(stock['change_percent']))

            change = stock['change'].replace(',', '')  # 문자열에서 쉼표 제거
            color = QColor('red') if change.startswith('+') else QColor('blue') if change.startswith('-') else QColor('black')

            for column in range(self.tableWidget_2.columnCount()):
                item = self.tableWidget_2.item(row_position, column)
                if item is None:
                    item = QTableWidgetItem()  # 빈 아이템 생성
                    self.tableWidget_2.setItem(row_position, column, item)
                item.setForeground(color)

    def refreshDomesticMarket(self):
        self.updateStockInformation()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())





