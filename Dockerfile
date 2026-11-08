FROM python:3.12-alpine
WORKDIR /app
COPY app.py index.html styles.css app.js favicon.svg ./
RUN addgroup -S cooksy && adduser -S -G cooksy -u 10001 cooksy && mkdir -p /data && chown -R cooksy:cooksy /data /app
USER cooksy
ENV PYTHONUNBUFFERED=1 COOKSY_DATA_DIR=/data
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz',timeout=2)"
CMD ["python", "app.py"]
