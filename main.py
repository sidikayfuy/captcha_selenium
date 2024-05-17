import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

load_dotenv()


def captcha_click():
    captcha = driver.find_element(By.ID, 'captcha_widget')
    captcha.click()


def show_g_response():
    driver.execute_script("document.getElementById('g-recaptcha-response').style.display = 'block';")


def get_captcha_key():
    captcha_link = driver.find_element(By.XPATH,"//iframe[starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor')]").get_attribute('src')
    parsed_url = urlparse(captcha_link)
    key = parse_qs(parsed_url.query)['k'][0]
    return key


def send_solution_request(rucaptcha_token, captcha_key, site_url):
    print(f"Captcha solving start...")
    return json.loads(requests.get(
        f"http://rucaptcha.com/in.php?json=1&key={rucaptcha_token}&method=userrecaptcha&googlekey={captcha_key}&pageurl={site_url}").content)


def check_solution_status(rucaptcha_token, solution_id, retry=0):
    print(f"Captcha check solution {retry+1} time")
    response = requests.get(
        f"http://rucaptcha.com/res.php?key={rucaptcha_token}&action=get&id={solution_id}").content.decode('utf-8')
    if 'OK' not in response:
        if retry<=10:
            time.sleep(5)
            return check_solution_status(rucaptcha_token, solution_id, retry+1)
        else:
            return ''
    else:
        return response.split('|')[1]


if __name__ == '__main__':
    driver = webdriver.Chrome()
    print('Start')
    url = "https://account.habr.com/login/?consumer=career"
    driver.get(url)
    captcha_click()
    time.sleep(5)
    show_g_response()
    result = driver.find_element(By.ID, 'g-recaptcha-response')
    if len(result.get_attribute('value')) == 0:
        key = get_captcha_key()
        RUCAPTCHA_TOKEN = os.getenv("RUCAPTCHA_TOKEN")
        solution = send_solution_request(RUCAPTCHA_TOKEN, key, url)
        if solution['status'] == 1:
            solution_id = solution['request']
            time.sleep(20)
            solution_text = check_solution_status(RUCAPTCHA_TOKEN, solution_id)
            if solution_text != "":
                print(f"Captcha solved")
                print(f"You can fill form and submit")
                driver.execute_script(f"document.getElementById('g-recaptcha-response').value = '{solution_text}';")
                time.sleep(50)
                driver.close()
            else:
                print(f"ERROR (rucaptcha): Solution not create after 11 check times")
        else:
            print(f"ERROR (rucaptcha): {solution['error_text']}")
    else:
        print(f"Captcha solved")
        print(f"You can fill form and submit")
        time.sleep(50)
        driver.close()
