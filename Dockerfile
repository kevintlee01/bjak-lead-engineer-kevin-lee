FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/ server/
COPY static/ static/

RUN useradd --create-home --shell /bin/bash askkevin \
    && chown -R askkevin:askkevin /app
USER askkevin

WORKDIR /app/server

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
