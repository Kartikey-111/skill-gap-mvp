 .PHONY: build run dev test down

 build:
 	docker compose build

 run:
 	docker compose up -d

 dev:
	uvicorn main:app --reload --port 8080

 test:
	curl -s -X POST http://127.0.0.1:8080/diagnostics/generate -H "Content-Type: application/json" -d @sample_payload.json | jq .

 down:
	docker compose down -v
