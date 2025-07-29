from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

def scrape_ibkr_products():
    url = "https://www.interactivebrokers.com/en/trading/products-exchanges.php#/#"
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)

    data = []
    columns = ["SYMBOL", "DESCRIPTION", "IBKR SYMBOL", "CURRENCY", "REGION", "EXCHANGE"]

    page_num = 1
    while True:
        print(f"Scraping page {page_num} ...")
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                data.append([col.text for col in cols])
        # Next 버튼(→ a.btn-forward) 찾기
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a.btn-forward")
            # 만약 next_btn에 disabled가 있으면 마지막 페이지
            if 'disabled' in next_btn.get_attribute('class') or not next_btn.is_enabled():
                print("마지막 페이지(Next 비활성화)")
                break
            next_btn.click()
            page_num += 1
            time.sleep(2)
        except Exception as e:
            print("Next 버튼을 찾을 수 없거나, 마지막 페이지로 판단 (정상 종료)")
            break

    driver.quit()
    df = pd.DataFrame(data, columns=columns)
    df.to_excel("ibkr_products.xlsx", index=False)
    print("스크랩 및 저장 완료: ibkr_products.xlsx")


def main():
    scrape_ibkr_products()


if __name__ == "__main__":
    main()
