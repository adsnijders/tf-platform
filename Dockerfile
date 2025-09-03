FROM alpine:3.22.0

# Set up a path for the uv CLI
ENV PATH="$PATH:/root/.local/bin"

# Install uv and python
RUN wget -qO- https://astral.sh/uv/install.sh | sh
RUN apk update && apk add python3 git

# Set a working directory and copy the project
WORKDIR /app
COPY ./ .

# Sync all dependencies with uv
RUN uv sync

# Excecute command
CMD ["uv" , "run", "uvicorn", "roman_api.main:app", "--host", "0.0.0.0", "--port", "8000"]