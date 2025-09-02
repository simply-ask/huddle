web: gunicorn -k uvicorn.workers.UvicornWorker config.asgi:application --log-file -
worker: celery -A config worker --loglevel=info --pool=threads --concurrency=4