FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY radar ./radar
RUN pip install --no-cache-dir .

EXPOSE 8000

# a carga roda antes de servir, para o banco nunca ficar vazio na primeira subida
CMD ["sh", "-c", "python -m radar && uvicorn --factory radar.api:cria_app --host 0.0.0.0 --port 8000"]
