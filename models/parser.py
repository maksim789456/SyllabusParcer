import pandas
import re
from typing import List
from .TopicHour import TopicHour
from .TopicHour import HourType
from pandas import DataFrame


def parse(df: DataFrame, practical_setting: int, independent_setting: int) -> List[TopicHour]:
    df = rename_columns(df)
    df = clear_nan(df)
    df = try_fix_symbols(df)
    df = try_fix_topics(df)
    df = try_fix_independent(df)

    raw_syllabus = make_raw_syllabus(df, practical_setting, independent_setting)
    return make_final_syllabus(raw_syllabus)


def make_raw_syllabus(df: DataFrame, practical_setting: int, independent_setting: int) -> List:
    # ЧД: Создание сырого массива на основе индексов
    rows_size = df['topic'].size
    selection_indexes = range_indexes(get_selection_indexes(df), rows_size)
    topic_indexes = range_indexes(get_topic_indexes(df), rows_size)
    practical_indexes = get_practical_indexes(df)
    independent_indexes = get_independent_indexes(df)

    # Групировка всего и вся. Раздел -> Тема -> Занятие -> СР
    raw_syllabus = []
    for selection_index in selection_indexes:  # Разделы
        selection_value = df.loc[selection_index.start, 'topic']
        topics = []
        for topic_index in topic_indexes:  # Темы
            if selection_index.start <= topic_index.start <= selection_index.stop:  # Если тема попадает в раздел
                topic_value = df.loc[topic_index.start, 'topic']
                practicals = []
                for practical_index in practical_indexes:  # Уроки
                    if topic_index.start <= practical_index <= topic_index.stop:  # Если занятие попадает в тему
                        if practical_setting == 1:
                            practical_value: str = df.loc[practical_index, 'content']
                        else:
                            practical_next_line_index = practical_index
                            practical_next_line_index += 1
                            practical_value: str = df.loc[practical_next_line_index, 'content']
                        independent = ""
                        independent_index = practical_index
                        independent_index += 1
                        if independent_index in independent_indexes:  # Если есть СР после занятия
                            if independent_setting == 1:
                                independent = df.loc[independent_index, 'content']
                            else:
                                independent_index += 1
                                independent = df.loc[independent_index, 'content']
                        hours = int(df.loc[practical_index, 'hours'])
                        regexp = re.compile(r'[Пп]рактичес')
                        if regexp.search(practical_value):
                            hour_type = HourType.PracticalWork
                        else:
                            hour_type = HourType.Lecture
                        practicals.append({'practical': practical_value, 'independent': independent,
                                           'hours': hours, 'hourType': hour_type})
                topics.append({'topic': topic_value, 'practicals': practicals})
        raw_syllabus.append({'selection': selection_value, 'topics': topics})
    return raw_syllabus


def make_final_syllabus(raw_syllabus: List) -> List[TopicHour]:
    # ЧД: Создание финальный массив с занятиями из групированного сырого массива
    syllabus = []
    regex = r'^\d+\.?\ ?'
    for selection in raw_syllabus:
        for topic in selection.get('topics'):
            for practical in topic.get('practicals'):
                practical_value = practical.get('practical')
                practical_value = re.sub(regex, '', practical_value, 1)  # замена число-точка на ничего
                syllabus.append(TopicHour(selection.get('selection'), topic.get('topic'), practical_value,
                                          practical.get('independent'), practical.get('hours'),
                                          practical.get('hourType')))
    return syllabus


def rename_columns(df: DataFrame) -> DataFrame:
    # Почему: При импорте из excel pandas засовывает первую строчку в название столбцов
    # ЧД: Сохраняем столбцы, переименовываем, и суем потеряные данные в первую сточку
    curr_col = df.columns
    if curr_col.size == 4:
        df.columns = ["topic", "content", "content2", "hours"]
        df.loc[-1] = [curr_col[0], curr_col[1], curr_col[2], curr_col[3]]
    else:
        df.columns = ["topic", "content", "hours"]
        df.loc[-1] = [curr_col[0], curr_col[1], curr_col[2]]

    df.index = df.index + 1
    return df.sort_index()


