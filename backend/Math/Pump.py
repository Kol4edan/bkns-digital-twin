import numpy as np
import time
from .OilSystem import OilSystem
from .Pipe import PipeModel


class CentrifugalPump:
    def __init__(self, bond_oil_system, name):
        # Pump parameters
        self.name = name
        self.bond_oil_system = bond_oil_system
        self.p_in_outside = 1.7
        self.p_in = 1.7  # МПа (входное давление)
        self.p_out = 1.7
        self.nominal_capacity = 45.0  # m^3/s
        self.nominal_head = 40.0  # m
        self.nominal_brake_power = 0.85  # kW
        self.max_head_zero_capacity = 60.0  # m
        self.max_capacity_zero_head = 80.0  # m^3/s
        self.reference_shaft_speed = 1770.0  # rad/s
        self.min_shaft_speed_threshold = 1e-2
        self.impeller_diameter_scale = 1.0

        # Motor parameters
        self.nominal_current = 10.0  # A (номинальный ток двигателя)
        self.current_reduction_step = 0.1  # шаг уменьшения тока при остановке
 
        # Temperature parameters
        self.ambient_temp = 25.0  # °C (температура окружающей среды)
        self.max_operating_temp = 40.0  # °C (максимальная рабочая температура)
        self.temp_rise_rate = 0.25  # скорость роста температуры °C/сек
        self.temp_cooling_rate = 0.32  # скорость охлаждения °C/сек
        self.temp_dry_run_rise_rate = 0.25  # скорость роста температуры при работе "всухую"
        self.temp_closed_valve_rise_rate = 0.18  # скорость роста температуры при закрытой задвижке

        # Fluctuation parameters
        self.temp_fluctuation = 0.3  # Колебания температуры (±0.3°C)
        self.current_fluctuation = 0.1  # Колебания тока (±0.1A)
        self.pressure_fluctuation = 0.01  # Колебания давления (±0.01 МПа)
        self.flow_fluctuation = 0.05  # Колебания расхода (±0.05 м³/с)

        # Current state
        self.current_omega = 0.0  # Начинаем с 0 скорости!
        self.current_motor_i = 0.0
        self.na_on = False
        self.na_off = True
        self.na_start = False
        self.na_stop = False

        # Режимы работы насоса
        self.OPERATION_MODE_NORMAL = 0  # Штатный режим
        self.OPERATION_MODE_INLET_CLOSED = 1  # Закрыта входная задвижка
        self.OPERATION_MODE_OUTLET_CLOSED = 2  # Закрыта выходная задвижка
        self.OPERATION_MODE_BOTH_CLOSED = 3  # ИЗМЕНЕНО: Обе задвижки закрыты
        self.operation_mode = self.OPERATION_MODE_NORMAL
        self.mode_change_time = 0.0  # Время последней смены режима

        # Temperatures
        self.NA_AI_T_1_n = self.ambient_temp  # Температура рабочего подшипника насоса
        self.NA_AI_T_2_n = self.ambient_temp  # Температура полевого подшипника насоса
        self.NA_AI_T_3_n = self.ambient_temp  # Температура рабочего подшипника двигателя
        self.NA_AI_T_4_n = self.ambient_temp  # Температура полевого подшипника двигателя
        self.NA_AI_T_5_n = self.ambient_temp  # Температура воды в гидропяте

        # Flow
        self.NA_AI_Qmom_n = 0.0

        # Constants
        self.g = 9.81  # gravitational acceleration [m/s^2]

        # Simulation parameters
        self.time_constant = 5.0  # постоянная времени для экспоненциального роста
        self.simulation_time = 0.0

        # Derived parameters
        self.a, self.b, self.c = self._calculate_head_curve_coeffs()

        # For exponential ramp calculation
        self.start_omega = 0.0
        self.start_time = 0.0

    def _calculate_head_curve_coeffs(self):
        """Коэффициенты для определения работы насоса"""
        q1, h1 = 0, self.max_head_zero_capacity
        q2, h2 = self.nominal_capacity, self.nominal_head
        q3, h3 = self.max_capacity_zero_head, 0

        A = np.array([
            [q1 ** 2, q1, 1],
            [q2 ** 2, q2, 1],
            [q3 ** 2, q3, 1]
        ])
        B = np.array([h1, h2, h3])

        return np.linalg.solve(A, B)

    def reset_ramp(self):
        """Ресет при отключении"""
        self.start_omega = self.current_omega
        self.start_time = self.simulation_time

    def calculate_omega(self, target_omega):
        """Симулируем плавное повышение угловой скорости"""
        t = self.simulation_time - self.start_time
        if t < 0:
            t = 0

        if self.na_on:  # Скорость растет только при включенном насосе
            self.current_omega = target_omega - (target_omega - self.start_omega) * np.exp(-t / self.time_constant)
        else:  # Если насос выключен, скорость падает до 0
            self.current_omega = max(0, self.start_omega * np.exp(-t / (self.time_constant / 2)))

        return self.current_omega

    def apply_fluctuation(self, value, target_max, fluctuation_range):
        """Добавляет случайные колебания, если значение близко к максимуму."""
        if value >= target_max * 0.9:
            noise = np.random.uniform(-fluctuation_range, fluctuation_range)
            return value + noise
        return value

    def calculate_head(self, q, omega=None):
        """Вычисляем напор"""
        omega = omega if omega is not None else self.current_omega
        if omega < self.min_shaft_speed_threshold:
            return 0.0

        q_ref = q * (self.reference_shaft_speed / omega) * (1.0 / self.impeller_diameter_scale) ** 3
        H_ref = self.a * q_ref ** 2 + self.b * q_ref + self.c
        return H_ref * (omega / self.reference_shaft_speed) ** 2 * (self.impeller_diameter_scale) ** 2

    def calculate_pressure_gain(self, q, rho, omega=None):
        """Вычисляем прирост давления"""
        H = self.calculate_head(q, omega)
        delta_p = rho * self.g * H

        if delta_p >= 0.8 * rho * self.g * self.max_head_zero_capacity:
            delta_p += np.random.uniform(-self.pressure_fluctuation * 1e6, self.pressure_fluctuation * 1e6)

        return delta_p

    def calculate_current(self):
        """Находим ток насоса"""
        if not self.na_on or self.current_omega < self.min_shaft_speed_threshold:
            return 0.0

        # Ток зависит от режима работы
        if self.operation_mode == self.OPERATION_MODE_NORMAL:
            current = self.nominal_current * (self.current_omega / self.reference_shaft_speed)
        elif self.operation_mode == self.OPERATION_MODE_INLET_CLOSED:
            # При закрытой входной задвижке ток сначала падает, потом растет
            time_in_mode = self.simulation_time - self.mode_change_time
            if time_in_mode < 5.0:  # Первые 5 секунд
                current = self.nominal_current * (self.current_omega / self.reference_shaft_speed) * 0.7
            else:
                current = self.nominal_current * (self.current_omega / self.reference_shaft_speed) * 1.3
        #ИЗМЕНЕНО
        elif self.operation_mode == self.OPERATION_MODE_OUTLET_CLOSED:  
            # При закрытой выходной задвижке ток увеличивается
            current = self.nominal_current * (self.current_omega / self.reference_shaft_speed) * 1.5
        else: #Режим с обеими закрытыми
                        current = self.nominal_current * (self.current_omega / self.reference_shaft_speed) * 0.5
        
        if current >= self.nominal_current * 0.8:
            current += np.random.uniform(-self.current_fluctuation, self.current_fluctuation)

        return max(0, current)

    def update_temperatures(self):
        """Изменяем температуру на выходе насоса в зависимости от режима работы"""
        if not self.na_on or self.current_omega < self.min_shaft_speed_threshold:
            delta_temp = self.temp_cooling_rate
            self.NA_AI_T_1_n = max(self.NA_AI_T_1_n - delta_temp, self.ambient_temp)
            self.NA_AI_T_2_n = max(self.NA_AI_T_2_n - delta_temp, self.ambient_temp)
            self.NA_AI_T_3_n = max(self.NA_AI_T_3_n - delta_temp * 1.2, self.ambient_temp)
            self.NA_AI_T_4_n = max(self.NA_AI_T_4_n - delta_temp, self.ambient_temp)
            self.NA_AI_T_5_n = max(self.NA_AI_T_5_n - delta_temp * 0.8, self.ambient_temp)
            return

        # Определяем скорость роста температуры в зависимости от режима
        if self.operation_mode == self.OPERATION_MODE_NORMAL:
            temp_factor = (self.current_motor_i / self.nominal_current) * (
                        self.current_omega / self.reference_shaft_speed)
            delta_temp = self.temp_rise_rate * temp_factor
        elif self.operation_mode == self.OPERATION_MODE_INLET_CLOSED:
            # При закрытой входной задвижке температура растет быстрее
            time_in_mode = self.simulation_time - self.mode_change_time
            delta_temp = self.temp_dry_run_rise_rate * (1 + time_in_mode / 20)  # Температура растет со временем
        #ИЗМЕНЕНО
        #При закрытой выходной задвижке
        elif self.operation_mode == self.OPERATION_MODE_OUTLET_CLOSED:
            delta_temp = self.temp_closed_valve_rise_rate
        else:  #обе задвижки закрыты
            delta_temp = self.temp_closed_valve_rise_rate * 1.5

        # Применяем изменение температуры
        self.NA_AI_T_1_n = min(self.NA_AI_T_1_n + delta_temp * 1.3 + int(not(self.bond_oil_system.pressure_ok)) * 3, self.max_operating_temp)
        self.NA_AI_T_2_n = min(self.NA_AI_T_2_n + delta_temp + int(not(self.bond_oil_system.pressure_ok)) * 3, self.max_operating_temp)
        self.NA_AI_T_3_n = min(self.NA_AI_T_3_n + delta_temp * 1.1 + int(not(self.bond_oil_system.pressure_ok)) * 3, self.max_operating_temp)
        self.NA_AI_T_4_n = min(self.NA_AI_T_4_n + delta_temp * 0.9 + int(not(self.bond_oil_system.pressure_ok)) * 3, self.max_operating_temp)
        self.NA_AI_T_5_n = min(self.NA_AI_T_5_n + delta_temp * 0.7 + int(not(self.bond_oil_system.pressure_ok)) * 3, self.max_operating_temp)

        # Добавляем дребезг
        self.NA_AI_T_1_n = self.apply_fluctuation(self.NA_AI_T_1_n, self.max_operating_temp, self.temp_fluctuation)
        self.NA_AI_T_2_n = self.apply_fluctuation(self.NA_AI_T_2_n, self.max_operating_temp, self.temp_fluctuation)
        self.NA_AI_T_3_n = self.apply_fluctuation(self.NA_AI_T_3_n, self.max_operating_temp, self.temp_fluctuation)
        self.NA_AI_T_4_n = self.apply_fluctuation(self.NA_AI_T_4_n, self.max_operating_temp, self.temp_fluctuation)
        self.NA_AI_T_5_n = self.apply_fluctuation(self.NA_AI_T_5_n, self.max_operating_temp, self.temp_fluctuation)

    def detect_operation_mode(self, q, p_in, p_out):
        """Определяем текущий режим работы насоса"""
        # Пороговые значения для определения режима
        low_flow_threshold = 0.1  # м³/с
        low_inlet_pressure_threshold = 0.2  # МПа
        high_outlet_pressure_threshold = self.max_head_zero_capacity * 1000 * 9.81 / 1e6  # Макс. давление в МПа

        #ИЗМЕНЕНО
        if q < low_flow_threshold and p_in < low_inlet_pressure_threshold and p_out > high_outlet_pressure_threshold * 0.9:
            new_mode = self.OPERATION_MODE_BOTH_CLOSED
        elif q < low_flow_threshold and p_in < low_inlet_pressure_threshold:
            new_mode = self.OPERATION_MODE_INLET_CLOSED
        elif q < low_flow_threshold and p_out > high_outlet_pressure_threshold * 0.9:
            new_mode = self.OPERATION_MODE_OUTLET_CLOSED
        else:
            new_mode = self.OPERATION_MODE_NORMAL

        # Если режим изменился, запоминаем время изменения
        if new_mode != self.operation_mode:
            self.operation_mode = new_mode
            self.mode_change_time = self.simulation_time

    def control_pump(self):
        """Работа насоса в связи с командами, подающимися на него"""
        if self.na_start and not self.na_on:
            self.na_on = True
            self.na_off = False
            self.na_start = False
            self.reset_ramp()

        if self.na_stop and self.na_on:
            self.na_on = False
            self.na_stop = False
            self.reset_ramp()

        if not self.na_on and self.current_motor_i > 0:
            self.current_motor_i = max(0, self.current_motor_i - self.current_reduction_step)
            self.p_out = max(self.p_in, self.p_out - 0.01)

    def step(self, target_omega, q, rho, inlet, outlet):
        """Шаг работы насоса"""
        self.control_pump()
        self.calculate_omega(target_omega)

        # Определяем текущий режим работы
        if inlet and outlet:
            self.operation_mode = self.OPERATION_MODE_NORMAL
        elif not(inlet) and outlet:
            self.operation_mode = self.OPERATION_MODE_INLET_CLOSED
        elif inlet and not(outlet):
            self.operation_mode = self.OPERATION_MODE_OUTLET_CLOSED
        else:
            self.operation_mode = self.OPERATION_MODE_BOTH_CLOSED

        if self.bond_oil_system.pressure_ok:
            self.max_operating_temp = 40
        else:
            self.max_operating_temp = 60

        if self.na_on:
            # Поведение насоса зависит от режима работы
            if self.operation_mode == self.OPERATION_MODE_NORMAL:
                self.p_in = self.p_in_outside
                delta_p = self.calculate_pressure_gain(q, rho)
                self.p_out = self.p_in + (delta_p / 1e6)
                self.NA_AI_Qmom_n = q * (self.current_omega / target_omega)

            elif self.operation_mode == self.OPERATION_MODE_INLET_CLOSED:
                # При закрытой входной задвижке
                self.p_in = max(0, self.p_in - 0.5)  # Давление на входе падает
                self.p_out = max(0, self.p_out - 0.5)  # Давление на выходе тоже падает
                self.NA_AI_Qmom_n = 0.0  # Расход нулевой

            elif self.operation_mode == self.OPERATION_MODE_OUTLET_CLOSED:
                # При закрытой выходной задвижке
                delta_p = self.calculate_pressure_gain(0, rho)  # Расход нулевой
                self.p_in = self.p_in_outside
                self.p_out = self.p_in + (delta_p / 1e6)  # Давление на выходе растет
                self.NA_AI_Qmom_n = 0.0  # Расход нулевой

            elif self.operation_mode == self.OPERATION_MODE_BOTH_CLOSED:  # ИЗМЕНЕНО: обработка нового режима
                self.p_in = max(0, self.p_in - 0.5)
                self.p_out = max(0, self.p_out - 0.5)
                self.NA_AI_Qmom_n = 0.0

            # Добавляем флуктуации расхода в штатном режиме
            if self.operation_mode == self.OPERATION_MODE_NORMAL and self.NA_AI_Qmom_n >= 0.8 * self.nominal_capacity:
                self.NA_AI_Qmom_n += np.random.uniform(-self.flow_fluctuation, self.flow_fluctuation)

            self.current_motor_i = self.calculate_current()
        else:
            self.NA_AI_Qmom_n = 0.0

        self.update_temperatures()
        self.simulation_time += 1.0

    def get_operation_mode_name(self):
        """Возвращает текстовое название текущего режима работы"""
        modes = {
            self.OPERATION_MODE_NORMAL: "Штатный режим",
            self.OPERATION_MODE_INLET_CLOSED: "Закрыта входная задвижка",
            self.OPERATION_MODE_OUTLET_CLOSED: "Закрыта выходная задвижка",
            self.OPERATION_MODE_BOTH_CLOSED: "Обe задвижки закрыты"  # ИЗМЕНЕНО
        }
        return modes.get(self.operation_mode, "Неизвестный режим")

    def get_status(self):
        """Чисто чтобы смотреть"""
        mode = self.get_operation_mode_name()
        return (f"{self.simulation_time:8.1f} | {self.current_omega:7.1f} | {self.current_motor_i:4.1f}A | "
                f"{self.p_out:7.10f}MPa | {self.NA_AI_T_2_n:.1f}°C {self.NA_AI_T_3_n:.1f}°C "
                f"{self.NA_AI_T_4_n:.1f}°C {self.NA_AI_T_5_n:.1f}°C | {self.NA_AI_Qmom_n:.2f}m³/s | {mode}")




