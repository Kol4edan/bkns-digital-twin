# РЕЗЕРВУАРЫ СМАЗОЧНОГО МАТЕРИАЛА 
class OilTank:
    """ модель резервуара для хранения смазочного вещества с датчиками и управляющими клапанами """
    def __init__(self,
        volume_max=0.3, # м3 - максимальный размер резервуара (300 литров)
        density_init=860.0, # кг/м3, средняя плотность масла
        temperature_init=20.0, # °C
        level_init=0.25 # м3 (стартовый уровень налитого масла)                 
    ):
        # объем и уровень
        self.volume_max = volume_max # максимальный объем, м3
        self.level = min(level_init, volume_max) # текущий уровень масла, м3

        # плотность и температура
        self.density = density_init # кг/м3
        self.temperature = temperature_init # °C

        # счетчики расхода за отчетный интервал
        self.inflow = 0.0  # общий расход зашедшего масла, м3/ч
        self.outflow = 0.0 # общий расход вышедшего масла, м3/ч

        # клапаны — по 4 на каждый поток
        self.inlet_valves = [False] * 4   # входные клапаны (true — открыт)
        self.outlet_valves = [False] * 4  # выходные клапаны

    # открыть/закрыть клапаны (например, по входному управлению)
    # idx - нумерация клапонов, assert - оператор по проверке условия (если что-то не то, выдаст ошибку)
    def set_inlet_valve(self, idx, open_):
        assert 0 <= idx < 4
        self.inlet_valves[idx] = open_

    def set_outlet_valve(self, idx, open_):
        assert 0 <= idx < 4
        self.outlet_valves[idx] = open_

    def update(self, inlet_flow_signals, outlet_flow_signals, inflow_rates, outflow_rates, new_density=None, new_temp=None, dt=0.5):
        """
        обновление состояния резервуара:
        - inlet_flow_signals и outlet_flow_signals: списки логических сигналов открытия клапанов (длина 4).
        - inflow_rates и outflow_rates: список мгновенных расходов (м3/ч) по каждому входу/выходу (длина 4).
        - new_density (опционально): новое измеренное значение плотности.
        - new_temp (опционально): новое измеренное значение температуры.
        - dt: шаг по времени (часы, обычно 0.5/3600).
        """
        # обновление состояния клапанов
        # list -  функция, создающая список из любого итерируемого объекта. здесь преобразует входной параметр в список
        self.inlet_valves = list(inlet_flow_signals)
        self.outlet_valves = list(outlet_flow_signals)

        # расход по открытым клапанам
        # zip - функция, которая берёт 2 (или больше) списков и возвращает итератор, дающий пары элементов из каждого списка вместе
        self.inflow = sum([rate if open_ else 0.0 for open_, rate in zip(self.inlet_valves, inflow_rates)])
        self.outflow = sum([rate if open_ else 0.0 for open_, rate in zip(self.outlet_valves, outflow_rates)])

        # пересчет уровня (м3), скорость – м3/ч, dt – ч
        delta_volume = (self.inflow - self.outflow) * dt / 3600
        self.level = min(max(self.level + delta_volume, 0.0), self.volume_max)

        # считывание измеренных плотности и температуры, если поступили (имитация датчиков)
        if new_density is not None:
            self.density = new_density
        if new_temp is not None:
            self.temperature = new_temp

    # ДАТЧИКИ ДЛЯ СЪЕМА ДАННЫХ
    @property
    def level_radar(self):
        # измеренный радарный уровень в м3 (или % от объема)
        return self.level

    @property
    def density_meter(self):
        # плотность по плотномеру, кг/м3
        return self.density

    @property
    def flow_meter(self):
        # расход по резервуару (м3/ч) (разница вход - выход за шаг)
        return self.inflow - self.outflow

    @property
    def temperature_sensor(self):
        # температура масла в резервуаре, °C
        return self.temperature

    @property
    def inlet_valve_states(self):
        # статус входных клапанов
        return self.inlet_valves

    @property
    def outlet_valve_states(self):
        # статус выходных клапанов
        return self.outlet_valves
