from .analog_current_sensor import AnalogCurrentSensor
    
# ДАТЧИК ТЕМПЕРАТУРЫ
class ValveTemperatureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик температуры с диапазоном от -50 до +150 °C."""
    def __init__(self, temp_min=-50.0, temp_max=150.0):  # градусы Цельсия
        super().__init__(temp_min, temp_max)

    def measure_current(self, temperature):
        """Преобразует значение температуры в токовый сигнал (мА)."""
        return self.value_to_current(temperature)


# ДАТЧИК ДАВЛЕНИЯ
class ValvePressureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик давления с диапазоном от 0 до 10 бар."""
    def __init__(self, pressure_min=0.0, pressure_max=10.0):  # бар
        super().__init__(pressure_min, pressure_max)

    def measure_current(self, pressure):
        """Преобразует значение давления в токовый сигнал (мА)."""
        return self.value_to_current(pressure)


# ДАТЧИК ПОЛОЖЕНИЯ
class ValvePositionSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик положения задвижки с диапазоном 0-100 %."""
    def __init__(self, position_min=0.0, position_max=100.0):  # проценты открытия
        super().__init__(position_min, position_max)

    def measure_current(self, position):
        """Преобразует значение положения в токовый сигнал (мА)."""
        return self.value_to_current(position)
