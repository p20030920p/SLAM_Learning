FROM python:3.10.19-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git libgomp1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /study
COPY requirements.lock pyproject.toml ./
RUN python -m pip install --no-cache-dir setuptools==75.3.0 \
    && python -m pip install --no-cache-dir --require-hashes -r requirements.lock
COPY src ./src
COPY configs ./configs
COPY tests ./tests
RUN python -m pip install --no-deps --no-build-isolation -e .
ENTRYPOINT ["slam-study"]
CMD ["doctor"]
