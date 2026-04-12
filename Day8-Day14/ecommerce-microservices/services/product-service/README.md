# product-service

Phu trach inventory, product, category.
Codebase doc lap trong chinh thu muc service nay.

## Unit test va lint (Pytest + Ruff)

1. Cai goi dev:

	pip install -r requirements-dev.txt

2. Chay unit test:

	pytest

3. Kiem tra clean code theo Ruff:

	ruff check tests

4. Do coverage cho module notifications tasks:

	pytest --cov=apps.notifications.tasks --cov-report=term-missing

5. Do coverage cho module core service_clients:

	pytest tests/test_service_clients.py --cov=apps.orders.service_clients --cov-report=term-missing
