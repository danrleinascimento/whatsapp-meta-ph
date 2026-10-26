"""Linha de comando do whatsph.exe (agente local WHATSPH).

Uso: whatsph <comando>
Sem argumentos e iniciado pelo Windows, o exe atende como servico PHWhatsMeta.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from collections.abc import Sequence

from app import __version__

AGENT_HOST = "127.0.0.1"
AGENT_DEFAULT_PORT = 8767

SERVICE_COMMANDS = {
    "install-service": ["--startup", "auto", "install"],
    "update-service": ["--startup", "auto", "update"],
    "remove-service": ["remove"],
    "start-service": ["start"],
    "stop-service": ["stop"],
    "restart-service": ["restart"],
    "debug-service": ["debug"],
}


def print_json(value) -> None:
    print(json.dumps(value, ensure_ascii=True))


def agent_port() -> int:
    from app.config import get_settings

    settings = get_settings()
    if "port" in settings.model_fields_set:
        return settings.port
    return AGENT_DEFAULT_PORT


def setup_logging() -> None:
    from app.caminhos import logs_dir
    from app.config import get_settings

    folder = logs_dir()
    folder.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler = logging.handlers.RotatingFileHandler(
        folder / "whatsph.log", maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(getattr(logging, get_settings().log_level.upper(), logging.INFO))
    root.addHandler(file_handler)
    # No servico o stderr vai para logs\whatsph-service.log (sem rotacao): ali so erro fatal.
    if sys.stderr is not None and sys.stderr.isatty():
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)
    # Uma linha por consulta ao hub (a cada POLL_INTERVAL_SECONDS) encheria o log.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def run_server(_: list[str]) -> int:
    os.environ.setdefault("APP_ROLE", "agent")
    setup_logging()
    import uvicorn

    from app.main import app

    uvicorn.run(
        app,
        host=AGENT_HOST,
        port=agent_port(),
        loop="asyncio",
        http="h11",
        ws="none",
        log_config=None,
        workers=1,
    )
    return 0


def check_service(args: list[str]) -> int:
    import httpx

    timeout = 10.0
    if "--timeout" in args:
        position = args.index("--timeout") + 1
        try:
            timeout = float(args[position])
        except (IndexError, ValueError):
            print("Uso: whatsph verificar-servico [--timeout SEGUNDOS]", file=sys.stderr)
            return 2
    url = f"http://{AGENT_HOST}:{agent_port()}/health"
    try:
        response = httpx.get(url, timeout=timeout, trust_env=False)
        body = response.json()
    except Exception as exc:
        print_json({"status": "ERRO", "codigo": "WHATSPH_SEM_RESPOSTA", "url": url, "mensagem": str(exc)})
        return 1
    print_json(body)
    if response.status_code == 200 and isinstance(body, dict) and body.get("status") == "ok":
        return 0
    return 1


def generate_config(args: list[str]) -> int:
    from app.comandos.gerar_configuracao import generate

    return generate(force="--force" in args)


def apply_sql(_: list[str]) -> int:
    os.environ.setdefault("APP_ROLE", "agent")
    from app.db.migrate import AGENT_SQL_FILES, apply_sql_files

    result = apply_sql_files(AGENT_SQL_FILES)
    print_json(result)
    return 0 if result.get("ok") else 1


def show_version(_: list[str]) -> int:
    print(__version__)
    return 0


COMMANDS = {
    "run-server": run_server,
    "verificar-servico": check_service,
    "gerar-configuracao": generate_config,
    "aplicar-sql": apply_sql,
    "version": show_version,
}


def print_help() -> None:
    print("Uso: whatsph <comando> [argumentos]")
    print("")
    print("Comandos:")
    for command in sorted([*COMMANDS, *SERVICE_COMMANDS]):
        print(f"  {command}")


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None and len(sys.argv) == 1:
        try:
            from app.servico_windows import dispatch_service
        except ImportError:
            dispatch_service = None
        if dispatch_service is not None and dispatch_service():
            return 0
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print_help()
        return 0
    command = args[0]
    service_args = SERVICE_COMMANDS.get(command)
    if service_args is not None:
        from app.servico_windows import run_service_command

        return run_service_command([*service_args, *args[1:]])
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Comando desconhecido: {command}", file=sys.stderr)
        print_help()
        return 2
    return handler(args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
