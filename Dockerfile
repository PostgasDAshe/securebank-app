FROM python:3.12-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY app_corregida.py .

RUN pip install --no-cache-dir flask werkzeug

USER appuser

EXPOSE 5000

CMD ["python", "app_corregida.py"]