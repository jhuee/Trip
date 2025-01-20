from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import openpyxl
import os


# 인스타그램 로그인 정보
username_input = "your_id"
password_input = "your_pw"

# 웹드라이버 설정
driver = webdriver.Chrome()
driver.get("https://www.instagram.com/accounts/login/")

time.sleep(5)

# 로그인 절차
username_field = driver.find_element(By.NAME, "username")
password_field = driver.find_element(By.NAME, "password")
username_field.send_keys(username_input)
password_field.send_keys(password_input)
password_field.send_keys(Keys.RETURN)

excel_filename = "instagram_story_viewers.xlsx"

# 나중에 하기 버튼 그냥 자기가 알아서 눌러도 됨
wait = WebDriverWait(driver, 10)
later_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "나중에 하기")]')))
later_button.click()

def open_story():
    # 조회 목록 열기
    driver.get("https://www.instagram.com/stories/your_id/")

    time.sleep(1)  # 스토리 로딩 대기

def open_viewers():
    view_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "명이 읽음")]')))
    view_button.click()
    print("스토리 조회자 목록 열기")
    time.sleep(2)

def load_existing_data():
    if os.path.exists(excel_filename):
        df = pd.read_excel(excel_filename, sheet_name="Current")
        # NaN 값 제거
        existing_usernames = df["Username"].dropna().tolist()
        return set(existing_usernames) 
    return set()

def save_data(new_usernames, removed_usernames):
    new_usernames = {username for username in new_usernames if username and str(username) != 'nan'}
    removed_usernames = {username for username in removed_usernames if username and str(username) != 'nan'}

    df_new = pd.DataFrame(new_usernames, columns=["Username"])

    # 누적 저장장
    if os.path.exists(excel_filename):
        with pd.ExcelFile(excel_filename, engine="openpyxl") as reader:
            if "Removed" in reader.sheet_names:
                df_existing_removed = pd.read_excel(reader, sheet_name="Removed")
                # 기존 데이터와 새로운 데이터를 병합 후 중복 제거
                df_removed = pd.concat(
                    [df_existing_removed, pd.DataFrame(removed_usernames, columns=["Username"])]
                ).drop_duplicates().reset_index(drop=True)
            else:
                df_removed = pd.DataFrame(removed_usernames, columns=["Username"])
    else:
        df_removed = pd.DataFrame(removed_usernames, columns=["Username"])

    # current 시트는 덮어쓰기가 되고 removed sheet는 누적됨됨
    with pd.ExcelWriter(excel_filename, mode="w", engine="openpyxl") as writer:
        df_new.to_excel(writer, sheet_name="Current", index=False)
        df_removed.to_excel(writer, sheet_name="Removed", index=False)

    print("성공적으로 저장")

def close_story():
    """ 스토리 닫기 버튼 클릭 """
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="닫기"]'))
        )
        close_button.click()
        print("스토리를 성공적으로 닫았습니다.")
    except Exception as e:
        print(f"스토리 닫기 실패: {e}")

def check_viewers():
    account_data = set()  # 새롭게 가져온 계정 데이터를 저장할 세트
    try:
        accounts = driver.find_elements(By.CSS_SELECTOR, 'a._a6hd')
        for account in accounts:
            username = account.text.strip()  
            if username:  # 빈 문자열이 아닌 경우에만 추가
                account_data.add(username)

        existing_accounts = load_existing_data()
        new_accounts = account_data - existing_accounts  # 새로 추가된 계정
        removed_accounts = existing_accounts - account_data  # 사라진 계정

        # 변경 사항이 있는 경우만 저장
        if new_accounts or removed_accounts:
            print(f"새로운 계정 발견: {new_accounts}")
            print(f"사라진 계정 발견: {removed_accounts}")
            save_data(account_data, removed_accounts)

    except Exception as e:
        print(f"오류 발생: {e}")

# 스토리 열기 및 주기적 확인
try:
    while True:
        open_story()  # 스토리 페이지 다시 열기
        open_viewers()
        check_viewers()  # 조회자 확인 및 저장
        close_story()
        print("3초 대기 후 다시 실행...")
        time.sleep(3)
        

except KeyboardInterrupt:
    print("스크립트가 중단되었습니다.")
    driver.quit()
