from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time

# ====== 瀏覽器設定（可加上無頭模式） ======
options = Options()
# options.add_argument("--headless")  # ← 若不想開啟瀏覽器視窗可取消註解這行
options.add_argument("--start-maximized")

# 使用自動安裝的 ChromeDriver（正確用法）
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# ====== 要爬的頁面（兩頁） ======
urls = [
    "https://csie.asia.edu.tw/zh_tw/associate_professors_2?page_no=1&",
    "https://csie.asia.edu.tw/zh_tw/associate_professors_2?page_no=2&"
]

# ====== 清理文字用的函式 ======
def clean(text):
    return text.strip().replace('\xa0', ' ').replace('\n', '').replace('\r', '')

# ====== 建立 SQLite 資料庫 ======
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

# ====== 開始爬資料 ======
all_professors = []

try:
    for url in urls:
        driver.get(url)
        time.sleep(1.5)  # 等待網頁載入（可視網速調整）

        sections = driver.find_elements(By.CLASS_NAME, 'i-member-section')
        print(f"\n這頁共找到 {len(sections)} 個職稱區塊。")

        for section in sections:
            professor_items = section.find_elements(By.CLASS_NAME, 'i-member-item')
            print(f"該區塊有 {len(professor_items)} 位老師")

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

                name = clean(name)
                research = clean(research)
                title = clean(title)

                if name:
                    all_professors.append({'title': title, 'name': name, 'research': research})
                    cursor.execute('''
                        INSERT INTO professors (title, name, research)
                        VALUES (?, ?, ?)
                    ''', (title, name, research))

        conn.commit()

    # ====== 輸出成 .txt 檔案 ======
    with open("professors_selenium.txt", "w", encoding="utf-8") as f:
        for prof in all_professors:
            f.write(f"職稱: {prof['title']}, 姓名: {prof['name']}, 研究領域: {prof['research']}\n")

    print(f"\n✅ 共擷取 {len(all_professors)} 位老師資料，已成功寫入 professors_selenium.txt 與 SQLite 資料庫。")

except Exception as e:
    print("❌ 發生錯誤：", e)

finally:
    conn.close()
    driver.quit()
