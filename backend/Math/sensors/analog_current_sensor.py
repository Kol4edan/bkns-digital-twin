#АНАЛОГОВЫЙ ДАТЧИК
class AnalogCurrentSensor:
    """
    Класс для преобразования физического значения параметра в аналоговый ток 4–20 мА.
    Значения вне диапазона возвращают 0 мА — сигнал обрыва.
    """

    def __init__(self, physical_min, physical_max, current_min=4.0, current_max=20.0):
        # Инициализация диапазона физического параметра и соответствующего сигнала тока (мА)
        self.physical_min = physical_min
        self.physical_max = physical_max
        self.current_min = current_min
        self.current_max = current_max

    def value_to_current(self, value):
        # Возвращает 0 мА, если значение выходит за пределы диапазона
        if value < self.physical_min-0.00001 or value > self.physical_max+0.00001:
            return 0.0  
        
        # Линейное масштабирование значения в диапазон
        scale = (self.current_max - self.current_min) / (self.physical_max - self.physical_min)
        current = self.current_min + (value - self.physical_min) * scale
        return round(current, 3)
