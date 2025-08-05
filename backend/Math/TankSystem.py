from .tanks.Tank import Tank
from .sensors.tank_sensors import TankDensitySensor,TankFlowRateSensor,TankLevelSensor,TankTemperatureSensor
class TankSystem:
    def __init__(self, volume_max=10.0):
        # Модель резервуара
        self.tank = Tank(volume_max=volume_max)

        # Датчики жидкости с диапазонами
        self.level_sensor = TankLevelSensor(volume_max=volume_max)
        self.density_sensor = TankDensitySensor()
        self.temperature_sensor = TankTemperatureSensor()
        self.flow_sensor = TankFlowRateSensor(flow_max=10.0)  # макс расход 10 м3/ч

        # Текущие показания датчиков (ток, мА)
        self.sensor_values = {
            'level_mA': 0.0,
            'density_mA': 0.0,
            'temperature_mA': 0.0,
            'flow_mA': 0.0
        }

    def set_valve_states(self, inlet_states, outlet_states):
        """Установка состояний клапанов (списки булевых значений длиной 4)."""
        for idx, state in enumerate(inlet_states):
            self.tank.set_inlet_valve(idx, state)
        for idx, state in enumerate(outlet_states):
            self.tank.set_outlet_valve(idx, state)

    def update(self, inflow_rates, outflow_rates, new_density=None, new_temp=None, dt_hours=0.5):
        """
        Обновить состояние резервуара и датчиков за dt_hours.
        inflow_rates, outflow_rates — списки мгновенных расходов (м3/ч) длиной 4.
        new_density, new_temp — опциональное обновление физических свойств.
        """
        # Передать в update модели состояния клапанов и потоков
        self.tank.update(
            inlet_flow_signals=self.tank.inlet_valve_states,
            outlet_flow_signals=self.tank.outlet_valve_states,
            inflow_rates=inflow_rates,
            outflow_rates=outflow_rates,
            new_density=new_density,
            new_temp=new_temp,
            dt_hours=dt_hours
        )

        # Измерить токовые сигналы с датчиков по текущим параметрам
        self.sensor_values['level_mA'] = self.level_sensor.measure_current(self.tank.level)
        self.sensor_values['density_mA'] = self.density_sensor.measure_current(self.tank.density)
        self.sensor_values['temperature_mA'] = self.temperature_sensor.measure_current(self.tank.temperature)
        self.sensor_values['flow_mA'] = self.flow_sensor.measure_current(self.tank.inflow_rate)


    def __str__(self):
        lines = []
        lines.append("=== Состояние резервуара и датчиков ===")
        lines.append(f"{'Параметр':<20} {'Значение':>12} {'Сигнал (ток мА)':>20}")
        lines.append("-" * 54)

        lines.append(f"{'Уровень (м³)':<20} {self.tank.level:12.3f} {self.sensor_values['level_mA']:20.2f}")
        lines.append(f"{'Плотность (кг/м³)':<20} {self.tank.density:12.2f} {self.sensor_values['density_mA']:20.2f}")
        lines.append(f"{'Температура (°C)':<20} {self.tank.temperature:12.2f} {self.sensor_values['temperature_mA']:20.2f}")
        lines.append(f"{'Входной расход (м³/ч)':<20} {self.tank.inflow_rate:12.3f} {self.sensor_values['flow_mA']:20.2f}")

        lines.append("\nСостояния клапанов:")
        lines.append(f"  Входные: {['открыт' if v else 'закрыт' for v in self.tank.inlet_valve_states]}")
        lines.append(f"  Выходные: {['открыт' if v else 'закрыт' for v in self.tank.outlet_valve_states]}")

        return "\n".join(lines)


# Пример использования
if __name__ == "__main__":
    import time

    # Создаём систему резервуара с датчиками
    tank_sys = TankSystem(volume_max=10.0)

    # Начальные состояния клапанов (открыты входные 0 и 2, закрыты остальные; выходные все открыты)
    tank_sys.set_valve_states(
        inlet_states=[True, False, True, False],
        outlet_states=[True, True, True, True]
    )

    # Расходы на клапанах (м3/ч)
    inflow_rates = [1.0, 0.0, 0.5, 0.0]
    outflow_rates = [0.6, 0.4, 0.0, 0.0]

    print("=== Начало симуляции резервуара ===")
    for step in range(6):
        # На 0.5 часа обновляем модель и датчики
        tank_sys.update(inflow_rates, outflow_rates, new_density=850.0 + step, new_temp=20.0 + step * 0.5, dt_hours=0.5)
        print(f"\n--- Шаг {step + 1} ---")
        print(tank_sys)
        time.sleep(0.5)  # чтобы имитировать время, в реальной программе можно убрать
