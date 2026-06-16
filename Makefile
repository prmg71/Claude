.PHONY: up down restart logs status

PID_FILE := .uvicorn.pid
LOG_FILE := .uvicorn.log
PYTHON   := venv/bin/python
UVICORN  := venv/bin/uvicorn
APP      := app.api.main:app
PORT     := 8000

## Sobe o servidor em background
up:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Servidor já está rodando (PID $$(cat $(PID_FILE)))."; \
		exit 0; \
	fi
	$(UVICORN) $(APP) --host 0.0.0.0 --port $(PORT) \
		--log-level info >> $(LOG_FILE) 2>&1 & \
	echo $$! > $(PID_FILE)
	@echo "Servidor iniciado (PID $$(cat $(PID_FILE))). Docs em http://localhost:$(PORT)/docs"
	@echo "Logs: make logs"

## Derruba o servidor
down:
	@if [ ! -f $(PID_FILE) ]; then \
		echo "Servidor não está rodando ($(PID_FILE) não encontrado)."; exit 0; \
	fi
	@PID=$$(cat $(PID_FILE)); \
	if kill -0 $$PID 2>/dev/null; then \
		kill $$PID && echo "Servidor encerrado (PID $$PID)."; \
	else \
		echo "Processo $$PID já não existe."; \
	fi; \
	rm -f $(PID_FILE)

## Reinicia o servidor
restart: down up

## Exibe os logs em tempo real (Ctrl+C para sair)
logs:
	@tail -f $(LOG_FILE)

## Mostra se o servidor está rodando
status:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Rodando (PID $$(cat $(PID_FILE)))."; \
	else \
		echo "Parado."; \
	fi

## Sobe em modo dev com reload automático (foreground)
dev:
	$(UVICORN) $(APP) --host 0.0.0.0 --port $(PORT) --reload
