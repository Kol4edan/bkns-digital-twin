from .analog_current_sensor import AnalogCurrentSensor
# ДАТЧИК ТЕМПЕРАТУРЫ НАСОСА
class PumpTemperatureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик температуры различных частей насоса (0–120°C)."""
    def __init__(self, temp_min=0.0, temp_max=40.0):  # °C
        super().__init__(temp_min, temp_max)

    def measure_current(self, temp):
        """Преобразует температуру в ток (мА)."""
        return self.value_to_current(temp)


# ДАТЧИК ДАВЛЕНИЯ НАСОСА
class PumpPressureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик давления на выходе насоса (0–3 МПа)."""
    def __init__(self, pressure_min=0.0, pressure_max=3):  # МПа
        super().__init__(pressure_min, pressure_max)

    def measure_current(self, pressure):
        """Преобразует давление в ток (мА)."""
        return self.value_to_current(pressure)


# ДАТЧИК ТОКА ДВИГАТЕЛЯ НАСОСА
class PumpMotorCurrentSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик тока двигателя насоса (0–15 А)."""
    def __init__(self, current_min=0.0, current_max=15.0):  # А
        super().__init__(current_min, current_max)

    def measure_current(self, current):
        """Преобразует ток двигателя в токовый сигнал (мА)."""
        return self.value_to_current(current)


# ДАТЧИК РАСХОДА ЧЕРЕЗ НАСОС
class PumpFlowSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик расхода через насос (0–80 м³/ч)."""
    def __init__(self, flow_min=0.0, flow_max=80.0):  # м³/ч
        super().__init__(flow_min, flow_max)

    def measure_current(self, flow):
        """Преобразует расход в ток (мА)."""
        return self.value_to_current(flow)


# ДАТЧИК СКОРОСТИ ВРАЩЕНИЯ ВАЛА
class PumpShaftSpeedSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик скорости вращения вала насоса (0–2000 об/мин)."""
    def __init__(self, speed_min=0.0, speed_max=2000.0):  # об/мин
        super().__init__(speed_min, speed_max)

    def measure_current(self, speed):
        """Преобразует скорость вращения в ток (мА)."""
        return self.value_to_current(speed)