import time
from BKNS import BKNS



def tests (bkns:BKNS,test_id=None):

    try:
        valid_scenarios = {1, 2, 3, 4, 5, 6, 7} #индексы сценариев

        if test_id not in valid_scenarios:
            print(f"Предупреждение: сценарий {test_id} не определён. Запускается предыдущий сценарий.")
            test_id = 1
        

        print(f"\n=== Запуск сценария {test_id} ===")

        match test_id:
            
            #Функция для запуска определенного сценария для объекта БКНС. 
            #В качестве результата выводится таблица значений с датчиков

            case 1:

            #Пояснение происходящего
                print(f"\n=== Плавная работа одного из насосов (NA4) ===")

            # Сценарий 1: Плавный запуск и остановка насоса NA4 с нагревом

                print(f"\nЗапуск насоса NA4")
                #Открытие задвижек
                bkns.control_valve('in_0', 'open') 
                bkns.control_valve('out_0', 'open') 
                #Запуск насосов
                bkns.control_pump(0, start=True) 
                bkns.control_oil_pump(0, start=True)  

                #Работа насоса NA4 - ожидается рост давления, скорости насоса и тока, легкий рост температуры
                for _ in range(50):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОстановка насоса NA4")
                #Остановка насосов, задвижки оставляем
                bkns.control_pump(0, start=False)
                bkns.control_oil_pump(0, start=False)

                #Плавная остановка насоса NA4 - ожидается падение давления, скорости насоса и тока, остывание
                for _ in range(50):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)            


            case 2:

            #Пояснение происходящего
                print(f"\n=== Плавная работа обоих насосов  ===")

            #Сценарий 2: Работа сначала одного насоса, а после и второго (работа 2 насосов одновременно)

                print(f"\nЗапуск насоса NA4")
                #Открытие задвижек
                bkns.control_valve('in_0', 'open') 
                bkns.control_valve('out_0', 'open') 
                #Запуск насосов
                bkns.control_pump(0, start=True) 
                bkns.control_oil_pump(0, start=True)  

                #Работа насоса NA4 - ожидается
                for _ in range(15):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nЗапуск насоса NA2")
                #Открытие задвижек
                bkns.control_valve('in_1', 'open')
                bkns.control_valve('out_1', 'open')
                #Запуск насосов
                bkns.control_pump(1, start=True) 
                bkns.control_oil_pump(1, start=True)  

                #Работа обоих насосов - ожидается
                for _ in range(35):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОстановка насоса NA4")
                #Остановка насосов, задвижки оставляем
                bkns.control_pump(0, start=False)
                bkns.control_oil_pump(0, start=False)

                #Плавная остановка насоса NA4 - ожидается
                for _ in range(15):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОстановка насоса NA2") 
                #Остановка насосов, задвижки оставляем 
                bkns.control_pump(1, start=False)
                bkns.control_oil_pump(1, start=False)

                #Плавная остановка обоих насосов - ожидается
                for _ in range(35):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)
                

            case 3:

            #Пояснение происходящего
                print(f"\n=== Работа обоих насосов и закрытие входной задвижки у одного насоса ===")
     
            #Сценарий 3: Работа обоих насосов и переход одного в режим закрытой входной задвижки

                print(f"\nЗапуск обоих насосов")
                #Запуск насосов
                bkns.control_pump(0, start=True)
                bkns.control_pump(1, start=True)
                bkns.control_oil_pump(0, start=True)
                bkns.control_oil_pump(1, start=True)
                #Открытие задвижек
                for key in ['in_0', 'out_0', 'in_1', 'out_1']:
                    bkns.control_valve(key, 'open') 

                #Работа обоих насосов - ожидается
                for _ in range(25):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                #Закрытие входной задвижки - ожидается 
                print(f"\nЗакрытие входной задвижки NA4")
                bkns.control_valve('in_0', 'close')
                for _ in range(40):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОткрытие входной задвижки NA4")
                #Открытие задвижки
                bkns.control_valve('in_0', 'open') 

                #Возобновление прежней работы - ожидается 
                for _ in range(35):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

            case 4:

            #Пояснение происходящего
                print(f"\n=== Работа обоих насосов и закрытие выходной задвижки у одного насоса ===")
     
            #Сценарий 4: Работа обоих насосов и переход одного в режим закрытой выходной задвижки

                print(f"\nЗапуск обоих насосов")
                #Запуск насосов
                bkns.control_pump(0, start=True)
                bkns.control_pump(1, start=True)
                bkns.control_oil_pump(0, start=True)
                bkns.control_oil_pump(1, start=True)
                #Открытие задвижек
                for key in ['in_0', 'out_0', 'in_1', 'out_1']:
                    bkns.control_valve(key, 'open') 

                #Работа обоих насосов - ожидается 
                for _ in range(25):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                #Закрытие выходной задвижки - ожидается 
                print(f"\nЗакрытие выходной задвижки NA2")
                bkns.control_valve('out_1', 'close')
                for _ in range(40):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОткрытие выходной задвижки NA2")
                #Открытие задвижки
                bkns.control_valve('out_1', 'open') 

                #Возобновление прежней работы - ожидается 
                for _ in range(35):

                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

            case 5:

            #Пояснение происходящего
                print(f"\n=== Работа обоих насосов и закрытие задвижек у одного насоса ===")
     
            #Сценарий 5: Работа обоих насосов и переход одного в режим закрытых задвижек 

                print(f"\nЗапуск обоих насосов")
                #Запуск насосов
                bkns.control_pump(0, start=True)
                bkns.control_pump(1, start=True)
                bkns.control_oil_pump(0, start=True)
                bkns.control_oil_pump(1, start=True)
                #Открытие задвижек
                for key in ['in_0', 'out_0', 'in_1', 'out_1']:
                    bkns.control_valve(key, 'open') 

                #Работа обоих насосов - ожидается 
                for _ in range(25):

                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                #Закрытие задвижек - ожидается 
                print(f"\nЗакрытие задвижек NA2")
                bkns.control_valve('in_1', 'close')
                bkns.control_valve('out_1', 'close')
                for _ in range(40):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОткрытие задвижек NA2")
                #Открытие задвижки
                bkns.control_valve('in_1', 'open') 
                bkns.control_valve('out_1', 'open') 

                #Возобновление прежней работы - ожидается 
                for _ in range(35):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

            case 6:

            #Пояснение происходящего
                print(f"\n=== Работа обоих насосов и выключение маслосистемы у одного насоса ===")
     
            #Сценарий 6: Работа обоих насосов и переход одного в режим выключенной маслосистемы

                print(f"\nЗапуск обоих насосов")
                #Запуск насосов
                bkns.control_pump(0, start=True)
                bkns.control_pump(1, start=True)
                bkns.control_oil_pump(0, start=True)
                bkns.control_oil_pump(1, start=True)
                #Открытие задвижек
                for key in ['in_0', 'out_0', 'in_1', 'out_1']:
                    bkns.control_valve(key, 'open') 

                #Работа обоих насосов - ожидается 
                for _ in range(25):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                #Выключение маслосистемы NA4- ожидается 
                print(f"\nВыключение маслосистемы NA4")
                bkns.control_oil_pump(0, start=False)
                for _ in range(40):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nВключение маслосистемы NA4")
                #Включение маслосистемы NA4
                bkns.control_oil_pump(0, start=True)

                #Возобновление прежней работы - ожидается 
                for _ in range(35):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

            case 7:

            #Пояснение происходящего
                print(f"\n=== Работа обоих насосов и заклинивание (остановка) задвижки у одного насоса ===")
     
            #Сценарий 7: Работа обоих насосов и переход одного в режим выключенной маслосистемы

                print(f"\nЗапуск обоих насосов")
                #Запуск насосов
                bkns.control_pump(0, start=True)
                bkns.control_pump(1, start=True)
                bkns.control_oil_pump(0, start=True)
                bkns.control_oil_pump(1, start=True)
                #Открытие задвижек
                for key in ['in_0', 'out_0', 'in_1', 'out_1']:
                    bkns.control_valve(key, 'open') 

                #Работа обоих насосов - ожидается 
                for _ in range(25):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                #Закрытие выходной задвижки - ожидается 
                print(f"\nЗакрытие выходной задвижки NA4")
                bkns.control_valve('out_0', 'close')
                for _ in range(4):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОстановка задвижки NA4")
                #Остановка задвижки
                bkns.control_valve('out_0', 'stop')
                #Работа в данном режиме - ожидается 
                for _ in range(36):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

                print(f"\nОткрытие задвижки NA4")
                #Открытие задвижки
                bkns.control_valve('out_0', 'open')

                #Возобновление прежней работы - ожидается 
                for _ in range(35):
                    bkns.update_system()
                    print(bkns._format_sensors_table(bkns.get_status()))
                    time.sleep(0.3)

            case _:
                print(f"Сценарий {test_id} не определён.")


    #Нажатие на Ctrl+C прерывает сценарии
    except KeyboardInterrupt:
        print("\nСценарий прерван пользователем.")

import sys

if __name__ == "__main__":
    scenario_number = 7

    bkns = BKNS()
    
    filename = f"test_output_{scenario_number}.txt"  # Формируем имя файла с номером сценария
    
    with open(filename, "w", encoding='utf-8') as f:
        original_stdout = sys.stdout
        try:
            sys.stdout = f
            tests(bkns,scenario_number)
        finally:
            sys.stdout = original_stdout
            
    print(f"Сценарий выполнен. Результаты записаны в файл '{filename}'")
