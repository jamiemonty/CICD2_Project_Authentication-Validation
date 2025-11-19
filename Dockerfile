FROM python:3.11-slim AS builder

WORKDIR /docu_serve
RUN pip install --upgrade pip wheel
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /docu_serve
RUN useradd -m appuser
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "docu_serve.main:app", "--host=0.0.0.0", "--port=8000"]