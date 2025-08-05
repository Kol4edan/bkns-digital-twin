from .analog_current_sensor import AnalogCurrentSensor

# ПЛОТНОМЕР — датчик плотности масла
class OilDensitySensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик плотности масла с диапазоном 800-900 кг/м³."""
    def __init__(self, density_min=800.0, density_max=900.0):  # кг/м3
        super().__init__(density_min, density_max)

    def measure_current(self, density):
        """Преобразует значение плотности в токовый сигнал (мА)."""
        return self.value_to_current(density)

# РАСХОДОМЕР МАСЛА
class OilFlowSensor(AnalogCurrentSensor):
    """Моделирует аналоговый расходомер масла с диапазоном 0-40 л/мин."""
    def __init__(self, flow_min=0.0, flow_max=40.0):  # л/мин
        super().__init__(flow_min, flow_max)

    def measure_current(self, flow):
        """Преобразует значение расхода в токовый сигнал (мА)."""
        return self.value_to_current(flow)


# ДАТЧИК ИЗМЕРЕНИЯ ТЕМПЕРАТУРЫ
class OilTemperatureSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик температуры масла с диапазоном 0-120 °C."""
    def __init__(self, temp_min=0.0, temp_max=120.0):  # °C
        super().__init__(temp_min, temp_max)

    def measure_current(self, temp):
        """Преобразует значение температуры в токовый сигнал (мА)."""
        return self.value_to_current(temp)


# ДАТЧИК УРОВНЯ МАСЛА
class OilLevelRadarSensor(AnalogCurrentSensor):
    """Моделирует аналоговый датчик уровня масла с диапазоном 0-10000 м³."""
    def __init__(self, level_min=0.0, level_max=10000.0):  # м3
        super().__init__(level_min, level_max)

    def measure_current(self, level):
        """Преобразует значение уровня в токовый сигнал (мА)."""
        return self.value_to_current(level)
