# main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, BackgroundTasks
from fastapi.staticfiles import StaticFiles # <--- Импортируем StaticFiles
from fastapi.responses import FileResponse # <--- Импортируем FileResponse
from pydantic import BaseModel

from Math.BKNS import BKNS
from opc_adapter import OPCAdapter

simulation_is_running = asyncio.Event()
SERVER_URL = "opc.tcp://10.0.22.154:4840"

simulation_manager = {"main_bkns": BKNS()}
control_logic = None  # Объявляем переменную
opc_adapter = None    # Объявляем переменную

class ManualCommand(BaseModel):
    source: str
    component: str

class SetModeCommand(BaseModel):
    source: str
    component: str

class ControlLogic:
    def __init__(self):
        # ИСПОЛЬЗУЕМ УНИКАЛЬНЫЕ, ПОЛНЫЕ ИМЕНА
        self.control_modes = {
            "pump_0": "OPC",
            "pump_1": "OPC",
            "valve_in_0": "OPC",
            "valve_out_0": "OPC",
            "valve_in_1": "OPC",
            "valve_out_1": "OPC",
            "oil_system_0": "OPC",
            "oil_system_1": "OPC",
        }
    
    def get_control_modes(self):
        return self.control_modes
        
    def set_control_source(self, component: str, source: str):
        if component not in self.control_modes:
            return {"status": "ERROR", "message": f"Неизвестный компонент: {component}"}
        if source not in ['MANUAL', 'OPC']:
            return {"status": "ERROR", "message": f"Неизвестный режим: {mode}"}
        
        self.control_modes[component] = source
        print(f"[CONTROL MODE] Режим для '{component}' изменен на '{source}'")
        return {"status": "OK", "message": f"Режим для {component} переключен на {source}."}

    def process_command(self, mode: str, source: str, component: str, param: str, value):
        print(f"\n[CONTROL] Команда: source={source}, component={component}, param={param}\n")

        # Проверяем, разрешено ли управление
        if self.control_modes.get(component) != source:
            print(f"[CONTROL] БЛОКИРОВАНО! Режим для '{component}': {self.control_modes.get(component)}")
            return {"status": "BLOCKED"}
        
        
        print(f"[CONTROL] РАЗРЕШЕНО. Отправка в модель.")
        model = simulation_manager["main_bkns"]
        
        try:
            comp_type, comp_id_str = component.rsplit('_', 1)
            comp_id_int = int(comp_id_str)
        except ValueError:
            return {"status": "ERROR", "message": f"Неверный формат ID в компоненте '{component}'"}

        # --- ИСПРАВЛЕННАЯ ЛОГИКА ДИСПЕТЧЕРИЗАЦИИ ---

        if comp_type == "pump":
            print("Обработка насоса...", param)
            if param == "na_start":
                model.control_pump(comp_id_int, True)
                model.get_status()
                return {"status": "OK", "message": f"Команда START для насоса {comp_id_int} выполнена"}
            # ИСПРАВЛЕНО: Теперь на stop передается False
            elif param == "na_stop":
                model.control_pump(comp_id_int, False)
                return {"status": "OK", "message": f"Команда STOP для насоса {comp_id_int} выполнена"}
                  
        elif comp_type == "valve_out":
            print("Обработка задвижки...")
            # ИСПРАВЛЕНО: ID задвижек формируются на основе ID компонента (valve_0 -> in_0, out_0)
            valve_in_id = f"in_{comp_id_int}"
            valve_out_id = f"out_{comp_id_int}"
            
            if param == "valve_open":
                model.control_valve(valve_in_id, True)
                model.control_valve(valve_out_id, True)
                return {"status": "OK", "message": f"Команды OPEN для задвижек {valve_in_id} и {valve_out_id} выполнены"}
            elif param == "valve_close":
                model.control_valve(valve_in_id, False)
                model.control_valve(valve_out_id, False)
                return {"status": "OK", "message": f"Команды CLOSE для задвижек {valve_in_id} и {valve_out_id} выполнены"}
                
        elif comp_type == "oil_system":
            print("Обработка маслосистемы...")
            if param == "oil_pump_start":
                model.control_oil_pump(comp_id_int, True)
                return {"status": "OK", "message": f"Команда START для маслонасоса {comp_id_int} выполнена."}
            # ИСПРАВЛЕНО: Условие для stop теперь правильное
            elif param == "oil_pump_stop":
                model.control_oil_pump(comp_id_int, False)
                return {"status": "OK", "message": f"Команда STOP для маслонасоса {comp_id_int} выполнена."}

        # Если ни один if не сработал, значит, параметр не подошел
        print(f"Неизвестный компонент {comp_type} с параметром {param}")
        return {"status": "ERROR", "message": f"Неизвестный параметр '{param}' для компонента '{component}'"}

