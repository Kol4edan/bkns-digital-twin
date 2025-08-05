import time
from typing import Dict
from .OilSystem import OilSystem
from .Pump import CentrifugalPump
from .Pipe import PipeModel
from .Valve import Valve
from .sensors.valve_sensors import ValveTemperatureSensor, ValvePressureSensor,ValvePositionSensor
from .sensors.pump_sensors import PumpFlowSensor,PumpMotorCurrentSensor,PumpPressureSensor,PumpShaftSpeedSensor,PumpTemperatureSensor
from .sensors.pipe_sensors import PipePressureSensor,PipeTemperatureSensor
from .sensors.oil_sensors import  OilFlowSensor, OilTemperatureSensor
from .sensors.tank_sensors import TankLevelSensor, TankDensitySensor, TankTemperatureSensor, TankFlowRateSensor


class BKNS:
    """
    Одна установка состоит из 2 насосов. 
    Каждый насос имеет входную задвижку и выходную;
    После задвижек идут трубы -входная и выходная.
    Трубы выходят в общую выходную и общую входную.
    Каждый насос подключен к маслосистеме.
    Итог: 2 насоса
        2 маслосистемы
        4 задвижки
        6 труб (2 входные, 2 выходные, 1 общая входная, 1 общая выходная)
    """

    def __init__(self,inlet_pressure=1.9, inlet_temperature=25.0):
        
        #Параметры для входной трубы (если труба откуда-то идет)
        self.inlet_pressure = inlet_pressure  # По умолчанию 1.9 (относительное давление)
        self.inlet_temperature = inlet_temperature  # По умолчанию 25°C

        # Инициализация маслосистем для каждого насоса
        self.oil_systems = [
            OilSystem(0),  # Маслосистема для насоса NA4
            OilSystem(1)   # Маслосистема для насоса NA2
        ]

        # Команды управления маслонасосами: 
        # для каждого маслонасоса отдельные флаги запуска/остановки
        self.oil_pump_commands = [
            {'start': False, 'stop': True},  # Маслонасос для NA4
            {'start': False, 'stop': True}   # Маслонасос для NA2
        ]

        # Инициализация насосов с привязкой к соответствующим маслосистемам
        self.pumps = [
            CentrifugalPump(self.oil_systems[0],'NA4'),  # Насос NA4
            CentrifugalPump(self.oil_systems[1],'NA2')   # Насос NA2
        ]

        # Задвижки: входные и выходные для каждого насоса
        self.valves = {
            'in_0': Valve(),  # Входная задвижка NA4
            'out_0': Valve(), # Выходная задвижка NA4
            'in_1': Valve(),  # Входная задвижка NA2
            'out_1': Valve()  # Выходная задвижка NA2
        }

        # Трубы входные и выходные для каждого насоса, а также общие
        self.pipes = {
            'in_0': PipeModel(),   # Входная труба NA4
            'out_0': PipeModel(),  # Выходная труба NA4
            'in_1': PipeModel(),   # Входная труба NA2
            'out_1': PipeModel(),  # Выходная труба NA2
            'main_inlet': PipeModel(),  # Общая входная труба (до разделения)
            'main_outlet': PipeModel()  # Общая выходная труба (после объединения)
        }

        # Физические параметры жидкости
        self.rho = 1000       # Плотность жидкости [кг/м3]
        self.mu = 1e-3        # Динамическая вязкость [Па·с]
        self.m_dot_A = 0.5      # Массовый расход [кг/с]
        self.m_dot_B = 0.5      # Массовый расход [кг/с]
        
        #Датчики
        #Задвижки
        self.valve_sensors = {}
        for key in self.valves.keys():
            self.valve_sensors[key] = {
                'temperature_sensor': ValveTemperatureSensor(),
                'pressure_sensor': ValvePressureSensor(),
                'position_sensor': ValvePositionSensor()
            }

        #Насосы
        self.pump_sensors = {}
        for pump_id, pump in enumerate(self.pumps):
            self.pump_sensors[pump_id] = {
            'bearing_work_temp_sensor': PumpTemperatureSensor(),
            'bearing_field_temp_sensor': PumpTemperatureSensor(),
            'motor_bearing_work_temp_sensor': PumpTemperatureSensor(),
            'motor_bearing_field_temp_sensor': PumpTemperatureSensor(),
            'hydro_support_temp_sensor': PumpTemperatureSensor(),
            'pressure_sensor': PumpPressureSensor(),
            'motor_current_sensor': PumpMotorCurrentSensor(),
            'flow_sensor': PumpFlowSensor(),
            'shaft_speed_sensor': PumpShaftSpeedSensor()
            }

        #Трубы
        self.pipe_sensors = {}
        for key in self.pipes.keys():
            self.pipe_sensors[key] = {
                'pressure_sensor': PipePressureSensor(),
                'temperature_sensor': PipeTemperatureSensor()
            }

        #Маслосистема
        self.oil_sensors = {}
        for i in range(len(self.oil_systems)):
            self.oil_sensors[i] = {
                'flow_sensor': OilFlowSensor(),
                'temperature_sensor': OilTemperatureSensor(),
            }

        #Маслобак
        self.tank_sensors = {}
        for i, oil_system in enumerate(self.oil_systems):
            tank = oil_system.tank
            self.tank_sensors[i] = {
                'level_sensor': TankLevelSensor(volume_max=tank.volume_max),
                'density_sensor': TankDensitySensor(),
                'temperature_sensor': TankTemperatureSensor(),
                'flow_sensor': TankFlowRateSensor() 
            }        

        #Переменные для хранения значений с датчиков
        #Задвижки
        self.valve_sensor_values = {}
        for key in self.valves.keys():
            self.valve_sensor_values[key] = {
                'temperature_current_mA': 0.0,
                'pressure_current_mA': 0.0,
                'position_current_mA': 0.0
            }

        #Насосы
        self.pump_sensor_values = {}
        for pump_id in range(len(self.pumps)):
            self.pump_sensor_values[pump_id] = {
            'bearing_work_temp_current_mA': 0.0,
            'bearing_field_temp_current_mA': 0.0,
            'motor_bearing_work_temp_current_mA': 0.0,
            'motor_bearing_field_temp_current_mA': 0.0,
            'hydro_support_temp_current_mA': 0.0,
            'pressure_current_mA': 0.0,
            'motor_current_current_mA': 0.0,
            'flow_current_mA': 0.0,
            'shaft_speed_current_mA': 0.0
            }

        #Трубы
        self.pipe_sensor_values = {}
        for key in self.pipes.keys():
            self.pipe_sensor_values[key] = {
                'pressure_current_mA': 0.0,
                'temperature_current_mA': 0.0
            }

        #Маслосистема
        self.oil_sensor_values = {}
        for i in range(len(self.oil_systems)):
            self.oil_sensor_values[i] = {
                'flow_current_mA': 0.0,
                'temperature_current_mA': 0.0,
            }

        #Маслобак
        self.tank_sensor_values = {}
        for i in range(len(self.oil_systems)):
            self.tank_sensor_values[i] = {
                'level_current_mA': 0.0,
                'density_current_mA': 0.0,
                'temperature_current_mA': 0.0,
                'flow_current_mA': 0.0
            }

        # Таймер для обновления состояния
        self.last_update_time = time.time()


    def  update_system(self):
        """
        Основной метод обновления состояния всей системы.
        Выполняется циклически для симуляции работы БКНС.

        """

        #Для большей плавности и корректной работы модели
        current_time = time.time()  # Получаем текущее время в секундах с начала эпохи
        dt = current_time - self.last_update_time  # Вычисляем разницу с предыдущим обновлением
        self.last_update_time = current_time  # Обновляем время последнего обновления

        # Обновляем состояние всех задвижек
        for valve in self.valves.values():
            valve.update(dt)



        # Обновляем общую входную трубу (рассчитываем давление и температуру)
        self.pipes['main_inlet'].compute_output_pressure(
            p_in=self.inlet_pressure,  # Входное давление в систему
            m_dot_A=self.m_dot_A,      # Массовый расход в порту A
            m_dot_B=self.m_dot_B,      # Массовый расход в порту B
            mu=self.mu,                # Вязкость жидкости
            rho=self.rho,              # Плотность жидкости
            temperature=self.inlet_temperature  # Температура жидкости на входе
        )

        #Пока что так, дальше надо будет корректировать !
        inlet_signals = [True, True, True, True]
        outlet_signals = [True, True, True, True]
        inflow_rates = [1.0, 1.0, 1.0, 1.0]
        outflow_rates = [1.0, 1.0, 1.0, 1.0]


        # Обновляем маслосистемы с учётом команд запуска/остановки маслонасосов
        # Важно: маслосистема запускается только по команде, без автоматического запуска
        for pump_id, oil_system in enumerate(self.oil_systems):
            cmd = self.oil_pump_commands[pump_id]
            oil_system.update(
                command_main_run=cmd['start'],
                command_main_stop=cmd['stop'],
                command_reserve_run=False,  # Резервный маслонасос всегда выключен
                command_reserve_stop=True,
                dt=dt,
                inlet_signals=inlet_signals, 
                outlet_signals=outlet_signals, 
                inflow_rates=inflow_rates,
                outflow_rates=outflow_rates
            )

        # Обновляем насосы, трубы и задвижки
        for pump_id, pump in enumerate(self.pumps):

            # Параметры для труб и задвижек данного насоса
            in_valve = self.valves[f'in_{pump_id}']
            out_valve = self.valves[f'out_{pump_id}']
            in_pipe = self.pipes[f'in_{pump_id}']
            out_pipe = self.pipes[f'out_{pump_id}']
                
            # Обновляем входную трубу насоса (от общей входной трубы)
            in_pipe.compute_output_pressure(
                p_in=self.pipes['main_inlet'].p_out,
                m_dot_A=self.m_dot_A,
                m_dot_B=self.m_dot_B,
                mu=self.mu,
                rho=self.rho,
                temperature=self.pipes['main_inlet'].T
            )
                
            # Обновляем насос
            in_cv = in_valve.get_opening_coefficient()
            p_after_in_valve = in_pipe.p_out * in_cv 
            out_cv = out_valve.get_opening_coefficient()
            p_before_out_pipe = pump.p_out * out_cv
            valve_flow_factor = min(in_cv, out_cv)
            target_omega = pump.reference_shaft_speed if pump.na_on else 0.0
            q = pump.nominal_capacity * 0.8 * valve_flow_factor
            # Получаем состояния задвижек (True - открыта, False - закрыта)
            inlet_open = in_valve.state == "open" or  in_valve.state == "moving" or in_valve.state == "stopped"  # можно считать двигающуюся задвижку частично открытой
            outlet_open = out_valve.state == "open" or out_valve.state == "moving"
            pump.step(target_omega, q, self.rho, inlet_open, outlet_open)
                
            # Обновляем давление и температуру в выходной трубе
            out_pipe.compute_output_pressure(
                p_in=p_before_out_pipe,
                m_dot_A=self.m_dot_A,
                m_dot_B=self.m_dot_B,
                mu=self.mu,
                rho=self.rho,
                temperature=self.inlet_temperature
            )
                
            # Обновляем состояние задвижек
            in_valve.update_conditions(
                pressure=in_pipe.p_out,
                temperature=in_pipe.T
            )
            out_valve.update_conditions(
                pressure=out_pipe.p_out,
                temperature=out_pipe.T
            )
            
        # Обновляем общую выходную трубу (объединяем выходы насосов)
        # Для упрощения считаем, что давление в общей трубе - среднее от выходных труб
        avg_pressure = (self.pipes['out_0'].p_out + self.pipes['out_1'].p_out) / 2
        avg_temp = (self.pipes['out_0'].T + self.pipes['out_1'].T) / 2
        
        self.pipes['main_outlet'].compute_output_pressure(
            p_in=avg_pressure,
            m_dot_A=self.m_dot_A,
            m_dot_B=self.m_dot_B,
            mu=self.mu,
            rho=self.rho,
            temperature=avg_temp
        )
        
        #Обновление данных на датчиках
        #Задвижки
        for key, sensors in self.valve_sensors.items():
            valve = self.valves[key]

            temp_current = sensors['temperature_sensor'].measure_current(valve.temperature)
            pressure_current = sensors['pressure_sensor'].measure_current(valve.pressure)
            position_current = sensors['position_sensor'].measure_current(valve.current_position)

            self.valve_sensor_values[key]['temperature_current_mA'] = temp_current
            self.valve_sensor_values[key]['pressure_current_mA'] = pressure_current
            self.valve_sensor_values[key]['position_current_mA'] = position_current

        #Насосы
        for pump_id, sensors in self.pump_sensors.items():
            pump = self.pumps[pump_id]

            bearing_work_temp_current = sensors['bearing_work_temp_sensor'].measure_current(pump.NA_AI_T_1_n)
            bearing_field_temp_current = sensors['bearing_field_temp_sensor'].measure_current(pump.NA_AI_T_2_n)
            motor_bearing_work_temp_current = sensors['motor_bearing_work_temp_sensor'].measure_current(pump.NA_AI_T_3_n)
            motor_bearing_field_temp_current = sensors['motor_bearing_field_temp_sensor'].measure_current(pump.NA_AI_T_4_n)
            hydro_support_temp_current = sensors['hydro_support_temp_sensor'].measure_current(pump.NA_AI_T_5_n)
            pressure_current = sensors['pressure_sensor'].measure_current(pump.p_out)
            motor_current_current = sensors['motor_current_sensor'].measure_current(pump.current_motor_i)
            flow_current = sensors['flow_sensor'].measure_current(pump.NA_AI_Qmom_n)
            shaft_speed_current = sensors['shaft_speed_sensor'].measure_current(pump.current_omega)

            self.pump_sensor_values[pump_id]['bearing_work_temp_current_mA'] = bearing_work_temp_current
            self.pump_sensor_values[pump_id]['bearing_field_temp_current_mA'] = bearing_field_temp_current
            self.pump_sensor_values[pump_id]['motor_bearing_work_temp_current_mA'] = motor_bearing_work_temp_current
            self.pump_sensor_values[pump_id]['motor_bearing_field_temp_current_mA'] = motor_bearing_field_temp_current
            self.pump_sensor_values[pump_id]['hydro_support_temp_current_mA'] = hydro_support_temp_current

            self.pump_sensor_values[pump_id]['pressure_current_mA'] = pressure_current
            self.pump_sensor_values[pump_id]['motor_current_current_mA'] = motor_current_current
            self.pump_sensor_values[pump_id]['flow_current_mA'] = flow_current
            self.pump_sensor_values[pump_id]['shaft_speed_current_mA'] = shaft_speed_current


        #Трубы
        for key, sensors in self.pipe_sensors.items():
            pipe = self.pipes[key]

            pressure_current = sensors['pressure_sensor'].measure_current(pipe.p_out)
            temperature_current = sensors['temperature_sensor'].measure_current(pipe.T)

            self.pipe_sensor_values[key]['pressure_current_mA'] = pressure_current
            self.pipe_sensor_values[key]['temperature_current_mA'] = temperature_current           

        #Маслосистема
        for i, oil_system in enumerate(self.oil_systems):
            sensors = self.oil_sensors[i]

            flow_current = sensors['flow_sensor'].measure_current(oil_system.flow_rate)
            temperature_current = sensors['temperature_sensor'].measure_current(oil_system.temperature)
            
            self.oil_sensor_values[i]['flow_current_mA'] = flow_current
            self.oil_sensor_values[i]['temperature_current_mA'] = temperature_current


        #Маслобак
        for i, oil_system in enumerate(self.oil_systems):
            tank = oil_system.tank
            sensors = self.tank_sensors[i]

            level_current = sensors['level_sensor'].measure_current(tank.level_radar)
            density_current = sensors['density_sensor'].measure_current(tank.density_meter)
            temperature_current = sensors['temperature_sensor'].measure_current(tank.temperature_sensor)
            flow_current = sensors['flow_sensor'].measure_current(tank.flow_meter)

            self.tank_sensor_values[i]['level_current_mA'] = level_current
            self.tank_sensor_values[i]['density_current_mA'] = density_current
            self.tank_sensor_values[i]['temperature_current_mA'] = temperature_current
            self.tank_sensor_values[i]['flow_current_mA'] = flow_current

    def control_pump(self, pump_id: int, start: bool):
        """
        Управление насосом (включение/выключение)

        """
        if pump_id not in [0, 1]:
            raise ValueError("Invalid pump_id. Must be 0 or 1.")
            
        if start:
            
            self.pumps[pump_id].na_start = True
            self.pumps[pump_id].na_stop = False

        else:
            self.pumps[pump_id].na_start = False
            self.pumps[pump_id].na_stop = True
    
    def control_oil_pump(self, pump_id: int, start: bool):
        """
        Управление маслонасосом, отдельное от основного насоса.
        start=True — запустить маслонасос, False — остановить.
        """
        if pump_id not in [0, 1]:
            raise ValueError("Invalid pump_id. Must be 0 or 1.")

        self.oil_pump_commands[pump_id]['start'] = start
        self.oil_pump_commands[pump_id]['stop'] = not start

    def control_valve(self, valve_key: str, command_or_bool):
        """
        Управление задвижкой
        """
        if valve_key not in self.valves:
            raise ValueError(f"Invalid valve lock key: {valve_key}")
        valve = self.valves[valve_key]
        if isinstance(command_or_bool, bool):
            command = "open" if command_or_bool else "close"
        elif isinstance(command_or_bool, str):
            if command_or_bool not in ("open", "close", "stop"):
                raise ValueError(f"Invalid valve control command: {command_or_bool}")
            command = command_or_bool
        else:
            raise TypeError("command_or_bool must be of type str or bool")

        valve.control(command)
    
    
    
    def get_status(self) -> Dict:
        """
        Возвращает состояние системы в структуре, ожидаемой OPC и flatten_status_for_opc().
        """
        status = {}

        for pump_id, pump in enumerate(self.pumps):
            status[f"pump_{pump_id}"] = {
                "na_on": pump.na_on,
                "na_off": pump.na_off,
                "motor_current": pump.current_motor_i,
                "pressure_in": self.pipes[f"in_{pump_id}"].p_out,
                "pressure_out": pump.p_out,
                "flow_rate": pump.NA_AI_Qmom_n,
                "temp_bearing_1": pump.NA_AI_T_2_n,
                "temp_bearing_2": pump.NA_AI_T_1_n,
                "temp_motor_1": pump.NA_AI_T_3_n,
                "temp_motor_2": pump.NA_AI_T_4_n,
                "temp_water": pump.NA_AI_T_5_n,
                "cover_open": True
            }

        for i, oil_system in enumerate(self.oil_systems):
            status[f"oil_system_{i}"] = {
                "oil_sys_running": oil_system.running,
                "oil_sys_pressure_ok": oil_system.pressure_ok,
                "oil_pressure": oil_system.pressure,
                "temperature": oil_system.temperature,
            }

        for valve_key, valve in self.valves.items():
            if valve_key.startswith("out_"):
                idx = valve_key[-1]
                status[f"valve_out_{idx}"] = {
                    "valve_open": valve.state == "open",
                    "valve_closed": valve.state == "closed"
                }

        return status


    def _format_sensors_table(self, status: Dict) -> str:
        lines = []
        lines.append("=== Датчики (ток 4-20 мА) ===\n")

        # Задвижки
        lines.append(f"{'Valve':<8} {'Temp':>6} {'Pres':>6} {'Pos':>6}")
        for key, val in status['valve_sensors'].items():
            lines.append(f"{key:<8} "
                        f"{val['temperature_current_mA']:6.2f} "
                        f"{val['pressure_current_mA']:6.2f} "
                        f"{val['position_current_mA']:6.2f}")
        lines.append("")

        # Насосы
        lines.append(f"{'PumpID':<6} {'T1':>6} {'T2':>6} {'T3':>6} {'T4':>6} {'Hydro':>6} {'Pres':>6} {'MotorI':>7} {'Flow':>6} {'Speed':>6}")
        for pump_id, val in status['pump_sensors'].items():
            lines.append(f"{pump_id:<6} "
                        f"{val['bearing_work_temp_current_mA']:6.2f} "
                        f"{val['bearing_field_temp_current_mA']:6.2f} "
                        f"{val['motor_bearing_work_temp_current_mA']:6.2f} "
                        f"{val['motor_bearing_field_temp_current_mA']:6.2f} "
                        f"{val['hydro_support_temp_current_mA']:6.2f} "
                        f"{val['pressure_current_mA']:6.2f} "
                        f"{val['motor_current_current_mA']:7.2f} "
                        f"{val['flow_current_mA']:6.2f} "
                        f"{val['shaft_speed_current_mA']:6.2f}")
        lines.append("")

        # Трубы
        lines.append(f"{'Pipe':<10} {'Pres':>6} {'Temp':>6}")
        for key, val in status['pipe_sensors'].items():
            lines.append(f"{key:<10} "
                        f"{val['pressure_current_mA']:6.2f} "
                        f"{val['temperature_current_mA']:6.2f}")
        lines.append("")

        # Маслосистемы
        lines.append(f"{'OilSys':<6} {'Flow':>6} {'Temp':>6}")
        for i, val in status['oil_sensors'].items():
            lines.append(f"{i:<6} "
                        f"{val['flow_current_mA']:6.2f} "
                        f"{val['temperature_current_mA']:6.2f}")
        lines.append("")

        # Маслобаки
        lines.append(f"{'Tank':<6} {'Level':>6} {'Density':>8} {'Temp':>6} {'Flow':>6}")
        for i, val in status['tank_sensors'].items():
            lines.append(f"{i:<6} "
                        f"{val['level_current_mA']:6.2f} "
                        f"{val['density_current_mA']:8.2f} "
                        f"{val['temperature_current_mA']:6.2f} "
                        f"{val['flow_current_mA']:6.2f}")
        lines.append("")

        return "\n".join(lines)




    def __str__(self):
        """
        Возвращает текстовое представление состояния системы.

        """
        status = self.get_status()
        output = []
        
        # Общая информация
        output.append("=== Состояние БКНС ===")
        output.append(f"Входные параметры: Давление={status['main_inlet']['pressure']:.4f} МПа")
        output.append(f"Выходные параметры: Давление={status['main_outlet']['pressure']:.4f} МПа\n")

        # Детальная информация по каждому насосу
        for pump_name, pump_data in status['pumps'].items():
            output.append(
                f"Насос {pump_name} (ID {pump_data['pump_id']}):\n"
                f"  Режим работы: {pump_data['operation_mode']}\n"
                f"  Старт: {pump_data['start']}, Стоп: {pump_data['stop']}, "
                f"Вкл: {pump_data['on']}, Выкл: {pump_data['off']}\n"
                f"  Ток двигателя: {pump_data['motor_i']:.2f} А\n"
                f"  Давление вход: {pump_data['pressure_in']:.3f} МПа, "
                f"выход: {pump_data['pressure_out']:.3f} МПа\n"
                f"  Температуры:\n"
                f"    Подшипник (раб.): {pump_data['bearing_work_temp']:.1f}°C\n"
                f"    Подшипник (поле): {pump_data['bearing_field_temp']:.1f}°C\n"
                f"    Мотор (раб.): {pump_data['motor_bearing_work_temp']:.1f}°C\n"
                f"    Мотор (поле): {pump_data['motor_bearing_field_temp']:.1f}°C\n"
                f"    Гидроподшипник: {pump_data['hydro_support_temp']:.1f}°C\n"
                f"  Маслосистема: {'запущена' if pump_data['oil_system_running'] else 'остановлена'}, "
                f"Давление: {pump_data['oil_pressure']:.2f} бар ,"
                f"Температура масла: {pump_data['oil_temperature']:.1f}°C\n"
                f"  Команды маслонасоса: старт={pump_data['oil_pump_start_cmd']}, стоп={pump_data['oil_pump_stop_cmd']}\n"
                f"  Входная задвижка: состояние: "
                f"{'открыта' if pump_data['in_valve_open'] else 'закрыта' if pump_data['in_valve_closed'] else 'в движении'}, "
                f"команды: открыть={pump_data['in_valve_open_cmd']}, закрыть={pump_data['in_valve_close_cmd']}\n"
                f"  Выходная задвижка: состояние: "
                f"{'открыта' if pump_data['out_valve_open'] else 'закрыта' if pump_data['out_valve_closed'] else 'в движении'}, "
                f"команды: открыть={pump_data['out_valve_open_cmd']}, закрыть={pump_data['out_valve_close_cmd']}\n"
                f"  Расход: {pump_data['flow_rate']:.3f} м³/с\n"
            )
        
        output.append("")
        # Добавляем таблицу с датчиками
        output.append(self._format_sensors_table(status))
        return "\n".join(output)

