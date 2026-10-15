FROM python:3.12.7-slim
WORKDIR /app
COPY kit.py policy.py ./
COPY graphvoi/ ./graphvoi/
COPY assets/ ./assets/
COPY vendor/ ./vendor/
COPY LICENSE DATA_LICENSE.md ./
# Bytecode is compiled once at build time from the copied source; the read-only
# runtime then reads it instead of recompiling NetworkX on every invocation.
RUN python -m compileall -q /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65534:65534
ENTRYPOINT ["python", "policy.py"]
