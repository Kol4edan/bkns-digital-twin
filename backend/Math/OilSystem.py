import asyncio
import json
import math
import time
from .tanks.OilTank import OilTank
from asyncua import Client, ua, Server


# Конфигурацияp
interval_sec = 0.5  # более частый опрос для плавности

# МАСЛОНАСОСЫ 
class OilPump:
    """ модель отдельного маслонасоса (основной или резервный) """
    def __init__(self, name, nominal_flow, max_pressure):
        self.name = name # название/имя насоса
        self.nominal_flow = nominal_flow # номинальный расход масла
        self.max_pressure = max_pressure # максимальное давление, которое может создать насос
        self.running = False
        self.pump_speed = 0.0  # 0..1 - скорость работы насоса, исп-ся для расчета текущего расхода и давления

    def update(self, command_run, command_stop):
        """ обновление состояния насоса по входным сигналам (только чтение команд) """
        if command_run:
            self.running = True
            self.pump_speed = 1.0
        if command_stop:
            self.running = False
            self.pump_speed = 0.0


# МАСЛОСИСТЕМА использует 2 маслонасоса, подает масло к насосам и подшипникам
class OilSystem:
    def __init__(self, pump_id: int, temp_limit = 75.0):
        """ модель маслосистемы центробежного насоса (pump_id): идентификатор насоса (0 для NA4, 1 для NA2) """
        self.tank = OilTank() # маслобак

        self.pump_id = pump_id
        self.temp_limit = temp_limit  # предельная температура масла (°C)
        self.temperature = 40.0  # температура масла (°C)
        self.viscosity = 46.0  # вязкость масла (сСт)
        self.ambient_temp = 25.0 # температура окружающей среды (°C)

        # Маслонасосы (основной и резервный)
        self.main_pump = OilPump("main", nominal_flow = 20.0, max_pressure = 4.0)
        self.reserve_pump = OilPump("reserve", nominal_flow = 20.0, max_pressure = 4.0)

        # Параметры системы
        self.nominal_flow = 20.0  # номинальный расход (л/мин)
        self.max_pressure = 4.0  # максимальное давление (бар)

        # Теплофизические свойства
        self.oil_mass = 15.0  # условная масса масла (кг)
        self.oil_heat_capacity = 1.67  # теплоемкость масла (кДж/кг·К)
        self.heat_transfer_coeff = 0.02  # коэффициент теплоотдачи
        self.nominal_viscosity = 46.0  # номинальная вязкость (сСт)

        # Состояния
        self.running = False  # состояние маслонасоса
        self.pressure_ok = False  # флаг нормального давления
        self.temp_ok = True  # температура в норме
        self.flow_rate = 0.0  # расход масла (л/мин)
        self.pressure = 0.0  # текущее давление (бар)

    def update(self, command_main_run, command_main_stop, command_reserve_run, command_reserve_stop, dt, inlet_signals, outlet_signals, inflow_rates, outflow_rates, new_density=None, new_temp=None):
	
	# обновим состояние внутреннго резервуара
        self.tank.update(inlet_signals, outlet_signals, inflow_rates, outflow_rates, new_density, new_temp, dt)

        # 1. Обновление состояния маслонасосов
        # command_main_run - сигнал запуска основного насоса, command_main_stop - сигнал остановки
        # метод update меняет внутренние флаги running и pump_speed согласно этим командам
        self.main_pump.update(command_main_run, command_main_stop) # главный насос
        self.reserve_pump.update(command_reserve_run, command_reserve_stop) # резервный насос
        
        # Состояние маслосистемы — работает, если хотя бы один насос работает
        self.running = self.main_pump.running or self.reserve_pump.running

        # Параметры масла из резервуара
        self.temperature = self.tank.temperature_sensor
        oil_viscosity_input = None 
        oil_flow_input = self.tank.flow_meter
        oil_density_input = self.tank.density_meter

        # обновляем вязкость по температуре (если не передана, рассчитываем)
        if oil_viscosity_input is not None: # либо есть значение, либо отсутствует 
            self.viscosity = oil_viscosity_input
        else:
            k = 0.03
            self.viscosity = self.nominal_viscosity * math.exp(-k * (self.temperature - 40))
            self.viscosity = max(10, min(self.viscosity, 100))

        # 2. Суммарный расход и давление (если работает хотя бы один насос)
        total_speed = max(self.main_pump.pump_speed, self.reserve_pump.pump_speed)
        viscosity_factor = 1 - (self.viscosity - self.nominal_viscosity) / 100
        self.flow_rate = (self.main_pump.nominal_flow * self.main_pump.pump_speed + self.reserve_pump.nominal_flow * self.reserve_pump.pump_speed) * viscosity_factor

        # Динамическое давление с колебаниями (для имитации реальной работы)
        time_factor = 1 + 0.1 * math.sin(time.time() / 10)
        self.pressure = min(self.main_pump.max_pressure, self.main_pump.max_pressure * total_speed * time_factor)

        # 3. Термодинамика: нагрев масла при работе, охлаждение всегда!!!
        heating_power = 0.0
        if self.main_pump.pump_speed > 0:
            heating_power += self.pressure * (self.main_pump.nominal_flow * self.main_pump.pump_speed) / 600
        if self.reserve_pump.pump_speed > 0:
            heating_power += self.pressure * (self.reserve_pump.nominal_flow * self.reserve_pump.pump_speed) / 600

        # Расчёт изменения температуры за dt
        delta_heat = heating_power * dt / (self.oil_mass * self.oil_heat_capacity)  # нагрев
        cooling = self.heat_transfer_coeff * (self.temperature - self.ambient_temp) * dt  # охлаждение

        # Обновление температуры с ограничением сверху
        temperature_new = self.temperature + delta_heat - cooling
        if temperature_new > self.temp_limit:
            self.temperature = self.temp_limit
        else:
            self.temperature = temperature_new

        # Ограничение температуры снизу (не может быть ниже окружающей)
        self.temperature = max(self.temperature, self.ambient_temp)
      

        # 5. Проверка аварийных состояний
        """ проверяется, достаточно ли давление для норм работы """
        self.pressure_ok = self.pressure >= 2.0  # минимальное рабочее давление
        self.temp_ok = self.temperature < self.temp_limit 


    # пуск/стоп маслосистемы
    def start(self):
        """Запуск маслосистемы — запускаем главный насос, резервный выключен"""
        self.update(True, False, False, True, dt=0.1)

    def stop(self):
        """Остановка маслосистемы — останавливаем оба насоса"""
        self.update(False, True, False, True, dt=0.1)

    # Свойства для доступа к параметрам в нужном формате
    @property
    def oil_pressure(self): # передача давления 
        return self.pressure

    @property
    def oil_system_running(self):
        return self.running

    @property
    def oil_temperature(self): # передача температуры 
        return self.temperature

    @property
    def oil_flow_rate(self): # передача расхода масла
        return self.flow_rate