def clear_nan(df: DataFrame) -> DataFrame:
    # Почему: Объединённые строчки excel pandas считает как [данные, NaN, Nan]
    # ЧД: Чистим от сторочек в которых все NaN и заменяем остальные NaN на пустые строки
    df = df.dropna(axis=0, how='all')
    df = df.reset_index()
    del df['index']
    df.loc[:, 'topic'] = df['topic'].fillna("")
    df.loc[:, 'hours'] = df['hours'].fillna(1)
    if df.columns.size == 4:
        df.loc[:, 'content'] = df['content'].fillna("")
        df.loc[:, 'content2'] = df['content2'].fillna("")
    else:
        df.loc[:, 'content'] = df['content'].fillna("")
    return df


def try_fix_topics(df: DataFrame) -> DataFrame:
    # Почему: Некоторые авторы 'ТП' делают тему разбитую на 2 строчки
    # ЧД: Проверяем что следующая строчка после темы не пустая и собираем тему в одну строчку
    topic_index = get_topic_indexes(df)
    for index in topic_index:
        cur_row_value = df.loc[index].get('topic')

        new_row_index = index + 1
        next_row_value = df.loc[new_row_index].get('topic')
        if next_row_value != "":
            cur_row_value += " " + next_row_value
            df.at[index, 'topic'] = cur_row_value
            df.at[new_row_index, 'topic'] = ""

    return df


def try_fix_independent(df: DataFrame) -> DataFrame:
    # Почему: Некоторые авторы 'ТП' делают самостоятельную работу разбитую на 2 строчки
    # ЧД: Чистим строчку от лишних пробелов, проверяем что строчка c числом маленькая и собираем все в одну строчку.
    # В конце удаляем второй столбец
    practical_index = get_practical_indexes(df)
    if df.columns.size != 4:
        return df

    for index in practical_index:
        df.loc[index, 'content'] = " ".join(df.loc[index, 'content'].split())

    for index in practical_index:
        row = df.loc[index]
        curr_col_value = row.get('content')
        next_col_value = row.get('content2')
        if len(curr_col_value) < 5:
            df.loc[index, 'content'] = curr_col_value + next_col_value

    del df['content2']
    return df


def try_fix_symbols(df: DataFrame) -> DataFrame:
    # Убираем всякий шлак, заменяем непонятные
    df.loc[:, 'topic'] = df['topic'].str.replace('^\d$', '',)
    df.loc[:, 'content'] = df['content'].str.replace('\xa0', '')
    df.loc[:, 'content'] = df['content'].str.replace('\xad', '')
    df.loc[:, 'content'] = df['content'].str.replace('\d\)', '')
    df.loc[:, 'content'] = df['content'].str.replace(';', ':')

    df.loc[:, 'topic'] = df['topic'].fillna("")
    df.loc[:, 'content'] = df['content'].fillna("")
    return df


def range_indexes(old_indexes: List[int], df_size: int) -> List[pandas.RangeIndex]:
    # ЧД: Превращаем список из индексов в RangeIndex.
    indexes = []
    i = 0
    while i <= len(old_indexes) - 1:
        curr_value = old_indexes[i]
        next_index = i
        next_index += 1
        if i == len(old_indexes) - 1:
            indexes.append(pandas.RangeIndex(curr_value, df_size))
        else:
            next_value = old_indexes[next_index]
            next_value -= 1
            indexes.append(pandas.RangeIndex(curr_value, next_value))
        i += 1

    return indexes


# Методы для получения всех необходимых индексов (для раздела, темы, занятия и самостоятельной)
def get_selection_indexes(df: DataFrame):
    selection_index = df[df['topic'].str.contains('(?:Р|р)аздел')].index.values
    return selection_index


def get_topic_indexes(df: DataFrame):
    topic_index = df[df['topic'].str.contains('(?:Т|т)ема')].index.values
    return topic_index


def get_practical_indexes(df: DataFrame):
    practical_index = df[df['content'].str.contains('^\d+\.?')].index.values
    return practical_index


def get_independent_indexes(df: DataFrame):
    independent_index = df[df['content'].str.contains('(?:С|с)амостоятельная')].index.values
    return independent_index
