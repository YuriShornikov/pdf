from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table
from sqlalchemy.orm import sessionmaker
import PyPDF2
import os
import re

# Установка соединения с базой данных (в данном случае, используем PostgreSQL)
engine = create_engine('postgresql://postgres:pdf02RUS@localhost:5432/pdf', echo=True)
metadata = MetaData()

# Определение таблицы в базе данных
j1939_table = Table('j1939_data', metadata,
                    Column('ID', Integer),
                    Column('Data_length', Integer),
                    Column('Length', Integer),
                    Column('Name', String),
                    Column('RusName', String),
                    Column('Scaling', Float),
                    Column('Range', String),
                    Column('SPN', Integer)
                    )

# Создание сессии для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()

# Получение текущей директории, в которой находится скрипт
script_directory = os.path.dirname(os.path.abspath(__file__))

# Относительный путь к файлу PDF в той же папке, что и скрипт
pdf_path = os.path.join(script_directory, 'SAE J1939-71.pdf')

# Относительный путь для вывода данных из пунктов 5.3.
output_info_path_1 = os.path.join(script_directory, 'output_info_1.text')




# открываем пдф файл для чтения
with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfFileReader(file)

    # функция поиска параметров из пунктов 5.3.
    def search_param1(extracted_data):
        extracted_values = {}

        # все необходимые регулярные выражения для пунктов 5.3.
        regex_patterns = [
            re.compile(r'Data Length:\s*(\d+)', re.IGNORECASE),
            re.compile(r'Parameter Group\s*\n\s*(\d+)', re.IGNORECASE),
            re.compile(r'Parameter Group\s*\n\s*\d+\s*\(\s*(\w+)\s*\)', re.IGNORECASE),
            re.compile(r'(\d+\s*b\w+t\w+)', re.IGNORECASE),
            re.compile(r'\s\d+\s*b\w+t\w+\s*(.*)', re.IGNORECASE),
            re.compile(r'(5\.2\.\d+\.(?:\d+|\?{3}))', re.IGNORECASE)
        ]

        # перебираем регулярные выражения в поисках значений
        for regex_pattern in regex_patterns:
            matches = re.findall(regex_pattern, extracted_data)
            if matches:
                extracted_values[regex_pattern.pattern] = matches

                # Записываем извлеченные данные в файл output_info_path_1
                with open(output_info_path_1, 'w', encoding='utf-8') as output_file:
                    for pattern, values in extracted_values.items():
                        for value in values:
                            output_file.write(f"{value}\n")


    # поиск подходящего элемента с конца пдф файла через регулярное выражение
    regular = re.compile(r'5.3.\d{3}|5.3.2\?{2}', re.IGNORECASE)

    # Ищем количество элементов для поиска в разделе 5.3.
    def search_start(regular):
        count = 0
        search = False
        
        for i in range(len(pdf_reader.pages) - 1, -1, -1):
            page_text = pdf_reader.pages[i].extractText()
            search_elements = re.findall(regular, page_text)
            count += 1
            
            if '5.3.001' in search_elements:
                search = True
                break
        
        return count
    
    # получаем число элементов в 5.3.
    result_count = search_start(regular)

    # Функция поиска текста между 2мя регулярными выражениями типа 5.3. для поиска элементов
    def search_start(regular):
        end_element = ''
        extracted_data = ''
        start_element = ''
        start_found = False
        i = 1
        page = 0
        while i < 180:
            
            page_text = pdf_reader.pages[len(pdf_reader.pages) - i].extractText()
            print(page)
            print(i)
            search_value = re.findall(regular, page_text)
            # print(len(search_value))
            start_element = search_value[0]
            start_index = page_text.rfind(start_element)

            # находим первый элемент с конца
            if end_element == '':
                extracted_data += page_text[start_index:]
                page = i
                i += 1      

            # если на странице 1 элемент, end не пустой
            elif len(search_value) == 1 and end_element != '':
                extracted_data += page_text[start_index:]
                extracted_data += page_text[:end_index]
                page = i
                i += 1
                
            # если на странице 2 элемента, end и start на текущей странице
            elif len(search_value) > 1 and page == i:

                # рассматриваем страницу до известного элемента, чтобы отыскать неизвестный
                target_page = page_text[:start_index - len(start_element)]
                start_element = re.findall(regular, target_page)
                start_index = target_page.rfind(start_element[0])
                extracted_data += page_text[start_index:end_index]
                page = i
                i += 1

            # если на странице 2 элемента, end с прошлой страницы
            elif len(search_value) > 1 and page != i:
                extracted_data += page_text[start_index:]      
                extracted_data += page_text[:end_index]
                page = i
            
            else:
                page = i
                i += 1
                

            
            # вызов функции для поиска значений в пункте 5.3. через регулярки
            search_param1(extracted_data)
            end_element = start_element
            end_index = start_index        
            extracted_data = ''

        return extracted_data, start_element, end_element

    
    start_date = search_start(regular)
