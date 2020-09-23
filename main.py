import warnings
import csv
import easygui
import itertools
from typing import List, Tuple
from pandas.core.common import SettingWithCopyWarning
from pandas import read_excel
from xlrd import XLRDError

from models.parser import parse
from models.TopicHour import TopicHour


def main():
    header()
    warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)  # TODO: Fix

    file_path = easygui.fileopenbox(title="Выберете файл Еxcel", filetypes=[["*.xlsx", "*.xls", "Excel file"]])
    if file_path is not None:
        try:
            columns_setting = columns_settings()
            if columns_setting is None:
                print("Неправильный пункт")
                return
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
        if '/' in file_path:
            filename = file_path.split('/')[-1].split('.')[0]
            path = save_path + '/' + filename
        else:
            filename = file_path.split('\\')[-1].split('.')[0]
            path = save_path + '\\' + filename
        export_menu(path, syllabus)
    else:
        print("Такого файла нет")
    input()


def header():
    print("Syllabus Parser / Парсер учебных планов v0.3.3")
    print("Разработанно: maksim789456")


def columns_settings() -> List[int] or None:
    print("Выберите пункт который указывает на нужные номера стобцов (нумерация с нуля):")
    print("Порядок: 'номер столбца с темами', 'номер столбца с занятимии и прочем', 'номер столбца с часами'")
    print("Если в стоблце с занятиями данные разбиты на два стобца то укажите '0,1,2,3'")
    print("1. 0,1,2")
    print("2. 0,1,2,3")
    print("3. Ручной")
    collum_settings_menu = input("Выберите пункт: ")
    if collum_settings_menu == '1':
        collum_settings = '0,1,2'
    elif collum_settings_menu == '2':
        collum_settings = '0,1,2,3'
    elif collum_settings_menu == '3':
        collum_settings = input("Введите номера столбцов: ")
    else:
        return
    return list(map(int, collum_settings.split(',')))


def row_settings() -> Tuple[int, int]:
    print("Типы полей:")
    print("1. Весь текст слитно. Например: 'Самостоятельная работа 3. Бла бла бла'")
    print("2. Заголовок отдельно - текст содержимого отедьно. Пример:")
    print("Самостоятельная работа 3.")
    print("Сам текст...бла бла бла")
    practical_setting = int(input("Выберите тип занятия: "))
    independent_setting = int(input("Выберите тип самостоятельной работы: "))
    return practical_setting, independent_setting


def export_menu(path: str, syllabus: List[TopicHour]):
    print("Выберите формат CSV:")
    print("1) Spo")
    print("2) Sgk Journal")
    print("3) Spo + Sgk Journal")
    try:
        menu_p = int(input("Введите пункт: "))
    except ValueError:
        print('Вводите только число')
        return
    if menu_p == 1:
        export_sgo(path, syllabus)
    elif menu_p == 2:
        export_asu(path, syllabus)
    elif menu_p == 3:
        export_sgo(path, syllabus)
        export_asu(path, syllabus)
    else:
        print("Выбран неправильный пункт")


def export_sgo(path: str, syllabus: List[TopicHour]):
    path += '_sgo.csv'
    with open(path, mode='w', encoding='utf-8-sig') as sgo_csv_file:
        writer = csv.writer(sgo_csv_file, delimiter=';', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        current_selection = ''
        current_topic = ''
        for item in syllabus:
            place_dash = False
            if current_selection != item.selection:
                current_selection = item.selection
                place_dash = True

            if current_topic != item.topic:
                current_topic = item.topic
                place_dash = True

            description, demand = '', ''
            if place_dash:
                description, demand = '-', '-'

            homework = item.homework if item.homework != '' else '-'
            writer.writerow([item.selection, item.topic, description, demand, item.content, item.hourType.value,
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
