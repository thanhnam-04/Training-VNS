FROM python:3.10-slim

WORKDIR /app

RUN pip install uv
COPY pyproject.toml ./
RUN uv pip install --system fastapi "uvicorn[standard]" sqlalchemy asyncpg pyjwt passlib[bcrypt] python-multipart alembic email-validator

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]