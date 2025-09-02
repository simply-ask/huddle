web: gunicorn -k uvicorn.workers.UvicornWorker config.asgi:application --bind 0.0.0.0:8080 --log-file -
worker: celery -A config worker --loglevel=info --pool=threads --concurrency=4