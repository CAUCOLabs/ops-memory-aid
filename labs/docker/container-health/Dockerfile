FROM python:3.12-alpine

WORKDIR /app

COPY app.py .

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s \
  --start-period=2s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["python", "-u", "app.py"]
