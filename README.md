# Huddle - AI-Powered Meeting Intelligence Platform

Transform any meeting into actionable insights with zero friction. Just tap a link and let the collective intelligence of your team's phones create meeting transcripts, summaries, action items, and searchable meeting memory across your organization.

## 🚀 Key Features

### Multi-Phone Coordination
- **Zero-friction setup**: Participants join by visiting `huddle.spot/meet/[ID]` on their phones
- **No downloads required**: Progressive Web App (PWA) runs directly in browser
- **Smart audio capture**: Multiple phones work together as a distributed recording network
- **Intelligent coordination**: Algorithms determine optimal recording device based on proximity and quality

### AI-Powered Processing
- **High-accuracy transcription**: Using OpenAI Whisper for speech-to-text
- **Speaker diarization**: Identify who said what
- **Meeting summaries**: Automatic generation of key points and action items
- **RAG-powered insights**: Extract actionable intelligence from meetings

### Enterprise Integration
- **Shared authentication**: Integrated with simplyAsk user system
- **Organization support**: Multi-tenant architecture with company profiles
- **Cloud storage**: Audio files stored in DigitalOcean Spaces
- **Scalable processing**: Celery background tasks for AI processing

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.2 with Django REST Framework
- **Real-time**: Django Channels with WebSocket support
- **Task Queue**: Celery with Redis backend
- **Database**: PostgreSQL (shared with simplyAsk)
- **Storage**: DigitalOcean Spaces
- **AI/ML**: OpenAI Whisper, Custom coordination algorithms
- **Deployment**: DigitalOcean App Platform

### Project Structure
```
huddle/
├── apps/
│   ├── core/           # Shared utilities
│   ├── meetings/       # Meeting management & WebSocket
│   ├── audio/          # Audio processing & Whisper
│   ├── coordination/   # Multi-phone algorithms
│   └── api/            # REST API endpoints
├── config/             # Django settings
├── static/             # PWA assets
│   ├── js/            # Audio capture, WebSocket client
│   └── manifest.json   # PWA configuration
└── templates/          # HTML templates
```

## 🔧 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Node.js (for frontend tools)

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/simply-ask/huddle.git
cd huddle
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database and service credentials
```

5. **Run migrations**
```bash
./migrate_huddle.sh
# Or manually:
python manage.py migrate meetings
python manage.py migrate audio
python manage.py migrate coordination
```

6. **Start development server**
```bash
python manage.py runserver --settings=config.settings.development
```

7. **Start Celery worker** (in another terminal)
```bash
celery -A config worker -l info
```

8. **Access the application**
- Visit: http://localhost:8000
- Join meeting: http://localhost:8000/meet/[meeting-id]/

## 📱 PWA Features

### Mobile Capabilities
- **Install as app**: Add to home screen on iOS/Android
- **Offline support**: Service worker caching
- **Audio permissions**: Microphone access handling
- **Background sync**: Upload recordings when connection restored

### Browser Support
- Chrome/Edge 90+
- Safari 14+ (iOS)
- Firefox 88+

## 🔌 API Endpoints

### Meeting Management
- `POST /api/meetings/` - Create new meeting
- `GET /api/meetings/{meeting_id}/` - Get meeting details
- `GET /api/meeting/{meeting_id}/status/` - Get participants and status

### Audio Processing
- `POST /api/upload-audio/` - Upload audio recording
- `GET /api/recordings/` - List recordings

### WebSocket Endpoints
- `/ws/meeting/{meeting_id}/` - Meeting coordination
- `/ws/coordination/{meeting_id}/` - Phone coordination

## 🔐 Security

- **Authentication**: Django authentication (shared with simplyAsk)
- **HTTPS only**: SSL required in production
- **CORS protection**: Configured for specific domains
- **File permissions**: Secure audio file handling
- **Environment variables**: Sensitive data in .env

## 🚀 Deployment

### DigitalOcean App Platform

1. **Create App**: Use DigitalOcean App Platform
2. **Configure environment**: Add all variables from .env
3. **Set build command**: `python manage.py collectstatic --noinput`
4. **Set run command**: 
```bash
gunicorn --bind 0.0.0.0:8000 --workers 3 --worker-class uvicorn.workers.UvicornWorker config.asgi:application
```

### Database Integration
- Shares PostgreSQL with simplyAsk
- Tables use `huddle_` prefix
- User authentication shared across apps

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🧪 Testing

```bash
# Run tests
python manage.py test

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Database Schema

### Key Tables (all with `huddle_` prefix)
- `huddle_meeting` - Meeting records
- `huddle_meeting_participant` - Participants and devices
- `huddle_audio_recording` - Audio file records
- `huddle_transcription_segment` - Transcribed text segments
- `huddle_meeting_summary` - AI-generated summaries
- `huddle_coordination_decision` - Phone selection algorithms
- `huddle_audio_quality_metric` - Audio quality tracking

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For issues or questions:
- Create an issue on GitHub
- Contact: support@simplyask.me

## 🙏 Acknowledgments

- OpenAI Whisper for transcription
- Django Channels for WebSocket support
- DigitalOcean for infrastructure
- The simplyAsk team for integration support

---

Built with ❤️ by the simplyAsk team