.PHONY: install clean api client

install:
	pip install -r requirements.txt

run-api:
	uvicorn src.backend.api:app --host 0.0.0.0 --port 8000 --reload
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

run-app:
	streamlit run src/client/app.py