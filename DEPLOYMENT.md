# Huddle Deployment Guide - Integration with simplyAsk

## Overview
Huddle shares the same PostgreSQL database and DigitalOcean Spaces with simplyAsk, using table prefixes for separation.

## Database Integration

### Table Prefixes
- **simplyAsk tables**: Use existing tables (no prefix yet, can add `simply_ask_` prefix)
- **Huddle tables**: All use `huddle_` prefix
- **Shared tables**: `auth_user`, `auth_group`, etc. (Django core)

### Huddle Tables
```sql
huddle_meeting                  -- Meeting records
huddle_meeting_participant      -- Meeting participants
huddle_audio_recording          -- Audio recordings
huddle_transcription_segment    -- Transcription segments
huddle_meeting_summary          -- AI-generated summaries
huddle_coordination_decision    -- Phone coordination decisions
huddle_audio_quality_metric     -- Audio quality metrics
```

## Deployment Steps

### 1. Initial Setup
```bash
# Clone repository
git clone [your-repo-url]
cd huddle

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables from simplyAsk
cp .env.example .env
# Edit .env with your actual values from simplyAsk
```

### 2. Database Migration
```bash
# Run Huddle-specific migrations only
./migrate_huddle.sh

# Or manually:
python manage.py migrate meetings --settings=config.settings.production
python manage.py migrate audio --settings=config.settings.production
python manage.py migrate coordination --settings=config.settings.production
```

### 3. Static Files
```bash
python manage.py collectstatic --settings=config.settings.production
```

### 4. DigitalOcean App Platform

#### Create New App from GitHub:

1. **Connect Repository**: `https://github.com/simply-ask/huddle`
2. **Auto-detect**: App Platform will detect Django app automatically
3. **Configure Two Services**:

#### Web Service (Django App):
- **Source**: GitHub repo `simply-ask/huddle`
- **Branch**: `main`  
- **Build Command**: `python -m pip install -r requirements.txt && python manage.py collectstatic --noinput --settings=config.settings.production`
- **Run Command**: `gunicorn --bind 0.0.0.0:8000 --workers 3 --worker-class uvicorn.workers.UvicornWorker config.asgi:application`
- **Environment**: Production
- **Instance Type**: Basic ($5/month)

#### Worker Service (Celery):
- **Source**: Same GitHub repo  
- **Build Command**: `python -m pip install -r requirements.txt`
- **Run Command**: `celery -A config worker -l info --settings=config.settings.production`
- **Environment**: Production
- **Instance Type**: Basic ($5/month)

#### Environment Variables (both services):
```
SECRET_KEY=[generate-new-secret]
DEBUG=False
DB_NAME=defaultdb
DB_USER=doadmin
DB_PASSWORD=[your-password]
DB_HOST=[your-db-host]
DB_PORT=25060
DO_SPACES_KEY=[your-key]
DO_SPACES_SECRET=[your-secret]
AWS_STORAGE_BUCKET_NAME=simplyask
REDIS_URL=[your-redis-url]
CELERY_BROKER_URL=[your-redis-url]
CELERY_RESULT_BACKEND=[your-redis-url]
OPENAI_API_KEY=[your-openai-key]
```

### 5. Redis Setup (for WebSockets)

You'll need Redis for Django Channels (WebSocket support):

1. Add Redis Database in DigitalOcean
2. Update `REDIS_URL` in environment variables
3. Ensure firewall rules allow connection

### 6. Domain Configuration

- Main app: `huddle.spot` or subdomain of simplyAsk
- WebSocket URL: `wss://huddle.spot/ws/`
- API endpoints: `https://huddle.spot/api/`

## Testing Integration

### 1. Check Database Tables
```python
python manage.py dbshell
\dt huddle_*
```

### 2. Test User Integration
```python
python manage.py shell
from django.contrib.auth.models import User
User.objects.all()  # Should show simplyAsk users
```

### 3. Test File Upload
- Upload audio file through API
- Check DigitalOcean Spaces: `huddle/recordings/` folder

## Monitoring

### Health Check Endpoints
- `/api/health/` - API health
- `/admin/` - Django admin (shared with simplyAsk)

### Logs
- Application logs in DigitalOcean App Platform
- Celery logs for background processing
- WebSocket connection logs

## Troubleshooting

### Common Issues

1. **Migration Conflicts**
   - Don't run `migrate` without app names
   - Only migrate Huddle-specific apps

2. **WebSocket Connection Failed**
   - Check Redis is running
   - Verify ASGI configuration
   - Check CORS settings

3. **File Upload Issues**
   - Verify DigitalOcean Spaces credentials
   - Check bucket permissions
   - Ensure `huddle/` folder exists in bucket

## Maintenance

### Adding New Models
1. Create models with explicit `db_table` using `huddle_` prefix
2. Run `makemigrations [app_name]`
3. Deploy and run migrations

### Backup Strategy
- Database is shared with simplyAsk (same backup strategy)
- Audio files in Spaces have versioning enabled

## Security Notes

1. **Shared Authentication**: Users logged into simplyAsk can access Huddle
2. **API Keys**: Keep OpenAI/Whisper keys secure for transcription
3. **CORS**: Configure for your specific domains only
4. **SSL**: Always use HTTPS in production