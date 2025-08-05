class Valve:
    """
    Класс, моделирующий задвижку с электроприводом в промышленной системе труб.
    Реализует механизм плавного открытия/закрытия с временной задержкой.

    Атрибуты:
        state (str): Текущее состояние задвижки:
            - "open" — полностью открыта,
            - "closed" — полностью закрыта,
            - "moving" — в процессе открытия/закрытия,
            - "stopped" — остановлена в промежуточном положении.
        current_position (float): Текущее положение задвижки (0.0 - закрыто, 100.0 - открыто)
        pressure (float): Давление на входе (в барах или Па)
        temperature (float): Температура среды (в °C)
        is_moving (bool): Флаг движения задвижки (True - в движении)
        move_delay (float): Общее время открытия/закрытия (по умолчанию 2 сек)
        target_position (float): Целевое положение задвижки
        move_direction (int): Направление движения (1 - открытие, -1 - закрытие, 0 -нет движения)
    """

    def __init__(self,move_delay: float = 2.0):
        """Инициализация задвижки с параметрами по умолчанию"""
        self.current_position = 0.0   # Изначально закрыта
        self.state = "closed"         # Состояние: "open", "closed", "moving"
        self.pressure = 0.0        # Начальное давление - 0
        self.temperature = 0.0     # Начальная температура - 0
        self.is_moving = False     # Не в процессе движения
        self.move_delay = move_delay  # Установка времени задержки
        self.target_position = 0.0
        self.move_direction = 0  # 0 - нет движения, 1 - открытие, -1 - закрытие


    def update_conditions(self, pressure: float, temperature: float):
        """
        Обновляет текущие показатели давления и температуры.
        
        Args:
            pressure (float): Новое значение давления.
            temperature (float): Новое значение температуры.
        """
        self.pressure = pressure
        self.temperature = temperature

    def control(self, signal: str):
        """
        Управляет состоянием задвижки на основе внешнего сигнала.
        
        Args:
            signal (str): 
                "open" — открыть задвижку,
                "close" — закрыть задвижку,
                "stop" — остановить движение
        """
        if signal == "stop":
            # Останавливаем движение, сохраняем текущее положение
            self.is_moving = False
            self.move_direction = 0
            self.target_position = self.current_position  
            self._update_state()
            return # <--- Важно: после stop метод должен завершиться
        
        # Определяем новое целевое положение
        if signal == "open":
            self.target_position = 100.0  # <--- Теперь присваиваем self.target_position
        elif signal == "close":
            self.target_position = 0.0    # <--- Теперь присваиваем self.target_position
        else:
            # Если получен неизвестный сигнал, игнорируем команду
            print(f"Предупреждение: Неизвестный сигнал управления '{signal}'")
            return

        # Определяем направление движения: открытие или закрытие
        if self.current_position < self.target_position:
            self.move_direction = 1   # Открытие
        elif self.current_position > self.target_position:
            self.move_direction = -1  # Закрытие
        else:
            # Если уже в нужном положении — движение не требуется
            self.move_direction = 0
            self.is_moving = False
            self._update_state()
            return

        # Запускаем движение
        self.is_moving = True
        self._update_state()

    def update(self, dt: float):
        """
        Обновляет состояние задвижки с учётом прошедшего времени.

        Args:
            dt (float): Время с последнего обновления (в секундах).
        """
        if not self.is_moving:
            # Если задвижка неподвижна — ничего не делаем
            return
        
        # Рассчитываем изменение положения за dt
        step = (100.0 / self.move_delay) * dt

        if self.move_direction == 1:
            # Открываем задвижку, не превышая целевое положение
            self.current_position = min(self.current_position + step, self.target_position)
        elif self.move_direction == -1:
            # Закрываем задвижку, не опускаясь ниже целевого положения
            self.current_position = max(self.current_position - step, self.target_position)

        # Проверяем достижение целевого положения
        if self.current_position == self.target_position:
            self.is_moving = False    # Останавливаем движение
            self.move_direction = 0   # Сбрасываем направление

        # Обновляем состояние в зависимости от текущей позиции и движения
        self._update_state()

        # При полном закрытии сбрасываем параметры среды
        if self.current_position == 0.0:
            self.pressure = 0.0
            self.temperature = 0.0

    def _update_state(self):
        """
        Вспомогательный метод для обновления атрибута state
        в зависимости от текущего положения и флага движения.
        """
        if self.is_moving:
            # Если движется — состояние "moving"
            self.state = "moving"
        else:
            # Если не движется — определяем по положению
            if self.current_position == 100.0:
                self.state = "open"
            elif self.current_position == 0.0:
                self.state = "closed"
            else:
                # Остановлена в промежуточном положении
                self.state = "stopped"     

    def get_opening_coefficient(self) -> float:
        """
        Возвращает коэффициент пропускной способности от 0.0 (закрыта) до 1.0 (полностью открыта)
        """
        return self.current_position / 100.0

    def status(self) -> dict:
        """
        Возвращает текущее состояние задвижки и параметры среды.
        
        Returns:
                - state (str): состояние задвижки,
                - current_position (float): текущее положение,
                - is_moving (bool): флаг движения,
                - target_position (float): целевое положение,
                - pressure (float): давление среды,
                - temperature (float): температура среды.
        """
        return {
            "state": self.state,
            "current_position": self.current_position,
            "is_moving": self.is_moving,
            "target_position": self.target_position,
            "pressure": self.pressure,
            "temperature": self.temperature
        }

    def __str__(self):
        # Определяем текстовое представление состояния
       return f"Valve(state={self.state}, position={self.current_position:.1f}%, " \
               f"Pressure={self.pressure}, Temperature={self.temperature})"

'''
Пример 
'''
if __name__ == "__main__":
    import time

    # Создаём объект задвижки с временем полного открытия/закрытия 4 секунды
    valve = Valve(move_delay=4.0)

    print("Начальное состояние:", valve)

    # Команда открыть задвижку
    valve.control("open")
    print("\nКоманда: открыть")
    for i in range(5):
        valve.update(1.0)  # обновляем состояние за 1 секунду
        print(f"Время {i+1} сек: {valve}")
        time.sleep(0.1)  # пауза для наглядности (необязательно)



    # Через секунду команда закрыть
    valve.control("close")
    print("\nКоманда: закрыть")
    for i in range(5):
        valve.update(1.0)
        print(f"Время {i+1} сек: {valve}")
        time.sleep(0.1)

    # Команда открыть задвижку
    valve.control("open")
    print("\nКоманда: открыть")
    for i in range(5):
        valve.update(1.0)  # обновляем состояние за 1 секунду
        print(f"Время {i+1} сек: {valve}")
        time.sleep(0.1)  # пауза для наглядности (необязательно)
        if i==2:
            # Команда остановить движение
            valve.control("stop")
            print("\nКоманда: стоп")
            print(valve)

    # Команда открыть задвижку
    valve.control("open")
    print("\nКоманда: открыть")
    for i in range(5):
        valve.update(1.0)  # обновляем состояние за 1 секунду
        print(f"Время {i+1} сек: {valve}")
        time.sleep(0.1)  # пауза для наглядности (необязательно)

    # Финальное состояние
    print("\nФинальное состояние:", valve)