"""Servico Windows PHWhatsMeta (pywin32), no mesmo modelo do huph.exe.

O servico executa `whatsph.exe run-server` como processo filho e o encerra no stop.
"""

from __future__ import annotations

import subprocess
import sys
import time

from app.caminhos import install_dir, is_frozen, logs_dir, resource_dir

try:
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil
except ImportError:
    servicemanager = None
    win32event = None
    win32service = None
    win32serviceutil = None


SERVICE_NAME = "PHWhatsMeta"
SERVICE_DISPLAY_NAME = "PHWhatsMeta - WhatsApp oficial PH"
SERVICE_DESCRIPTION = "Agente local WHATSPH: envio de PDFs pela API oficial do WhatsApp (Meta) para os sistemas PH"
# O Windows devolve o start/stop antes de o servico mudar de estado (START_PENDING).
WAIT_INTERVAL = 0.5
WAIT_ATTEMPTS = 60
# Se o agente cair, o servico o reinicia, com espera crescente se cair logo apos subir.
RESTART_DELAY_MIN_MS = 5000
RESTART_DELAY_MAX_MS = 60000
STABLE_RUN_SECONDS = 60
SERVICE_BASE = win32serviceutil.ServiceFramework if win32serviceutil is not None else object


class WhatsPhService(SERVICE_BASE):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME
    _svc_description_ = SERVICE_DESCRIPTION

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        self.started_at = 0.0
        self.log_file = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.stop_process()

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        servicemanager.LogInfoMsg(f"{SERVICE_DISPLAY_NAME} iniciado")
        try:
            self.run_server()
        finally:
            self.close_log()
            servicemanager.LogInfoMsg(f"{SERVICE_DISPLAY_NAME} finalizado")

    def run_server(self):
        self.log_file = open_service_log()
        try:
            self.start_process()
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            delay_ms = RESTART_DELAY_MIN_MS
            while True:
                if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                    return
                exit_code = self.process.poll()
                if exit_code is None:
                    continue
                if time.monotonic() - self.started_at >= STABLE_RUN_SECONDS:
                    delay_ms = RESTART_DELAY_MIN_MS
                servicemanager.LogWarningMsg(
                    f"{SERVICE_NAME}: agente encerrou (codigo {exit_code}); "
                    f"reiniciando em {delay_ms // 1000} s. Ver logs\\whatsph.log"
                )
                if win32event.WaitForSingleObject(self.stop_event, delay_ms) == win32event.WAIT_OBJECT_0:
                    return
                delay_ms = min(delay_ms * 2, RESTART_DELAY_MAX_MS)
                self.start_process()
        finally:
            # O stop pode chegar entre a espera e um reinicio: nao deixar o agente orfao.
            self.stop_process()

    def start_process(self):
        self.process = subprocess.Popen(
            server_command(),
            cwd=str(working_dir()),
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
        )
        self.started_at = time.monotonic()

    def stop_process(self):
        if self.process is None or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def close_log(self):
        if self.log_file is None:
            return
        self.log_file.close()
        self.log_file = None


def working_dir():
    if is_frozen():
        return install_dir()
    return resource_dir()


def server_command() -> list[str]:
    if is_frozen():
        return [sys.executable, "run-server"]
    return [sys.executable, "-m", "app.cli", "run-server"]


def open_service_log():
    path = logs_dir() / "whatsph-service.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a", encoding="utf-8")


def dispatch_service() -> bool:
    if servicemanager is None:
        return False
    try:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WhatsPhService)
        servicemanager.StartServiceCtrlDispatcher()
        return True
    except Exception:
        return False


def has_command(args: list[str], name: str) -> bool:
    return name in {arg.lower() for arg in args}


def query_status():
    try:
        return win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1]
    except Exception:
        return None


def wait_status(expected):
    """Consulta ate o servico atingir o estado esperado (ou o tempo limite)."""
    status = query_status()
    for _ in range(WAIT_ATTEMPTS - 1):
        if status == expected:
            break
        time.sleep(WAIT_INTERVAL)
        status = query_status()
    return status


def validate_result(args: list[str]) -> None:
    if has_command(args, "start") or has_command(args, "restart"):
        status = wait_status(win32service.SERVICE_RUNNING)
    elif has_command(args, "remove"):
        status = wait_status(None)
    elif has_command(args, "stop"):
        status = wait_status(win32service.SERVICE_STOPPED)
    else:
        status = query_status()
    if has_command(args, "install") and status is None:
        raise RuntimeError(f"Falha ao instalar servico Windows {SERVICE_NAME}")
    if has_command(args, "update") and status is None:
        raise RuntimeError(f"Falha ao atualizar servico Windows {SERVICE_NAME}")
    if has_command(args, "start") and status != win32service.SERVICE_RUNNING:
        raise RuntimeError(f"Falha ao iniciar servico Windows {SERVICE_NAME}")
    if has_command(args, "restart") and status != win32service.SERVICE_RUNNING:
        raise RuntimeError(f"Falha ao reiniciar servico Windows {SERVICE_NAME}")
    if has_command(args, "stop") and status != win32service.SERVICE_STOPPED:
        raise RuntimeError(f"Falha ao parar servico Windows {SERVICE_NAME}")
    if has_command(args, "remove") and status is not None:
        raise RuntimeError(f"Falha ao remover servico Windows {SERVICE_NAME}")


def run_service_command(args: list[str]) -> int:
    if win32serviceutil is None:
        print("pywin32 nao esta disponivel", file=sys.stderr)
        return 1
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0], *args]
    try:
        win32serviceutil.HandleCommandLine(WhatsPhService)
        validate_result(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        sys.argv = original_argv
    return 0