import time
import sys

#log_file = open("Пример.log", "w", encoding="utf-8")
#sys.stdout = log_file
if __name__ == "__main__":

    # Инициализация системы БКНС с параметрами по умолчанию:
    bkns = BKNS()
    
    # Открываем все задвижки насосов NA4 и NA2
    bkns.control_valve('in_0', True)
    bkns.control_valve('out_0', True)
    bkns.control_valve('in_1', True)
    bkns.control_valve('out_1', True)

    # Запускаем маслонасосы для обоих насосов
    bkns.control_oil_pump(0, True)
    bkns.control_oil_pump(1, True)

    print("=== Начало симуляции БКНС ===")
    try:
        for i in range(45):  # Увеличиваем длительность для демонстрации новых сценариев
            bkns.update_system()
            print(f"\n=== Состояние БКНС через {i} секунд ===")
            print(bkns)

            # --- Режимы работы одного насоса (NA4) ---
            if i == 5:
                print("\n>>> Запускаем насос NA4")
                bkns.control_pump(0, True)
            if i == 10:
                print("\n>>> Закрываем выходную задвижку NA4")
                bkns.control_valve('out_0', False)
            if i == 14:
                print("\n>>> Повторная попытка закрыть выходную задвижку NA4")
                bkns.control_valve('out_0', False)
            if i == 16:
                print("\n>>> Открываем выходную задвижку NA4")
                bkns.control_valve('out_0', True)
            if i == 18:
                print("\n>>> Останавливаем насос NA4")
                bkns.control_pump(0, False)
            if i == 20:
                print("\n>>> Останавливаем маслонасос NA4")
                bkns.control_oil_pump(0, False)

            # --- Работа двух насосов одновременно ---
            if i == 22:
                print("\n>>> Запускаем насос NA4 и насос NA2 одновременно")
                bkns.control_pump(0, True)
                bkns.control_pump(1, True)
                bkns.control_oil_pump(0, True)
                bkns.control_oil_pump(1, True)
            if i == 25:
                print("\n>>> Закрываем входную задвижку NA2 (симуляция 'закрыта входная')")
                bkns.control_valve('in_1', False)
            if i == 28:
                print("\n>>> Открываем входную задвижку NA2")
                bkns.control_valve('in_1', True)

            # --- Работа насоса без масла (маслосистема выключена) ---
            if i == 30:
                print("\n>>> Останавливаем маслонасос NA2 (симуляция работы насоса без масла)")
                bkns.control_oil_pump(1, False)
            if i == 32:
                print("\n>>> Останавливаем насос NA2")
                bkns.control_pump(1, False)
            if i == 35:
                print("\n>>> Запускаем насос NA2 без маслонасоса (опасный режим!)")
                bkns.control_pump(1, True)
            if i == 40:
                print("\n>>> Запускаем маслонасос NA2")
                bkns.control_oil_pump(1, True)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nСимуляция остановлена пользователем")
#log_file.close()