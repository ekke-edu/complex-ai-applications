.PHONY: install run test clean

install:
	pip install -r requirements.txt

run:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
