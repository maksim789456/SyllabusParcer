import warnings
import csv
import easygui
import itertools
from typing import List, Tuple

from PyInquirer import prompt
from pandas.core.common import SettingWithCopyWarning
from pandas import read_excel
from xlrd import XLRDError

from models.ColumnsValidator import ColumnsValidator
from models.NumberValidator import NumberValidator
from models.parser import parse
from models.TopicHour import TopicHour


def main():
    header()
    warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)  # TODO: Fix

    file_path = easygui.fileopenbox(title="Выберете файл Еxcel", filetypes=[["*.xlsx", "*.xls", "Excel file"]])
    if file_path is not None:
        try:
            columns_setting = columns_settings()
            book = read_excel(file_path, usecols=columns_setting)
        except XLRDError:
            print("Неподерживаемый формат. Возможно вы выбрали не тот файл")
            return
        practical_setting, independent_setting = row_settings()
        syllabus = parse(book, practical_setting, independent_setting)
        print("Парсинг произошел успешно")
        save_path = easygui.diropenbox(title="Выберете место куда сохранить csv")
        if save_path is None:
            print("Не выбрана папка куда сохранять!")
            return
        split = '\\'
        if '/' in file_path:
            split = '/'

        filename = file_path.split(split)[-1].split('.')[0]
        export_menu(save_path + split + filename, syllabus)
    else:
        print("Такого файла нет")
    input()


def header():
    print("Syllabus Parser / Парсер учебных планов v0.4")
    print("Разработанно: maksim789456")


def columns_settings() -> List[int]:
    choices = ['0,1,2', '0,1,2,3', 'Ручной']
    question = [{'type': 'list', 'name': 'collum_settings', 'choices': choices, 'message': 'Выберите пункт:'}]
    print("Выберите пункт который указывает на нужные номера стобцов (нумерация с нуля):")
    print("Порядок: 'столбец с темами', 'столбец с занятимии и прочем', 'столбец с часами'")
    print("Если в стоблце с занятиями данные разбиты на два стобца то укажите '0,1,2,3'")
    answer = prompt(question)['collum_settings']
    if choices.index(answer) == 2:
        user_input = prompt([{'type': 'input', 'name': 'columns', 'validate': ColumnsValidator,
                              'message': 'Введите номера стобцов в формате 0,1,2:'}])['columns']
        return list(map(int, user_input.split(',')))
    else:
        return list(map(int, answer.split(',')))


def row_settings() -> Tuple[int, ...]:
    choices = ['Весь текст слитно', 'Заголовок отдельно - содержимое отдельно']
    questions = [{'type': 'list', 'name': 'practical_setting', 'choices': choices,
                  'message': 'Выберите тип поля для занятий:', 'validate': NumberValidator},
                 {'type': 'list', 'name': 'independent_setting', 'choices': choices,
                  'message': 'Выберите тип поля для самостоятельных работ:', 'validate': NumberValidator}]
    answers = []
    for key, value in prompt(questions).items():
        answers.append(choices.index(value))
    return tuple(answers)


def additional_settings() -> Tuple[bool, ...]:
    questions = [{'type': 'confirm', 'name': 'dash_detect', 'message': "Парсить занятия вида '30-34'?"},
                 {'type': 'confirm', 'name': 'enable_debug', 'message': "Включить отладочное окно?"}]
    answers = []
    for key, value in prompt(questions).items():
        answers.append(value)
    print(answers)
    return tuple(answers)


def export_menu(path: str, syllabus: List[TopicHour]):
    choices = ['Sgo', 'Sgk Journal', 'Sgo + Sgk Journal']
    question = [{'type': 'list', 'name': 'export_type', 'choices': choices, 'message': 'Выберите формат CSV:'}]
    index = choices.index(prompt(question)['export_type'])
    if index == 0:
        export_sgo(path, syllabus)
    elif index == 1:
        export_asu(path, syllabus)
    elif index == 2:
        export_sgo(path, syllabus)
        export_asu(path, syllabus)


def export_sgo(path: str, syllabus: List[TopicHour]):
    path += '_sgo.csv'
    with open(path, mode='w', encoding='utf-8-sig') as sgo_csv_file:
        writer = csv.writer(sgo_csv_file, delimiter=';', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        current_selection = ''
        current_topic = ''
        for item in syllabus:
            selection = ''
            place_dash = False
            if current_selection != item.selection:
                current_selection = item.selection
                selection = item.selection
                place_dash = True

            topic = ''
            if current_topic != item.topic:
                current_topic = item.topic
                topic = item.topic
                place_dash = True

            description, demand = '', ''
            if place_dash:
                description, demand = '-', '-'

            homework = item.homework if item.homework != '' else '-'
            writer.writerow([selection, topic, description, demand, item.content, item.hourType.value,
                             item.countHours, '-', homework])


def export_asu(path: str, syllabus: List[TopicHour]):
    path += '_asu.csv'
    with open(path, mode='w', encoding='utf-8-sig') as asu_csv_file:
        writer = csv.writer(asu_csv_file, delimiter=';', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        row_index = 1
        for item in syllabus:
            for _ in itertools.repeat(None, item.countHours):
                writer.writerow([row_index, item.content, item.homework])
                row_index += 1


if __name__ == '__main__':
    main()
