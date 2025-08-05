
from .analog_current_sensor import AnalogCurrentSensor
# ДАТЧИК ДАВЛЕНИЯ НА ВХОДЕ ТРУБЫ
class PipePressureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик давления трубы (0–3 МПа)."""
    def __init__(self, pressure_min=0.0, pressure_max=3):  # МПа
        super().__init__(pressure_min, pressure_max)

    def measure_current(self, pressure):
        """Преобразует давление в ток (мА)."""
        return self.value_to_current(pressure)

# ДАТЧИК ТЕМПЕРАТУРЫ В ТРУБЕ
class PipeTemperatureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик температуры в трубе (0–40°C)."""
    def __init__(self, temp_min=0.0, temp_max=40.0):  # °C
        super().__init__(temp_min, temp_max)

    def measure_current(self, temp):
        """Преобразует температуру в трубе в ток (мА)."""
        return self.value_to_current(temp)