if __name__ == "__main__":
    oil_system = OilSystem(0)
    pump = CentrifugalPump(oil_system,'NA4')
    pipe = PipeModel()

    m_dot_A = 0.5
    m_dot_B = 0.5
    mu = 1e-3
    rho = 1000

    target_omega = 1770.0
    q = 30.0
    iteration_count = 0
    simulation_duration = 30  # секунд

    print("Время (с) | Скорость | Ток  | Давление | Температуры (T2-T5)       | Расход | Режим работы")
    print("------------------------------------------------------------------------------------------")

    pump.na_start = True
    oil_system.start()

    try:
        while True:
            # ИЗМЕНЕНО
            # Обновляем маслосистему (параметры команд нужно передать корректно)
            oil_system.update(
                command_main_run=pump.na_on,
                command_main_stop=not pump.na_on,
                command_reserve_run=False,
                command_reserve_stop=True,
                dt=0.5
            )
            # Управление режимами насоса
            if iteration_count == 100:
                print("\n=== ПЕРЕКЛЮЧЕНИЕ В РЕЖИМ ЗАКРЫТОЙ ВХОДНОЙ ЗАДВИЖКИ ===")
                # В реальной системе это было бы вызвано внешним событием,
                # но здесь мы просто изменяем параметры, которые приведут к автоматическому
                # определению режима в методе detect_operation_mode()
                pump.na_stop = True

            # Основной шаг симуляции
            pump.step(target_omega, q, rho, True, True)
            print(pump.get_status())

            # Рассчитываем выходное давление
            pipe.compute_output_pressure(pump.p_out, m_dot_A, m_dot_B, mu, rho, pump.NA_AI_T_5_n)
            print(f"Output pressure to separator: {pipe.p_out:.10f} Pa, {pipe.T:.2f}")

            time.sleep(1)
            iteration_count += 1

    except KeyboardInterrupt:
        print("\nСимуляция остановлена.")
