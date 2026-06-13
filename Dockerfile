# Imagem base enxuta com o mesmo Python usado no desenvolvimento.
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instala dependências primeiro (melhor cache de camadas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação e referências.
COPY app ./app
COPY referencias ./referencias

# Usuário não-root (boa prática de segurança/governança) + diretórios de dados.
RUN useradd -m -u 1000 appuser \
    && mkdir -p data/uploads data/knowledge relatorios contratos \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Verificação de saúde (sem dependências extras, usa a stdlib).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
