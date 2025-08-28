\
        # Multi-stage Dockerfile (minimal)
        ARG PY_VER=3.11
        FROM python:${PY_VER}-slim AS build
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . .

        FROM python:${PY_VER}-slim AS runtime
        # create non-root user
        RUN addgroup --system app && adduser --system --ingroup app app
        WORKDIR /app
        # copy installed packages from build stage
        COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
        COPY --from=build /app /app
        USER app
        EXPOSE 8080
        HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD python - <<'PY' || exit 1
        import sys, urllib.request as u
        try:
            r = u.urlopen('http://127.0.0.1:8080/health', timeout=2)
            sys.exit(0 if r.getcode()==200 else 1)
        except Exception:
            sys.exit(1)
        PY
        CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
