# Birthday Wishes
- For celebrating birthdays

# Dev
- Poetry
- Python
- Docker(optional)

## How to use
### With Docker
1. Build container
```sh
docker compose build --no-cache
```

2. Start container
```sh
docker compose up -d
```

### Without Docker
1. Install dependencies
```sh
poetry install
```

2. Start Discord bot
```
poetry run python birthday.py
```
