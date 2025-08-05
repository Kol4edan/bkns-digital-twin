# РЕЗЕРВУАР ДЛЯ ХРАНЕНИЯ ЖИДКОСТИ. в дальнейшем здесь будут отслеживать уровень нефтепродукта

class Tank:
    def __init__(self,
                 volume_max=10.0,     # максимальный объём бака, м³
                 density_init=800.0,  # начальная плотность жидкости, кг/м³ 
                 temperature_init=20.0,  # начальная температура, °C
                 level_init=5.0       # начальный уровень жидкости в баке, м³
                 ):
        # Максимальный объём бака (м3)
        self.volume_max = volume_max

        # Текущий уровень жидкости (м3), гарантируем, что не выше максимума
        self.level = min(level_init, volume_max)

        # Физические свойства жидкости
        self.density = density_init
        self.temperature = temperature_init

        # Текущие количества входящего и исходящего объёма (м3/ч)
        self.inflow_total = 0.0
        self.outflow_total = 0.0

        # Управляющие клапаны: списки булевых значений (True = открыт) - моделируем несколько входов и выходов
        self.inlet_valves = [False] * 4
        self.outlet_valves = [False] * 4

    def set_inlet_valve(self, idx, open_):
        """ открыть/закрыть входной клапан под номером idx (0..3) """
        # assert - функция для проверки истинности условия
        assert 0 <= idx < len(self.inlet_valves), "индекс клапана вне диапазона"
        self.inlet_valves[idx] = open_

    def set_outlet_valve(self, idx, open_):
        """ открыть/закрыть выходной клапан под номером idx (0..3) """
        assert 0 <= idx < len(self.outlet_valves), " индекс клапана вне диапазона"
        self.outlet_valves[idx] = open_

    def update(self, inlet_flow_signals, outlet_flow_signals, inflow_rates, outflow_rates,
               new_density=None, new_temp=None, dt_hours=0.5):
        """ 
        - обновление состояния бака за период dt_hours (в часах)
        - inlet_flow_signals, outlet_flow_signals: списки логических значений открытия клапанов (длина 4)
        - inflow_rates, outflow_rates: мгновенные расходы потока по каждому клапану (м3/ч) длиной 4
        - new_density: опционально, обновление плотности жидкости
        - new_temp: опционально, обновление температуры жидкости
        - dt_hours: шаг времени в часах (например, 0.5 — 30 минут)
        """

        # Обновляем состояние клапанов согласно входным сигналам
        # list - функция создания нового списка
        self.inlet_valves = list(inlet_flow_signals)
        self.outlet_valves = list(outlet_flow_signals)

        # Считаем общий входящий и исходящий поток с учётом открытых клапанов
        self.inflow_total = sum(flow if valve_open else 0.0
                                for valve_open, flow in zip(self.inlet_valves, inflow_rates))
        self.outflow_total = sum(flow if valve_open else 0.0
                                 for valve_open, flow in zip(self.outlet_valves, outflow_rates))

        # Рассчитываем изменение объёма в баке за dt_hours (м3)
        delta_volume = (self.inflow_total - self.outflow_total) * dt_hours

        # Обновляем уровень, не давая ему выйти за пределы [0, volume_max]
        self.level = min(max(self.level + delta_volume, 0.0), self.volume_max)

        # Обновляем свойства жидкости, если заданы новые значения
        if new_density is not None:
            self.density = new_density
        if new_temp is not None:
            self.temperature = new_temp

    @property
    def level(self):
        """ текущий уровень жидкости в баке (м3) """
        return self._level

    @level.setter # нужен для инкапсуляции
    def level(self, value):
        """ гарантируем, что уровень не вышел за пределы"""
        self._level = max(0.0, min(value, self.volume_max))

    @property
    def density(self):
        """ плотность жидкости (кг/м3)"""
        return self._density

    @density.setter # нужен для инкапсуляции
    def density(self, value):
        self._density = value

    @property
    def temperature(self):
        """ температура жидкости (°C)"""
        return self._temperature

    @temperature.setter # нужен для инкапсуляции
    def temperature(self, value):
        self._temperature = value

    @property
    def inlet_valve_states(self):
        """ состояния входных клапанов (список булевых значений)"""
        return self.inlet_valves

    @property
    def outlet_valve_states(self):
        """ состояния выходных клапанов (список булевых значений)"""
        return self.outlet_valves

    @property
    def inflow_rate(self):
        """ общий фактический входящий расход (м3/ч)"""
        return self.inflow_total

    @property
    def outflow_rate(self):
        """ общий фактический исходящий расход (м3/ч) - сколько жидкости ВЫХОДИТ"""
        return self.outflow_total


