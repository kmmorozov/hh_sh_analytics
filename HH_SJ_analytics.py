import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv
import os


def get_vacancies(api_url, payload, headers):
    response = requests.get(api_url, payload, headers=headers)
    response.raise_for_status()
    return response.json()


def make_table(avg_salary_from_languages, title):
    vacancy_table = [
        [
            'Язык программирования ',
            'Вакансий найдено',
            'Вакансий обработано ',
            'Средняя зарплата'
        ]
    ]
    for language, language_analityc in avg_salary_from_languages.items():
        table_elements = []
        table_elements.append(language)
        table_elements.extend(language_analityc.values())
        vacancy_table.append(table_elements)
        vacancies_table = AsciiTable(vacancy_table, title)
    return vacancies_table


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        avg_salary = None
    elif salary_from and salary_to:
        avg_salary = (salary_from + salary_to) / 2
    elif salary_from:
        avg_salary = salary_from * 1.2
    elif salary_to:
        avg_salary = salary_to * 0.8
    return avg_salary


def predict_rub_salary_hh(vacancy):
    if not vacancy['salary']:
        return None
    if vacancy['salary']['currency'] != 'RUR':
        return None
    salary_from = vacancy['salary']['from']
    salary_to = vacancy['salary']['to']
    avg_salary = predict_salary(salary_from, salary_to)
    return avg_salary


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    if vacancy['currency'] != 'rub':
        return None
    avg_salary = predict_salary(salary_from, salary_to)
    return avg_salary


def get_analytics_from_hh(languages, api_hh_url, hh_headers, searching_period, city_id):
    hh_avg_salary_from_languages = {}
    for language in languages:
        salaryes_from_language_hh = []
        hh_payload = {
            'text': 'Программист {}'.format(language),
            'period': '{}'.format(searching_period),
            'area': '{}'.format(city_id)
        }
        pages_count = 1
        page = 0
        while page < pages_count:
            hh_payload['page'] = page
            vacancies = get_vacancies(api_hh_url, hh_payload, hh_headers)
            for vacancy in vacancies['items']:
                avg_salary = predict_rub_salary_hh(vacancy)
                if avg_salary:
                    salaryes_from_language_hh.append(avg_salary)
            page = page + 1
            pages_count = vacancies['pages']
            if not salaryes_from_language_hh:
                average_salary = 0
            else:
                average_salary = int(
                    sum(salaryes_from_language_hh) / len(salaryes_from_language_hh))
            vacancies_found = vacancies['found']
            vacancies_processed = len(salaryes_from_language_hh)
            vacancies_from_language = {
                'vacancies_found': vacancies_found,
                'vacancies_processed': vacancies_processed,
                'average_salary': average_salary
            }
        hh_avg_salary_from_languages[language] = vacancies_from_language
    return hh_avg_salary_from_languages


def get_analytics_from_sj(languages, api_sj_url, sj_headers, city_name):
    sj_avg_salary_from_languages = {}
    for language in languages:
        salaryes_from_language_sj = []
        sj_payload = {
            'keyword': 'программист {}'.format(language),
            'town': '{}'.format(city_name)
        }
        next_page = True
        page = 0
        while next_page:
            sj_payload['page'] = page
            vacancies = get_vacancies(api_sj_url, sj_payload, sj_headers)
            for vacancy in vacancies['objects']:
                avg_salary = predict_rub_salary_sj(vacancy)
                if avg_salary:
                    salaryes_from_language_sj.append(avg_salary)
            next_page = vacancies['more']
            page = page + 1
        if salaryes_from_language_sj:
            average_salary = int(sum(salaryes_from_language_sj) / len(salaryes_from_language_sj))
        else:
            average_salary = 0
        vacancies_found = vacancies['total']
        vacancies_processed = len(salaryes_from_language_sj)
        vacancies_from_language = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
        sj_avg_salary_from_languages[language] = vacancies_from_language
    return sj_avg_salary_from_languages


if __name__ == '__main__':
    load_dotenv()
    sjob_key = os.getenv("SJOB_KEY")
    api_hh_url = 'https://api.hh.ru/vacancies'
    api_sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    hh_headers = {'User-agent': 'Mozilla/5.0'}
    sj_headers = {
        'X-Api-App-Id': sjob_key
    }
    languages = [
        'go',
        'C',
        'CSS',
        'Scala',
        'PHP',
        'Ruby',
        'Python',
        'Java',
        'JavaScript'
    ]

    searching_period = 30
    city_id = 1
    city_name = 'Москва'
    try:
         hh_avg_salary_from_languages = get_analytics_from_hh(languages, api_hh_url, hh_headers, searching_period, city_id)
         hh_vacancies_table = make_table(hh_avg_salary_from_languages, 'HeadHunter Moscow')
         print(hh_vacancies_table.table)
    except(requests.HTTPError, requests.ConnectionError) as e:
         quit('Получили ошибку: {} '.format(e))
    try:
        sj_avg_salary_from_languages = get_analytics_from_sj(languages, api_sj_url, sj_headers, city_name)
        hh_vacancies_table = make_table(sj_avg_salary_from_languages, 'SuperJob Moscow')
        print(hh_vacancies_table.table)
    except(requests.HTTPError, requests.ConnectionError) as e:
        quit('Получили ошибку: {} '.format(e))
