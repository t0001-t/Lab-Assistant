FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LAB_ASSISTANT_DATA_DIR=/data/lab_data
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 lab
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=lab:lab . /app
COPY --chown=lab:lab .streamlit/static /app/.streamlit/static/
RUN mkdir -p /data/lab_data /app/projects && chown -R lab:lab /data /app/projects
USER lab
EXPOSE 8502
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD curl -fsS http://127.0.0.1:8502/_stcore/health || exit 1
CMD ["python", "pwa_server.py", "--host", "0.0.0.0", "--port", "8502"]
