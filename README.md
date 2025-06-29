# Crawler-Selenium
使用 Selenium 擷取亞洲大學資工系教師資料
本專案是一個使用 Python 與 Selenium 製作的網頁爬蟲，用於擷取亞洲大學資訊工程學系教師的姓名、職稱與研究領域。資料自學校官方網站自動抓取並儲存至 .txt 檔與 SQLite 資料庫中，可用於學術統整、自動化分析或其他研究用途。

# 使用技術
程式語言：Python 3

網頁爬蟲工具：

Selenium — 操控瀏覽器模擬點擊、抓取動態網頁內容

webdriver-manager — 自動安裝與管理 ChromeDriver

資料處理：

SQLite3 — 將資料儲存成本地資料庫（方便查詢、讀取）

純文字 .txt 檔案 — 方便檢查與人工閱讀

# 程式如何運作

## 1.匯入所需模組
```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time
```

selenium: 用來模擬瀏覽器操作

webdriver_manager: 自動下載並管理對應版本的 ChromeDriver

sqlite3: 用來將資料寫進 SQLite 資料庫

time: 控制程式等待，避免網頁還沒載入完就抓資料

## 2.瀏覽器設定與啟動
程式會依序打開兩個網址（第 1 頁與第 2 頁），爬取所有老師資料。
```python
options = Options()
# options.add_argument("--headless")  # 無頭模式（不顯示瀏覽器）
options.add_argument("--start-maximized")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
```
設定 Selenium 使用的 Chrome 瀏覽器，並透過 webdriver_manager 自動下載並啟動對應的 ChromeDriver。

## 3.頁面網址設定
```python
urls = [
    "https://csie.asia.edu.tw/zh_tw/associate_professors_2?page_no=1&",
    "https://csie.asia.edu.tw/zh_tw/associate_professors_2?page_no=2&"
]
```

## 4.清洗字串的工具函式
```python
def clean(text):
    return text.strip().replace('\xa0', ' ').replace('\n', '').replace('\r', '')
```
移除多餘空白與換行符號，讓擷取下來的文字更乾淨。

## 5.建立 SQLite 資料庫
```python
conn = sqlite3.connect('professors_selenium.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS professors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        name TEXT,
        research TEXT
    )
''')
conn.commit()
```
建立一個本地資料庫 professors_selenium.db，若表格不存在則創建一個用來儲存教師資訊的表格。

## 6.進入主要爬蟲邏輯
```python
for url in urls:
    driver.get(url)
    time.sleep(1.5)
```
用 Selenium 開啟每一頁網址並等待載入，接著開始擷取內容。

## 7.擷取每一個教師區塊的資料

```python
sections = driver.find_elements(By.CLASS_NAME, 'i-member-section')
```

這行會找到整個頁面上的區塊，每個職稱分類（如：副教授、助理教授）都是一個 section。

## 8.擷取單一教師的三項資料
```python
for item in professor_items:
    try:
        name = item.find_element(By.CLASS_NAME, 'member-data-value-name').text
    except:
        try:
            name = item.find_element(By.TAG_NAME, 'h3').text
        except:
            name = ""

    try:
        research = item.find_element(By.CLASS_NAME, 'member-data-value-7').text
    except:
        try:
            research = item.find_element(By.TAG_NAME, 'p').text
        except:
            research = "尚未提供"

    try:
        title = item.find_element(By.CLASS_NAME, 'member-data-value-1').text
    except:
        title = "未知職稱"
```

這段是整個爬蟲的核心，透過多種判斷方式保證能抓到「姓名」、「研究領域」、「職稱」，即使網頁結構不一致也能處理。

## 9.將結果儲存到記憶體與資料庫
```python
all_professors.append({'title': title, 'name': name, 'research': research})
cursor.execute('''
    INSERT INTO professors (title, name, research)
    VALUES (?, ?, ?)
''', (title, name, research))
```

每筆資料會同時存入列表（方便寫入文字檔）與 SQLite 資料庫。

## 10.存檔與結尾處理
```python
with open("professors_selenium.txt", "w", encoding="utf-8") as f:
    for prof in all_professors:
        f.write(f"職稱: {prof['title']}, 姓名: {prof['name']}, 研究領域: {prof['research']}\n")
```
最後將所有擷取到的資料輸出成文字檔 professors_selenium.txt

## END 關閉瀏覽器與資料庫連線
```python
driver.quit()
conn.close()
```

結束後關閉資料庫與瀏覽器。

# 開發過程遇到的困難與解法
## 1.找不到對應的 ChromeDriver
解決方法： 使用 webdriver_manager 自動安裝正確版本的 ChromeDriver。

```python
from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
```

## 2.教師資料的 HTML 結構不一致
解決方法： 使用 try-except 多層結構判斷，先嘗試常見的格式，再使用替代方案：

```python
try:
    name = prof.find_element(By.CLASS_NAME, 'member-data-value-name').text.strip()
except:
    name = prof.find_element(By.TAG_NAME, 'h3').text.strip()

try:
    research = prof.find_element(By.CLASS_NAME, 'member-data-value-7').text.strip()
except:
    try:
        research = prof.find_element(By.TAG_NAME, 'p').text.strip()
    except:
        research = "尚未提供"
```

## 3.資料分類錯誤（例如：第一頁的40 位老師都被歸為系主任）
解決方法：

檢查 Selenium 抓到的 section 是根據網站載入後的實際內容，而不是頁面標題。

改從每個 section 抓取內部的職稱標籤 .i-member-status-title，並搭配每位老師的區塊 .i-member-item 判斷來源。
