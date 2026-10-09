FROM python:3.10.19-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git libgomp1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /study
COPY src/configs/environments/cpu/requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir setuptools==75.3.0 \
    && python -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock
COPY src ./src
RUN python -m pip install --no-deps --no-build-isolation -e ./src
ENTRYPOINT ["slam-study"]
CMD ["doctor"]
