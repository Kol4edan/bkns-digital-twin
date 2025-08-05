// src/App.js

import React, { useState, useEffect, useCallback } from 'react';
import * as api from './api/twinApi';
import ComponentCard from './components/ComponentCard';
import SimulationControls from './components/SimulationControls';
// --- 1. ИМПОРТИРУЕМ НОВЫЙ КОМПОНЕНТ ---
import SystemStatus from './components/SystemStatus';
import './App.css';

function App() {
  const [modelStatus, setModelStatus] = useState({});
  const [controlModes, setControlModes] = useState({});
  const [simulationMode, setSimulationMode] = useState(null);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, modesRes, simModeRes] = await Promise.all([
        api.getSimulationStatus(),
        api.getControlModes(),
        api.getSimulationMode(),
      ]);

      const flatData = statusRes.data;

      const grouped = {
        pumps: {},
        valves: {},
        oil_systems: {}
      };

      for (const [key, value] of Object.entries(flatData)) {
        if (key.startsWith("pump_")) grouped.pumps[key] = value;
        else if (key.startsWith("valve_out_")) grouped.valves[key] = value;
        else if (key.startsWith("oil_system_")) grouped.oil_systems[key] = value;
      }

      setModelStatus(grouped);
      setControlModes(modesRes.data);
      setSimulationMode(simModeRes.data.status);
      setError(null);
    } catch (err) {
      console.error("Ошибка при получении данных с сервера:", err);
      setError("Не удалось подключиться к серверу симуляции. Убедитесь, что он запущен.");
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div className="App">
      <h1 className="text-2xl font-bold mb-4">Панель управления цифровым двойником БКНС</h1>

      <SimulationControls
        fetchData={fetchData}
        controlModes={controlModes}
        simulationMode={simulationMode}
        setSimulationMode={setSimulationMode}
      />

      {error && <div className="text-red-500">{error}</div>}

      <SystemStatus status={modelStatus} />

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Насосы</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(modelStatus.pumps || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} />
          ))}
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Клапаны</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(modelStatus.valves || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} />
          ))}
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Маслосистемы</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(modelStatus.oil_systems || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
