from .analog_current_sensor import AnalogCurrentSensor


# ДАТЧИК УРОВНЯ — датчик уровня жидкости в баке (объем в м3 от 0 до volume_max)
class TankLevelSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик уровня жидкости с диапазоном 0 - volume_max м³."""
    def __init__(self, volume_max):  # м3
        super().__init__(0.0, volume_max)

    def measure_current(self, level):
        """Преобразует значение уровня в токовый сигнал (мА)."""
        return self.value_to_current(level)


# ДАТЧИК ПЛОТНОСТИ — датчик плотности жидкости в баке (примерно 800-900 кг/м³)
class TankDensitySensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик плотности жидкости с диапазоном 800-900 кг/м³."""
    def __init__(self, density_min=800.0, density_max=900.0):  # кг/м3
        super().__init__(density_min, density_max)

    def measure_current(self, density):
        """Преобразует значение плотности в токовый сигнал (мА)."""
        return self.value_to_current(density)


# ДАТЧИК ТЕМПЕРАТУРЫ — датчик температуры жидкости в баке (°C)
class TankTemperatureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик температуры с диапазоном 0-100 °C."""
    def __init__(self, temp_min=0.0, temp_max=100.0):  # °C
        super().__init__(temp_min, temp_max)

    def measure_current(self, temperature):
        """Преобразует значение температуры в токовый сигнал (мА)."""
        return self.value_to_current(temperature)


# ДАТЧИК РАСХОДА — датчик расхода жидкости (м3/ч)
class TankFlowRateSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик расхода жидкости с диапазоном flow_min-flow_max м³/ч."""
    def __init__(self, flow_min=0.0, flow_max=10.0):  # м3/ч
        super().__init__(flow_min, flow_max)

    def measure_current(self, flow_rate):
        """Преобразует значение расхода в токовый сигнал (мА)."""
        return self.value_to_current(flow_rate)