# Инициализируем объекты после определения класса
control_logic = ControlLogic()
opc_adapter = OPCAdapter(SERVER_URL, control_logic, simulation_manager)

api_router = APIRouter(prefix="/api")

@api_router.get("/test")
async def test(): return {"message": "API работает"}
@api_router.get("/simulation/status")
def get_current_state(): return simulation_manager["main_bkns"].get_status()
@api_router.get("/simulation/control_modes")
def get_control_modes(): return control_logic.get_control_modes()

@api_router.post("/simulation/control/set_source")
def set_control_mode_endpoint(command: SetModeCommand): # Теперь SetModeCommand известен
    return control_logic.set_control_source(command.component, command.source)

'''
@api_router.post("/simulation/control/manual")
def control_from_manual(command: ManualCommand): # И ManualCommand известен
    return control_logic.process_command(
        mode="control",
        source="MANUAL", 
        component=command.component, 
        param=command.param,
        value=command.value
    )
'''

# --- НОВЫЙ ЭНДПОИНТ ДЛЯ СИНХРОНИЗАЦИИ ---
@api_router.post("/simulation/sync", status_code=202)
async def sync_simulation_endpoint(background_tasks: BackgroundTasks):
    """
    Запускает фоновую задачу для синхронизации состояния модели с OPC-сервером.
    """
    if not opc_adapter or not opc_adapter.is_running:
        return {"status": "ERROR", "message": "OPC-адаптер не подключен."}
    
    # Запускаем тяжелую операцию в фоне, чтобы не блокировать ответ
    background_tasks.add_task(opc_adapter.sync_with_opc_state)
    return {"status": "ACCEPTED", "message": "Синхронизация запущена."}
    
@api_router.post("/simulation/pause")
def pause_simulation():
    if not simulation_is_running.is_set(): return {"status": "already_paused"}
    simulation_is_running.clear(); print("[SYSTEM] Симуляция поставлена на паузу.")
    return {"status": "paused"}
@api_router.post("/simulation/resume")
def resume_simulation():
    if simulation_is_running.is_set(): return {"status": "already_running"}
    simulation_is_running.set(); print("[SYSTEM] Симуляция возобновлена.")
    return {"status": "resumed"}
@api_router.get("/simulation/mode")
def get_simulation_status(): return {"status": "running"} if simulation_is_running.is_set() else {"status": "paused"}



# --- Остальной код без изменений ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global update_task, opc_task
    print("[SYSTEM] Сервер запускается... Старт фоновых задач.")
    simulation_is_running.set()
    update_task = asyncio.create_task(update_loop())
    opc_task = asyncio.create_task(opc_adapter.run())
    yield 
    print("[SYSTEM] Сервер отключается... Остановка фоновых задач.")
    if opc_adapter.is_running: await opc_adapter.disconnect()
    if opc_task and not opc_task.done(): opc_task.cancel()
    if update_task and not update_task.done(): update_task.cancel()
    await asyncio.gather(opc_task, update_task, return_exceptions=True)
    print("[SYSTEM] Фоновые задачи успешно завершены. Сервер выключен.")

app = FastAPI(title="Digital Twin Control API", lifespan=lifespan)


#3. Подключаем роутер с API к основному приложению
app.include_router(api_router)

# 4. Монтируем папку со статическими файлами React
app.mount("/", StaticFiles(directory="build", html=True), name="static")

@app.get("/{full_path:path}", include_in_schema=False) # include_in_schema=False, чтобы не мешать Swagger
async def serve_react_app(full_path: str):
    index_path = os.path.join(BUILD_DIR, "index.html")
    # Проверяем, существует ли файл, чтобы избежать ошибок
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found"} # Или можно вернуть 404

@app.get("/debug/model_status")
def get_raw_model_status():
    """
    ВРЕМЕННЫЙ ЭНДПОИНТ ДЛЯ ОТЛАДКИ.
    Возвращает полный, необработанный словарь состояния модели BKNS.
    """
    print("[DEBUG] Запрошен полный статус модели.")
    return simulation_manager["main_bkns"].get_status()
    
async def update_loop():
    while True:
        try:
            await simulation_is_running.wait()
            # print("--- Обновление состояния модели ---")
            for model_name, model in simulation_manager.items():
                model.update_system()
                #print(model.get_status()) 
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("[LOOP] Цикл обновления модели остановлен.")
            break