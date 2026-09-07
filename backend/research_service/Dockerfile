FROM python:3.13-slim
RUN pip install --no-cache-dir uv==0.9.2
WORKDIR /service
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY app ./app
CMD ["uv", "run", "--no-sync", "python", "-m", "app.main"]
