import json
import re

import requests
from bs4 import BeautifulSoup
from fake_headers import Headers
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Параметры выполнения скрипта
HOST = 'https://spb.hh.ru/search/vacancy?text=python&area=1&area=2'
KEY_WORDS = ['Django', 'Flask']
KEY_CURRENCY = ['USD']


# Получение, по указанным параметрам, элементов страницы,
# с помощью seleniumв, в режиме ожидания полной загрузки страницы
def white_elements(driver, delay_seconds=1, by=By.TAG_NAME, value=None):
    return WebDriverWait(driver, delay_seconds).until(expected_conditions.presence_of_all_elements_located((by, value)))


# Поиск и получение текста элемента на странице
def element_text(soup, tag='span', attrs=None, default_text=''):
    if attrs is None:
        attrs = {}
    content_element = soup.find(tag, attrs=attrs)
    if content_element is not None:
        return content_element.text
    else:
        return default_text


def is_find_regex_in_text(regex_exp, text):
    matches = re.findall(regex_key_currency, vacancy_salary, re.MULTILINE)
    return matches is not None and len(matches) > 0


# Получение строки регулярного выражения, для поиска
# ключевых слов в тексте, переданных в массиве
def array_to_regex_string(array):
    result = r''
    for word in array:
        result += r'|'
        for symbol in word:
            result += r'['
            result += symbol.upper()
            result += symbol.lower()
            result += r']'
    return result[1:]


# Cтроки регулярных выражений для ключевых слов и валют
regex_key_words = array_to_regex_string(KEY_WORDS)
regex_key_currency = array_to_regex_string(KEY_CURRENCY)

# Заголовки запроса
request_headers = Headers(browser='firefox', os='win').generate()

# Запуск selenium
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get(HOST)

# Получение списка вакансий, в режиме ожидания полной загрузки страницы
serp_elements = white_elements(driver, delay_seconds=5, by=By.CLASS_NAME, value='serp-item__title')

vacancy_array = []
for serp_element in serp_elements:
    # Наименование вакансии
    vacancy_name = serp_element.text

    # Ссылка на вакансию
    vacancy_link = serp_element.get_attribute('href')

    # Переходим по ссылке и загружаем страницу вакансии
    html_data = requests.get(vacancy_link, headers=request_headers).content
    soup = BeautifulSoup(html_data, 'lxml')

    # Суммы и валюта компенсации
    vacancy_salary = element_text(soup, tag='div', attrs={'data-qa': 'vacancy-salary'}, default_text='з/п не указана')

    # Если в параметрах выполнения скрипта указаны валюты,
    # то пропускаем не подходящие вакансии
    if len(regex_key_currency) > 0 and not is_find_regex_in_text(regex_key_currency, vacancy_salary):
        continue

    # Описание вакансии
    vacancy_description = element_text(soup, tag='div',
                                       attrs={'class': 'g-user-content', 'data-qa': 'vacancy-description'},
                                       default_text='')

    # Если в параметрах выполнения скрипта указаны ключевые слова,
    # то пропускаем не подходящие вакансии
    if len(regex_key_words) > 0 and not is_find_regex_in_text(regex_key_words, vacancy_description):
        continue

    # Компания
    vacancy_company = element_text(soup, tag='div', attrs={'class': 'vacancy-company-details',
                                                           'data-qa': 'vacancy-company__details'},
                                   default_text='компания не указана')

    # Город
    vacancy_location = element_text(soup, tag='p', attrs={'data-qa': 'vacancy-view-location'}, default_text='')
    # Иногда указывают полный адрес, можно взять город из него
    if len(vacancy_location) == 0:
        content_element = soup.find('span', attrs={'data-qa': 'vacancy-view-raw-address'})
        if content_element is not None and content_element.contents is not None and len(
                content_element.contents) > 0:
            vacancy_location = content_element.contents[0]
        else:
            vacancy_location = 'город не указан'

    # Данные вакансии: Наименование, ссылка на hh, Компания, Город, Вилка компенсации
    vacancy = {'name': vacancy_name, 'link': vacancy_link, 'company': vacancy_company,
               'location': vacancy_location, 'salary': vacancy_salary}
    vacancy_array.append(vacancy)
    print(vacancy_name)

json_string = json.dumps(vacancy_array, ensure_ascii=False)
print(json_string)

with open('hh_data.json', 'w', encoding='utf-8') as outfile:
    outfile.write(json_string)
