# Data Pipeline

This is a minimal pipeline to fetch all players who ever played for Hapoel Be'er Sheva using a Transfermarkt API wrapper.

## How to run
1. Start the transfermarkt-api
2. Run: `poetry run python data_pipeline/main.py`

## With Docker
```
docker build -t data-pipeline .
docker run --rm data-pipeline
```