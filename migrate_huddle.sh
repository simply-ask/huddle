#!/bin/bash

echo "🚀 Migrating Huddle tables to shared simplyAsk database..."
echo ""
echo "This script will:"
echo "1. Apply only Huddle-specific migrations"
echo "2. Skip Django core migrations (already exist from simplyAsk)"
echo ""

# Only migrate Huddle apps, skip auth/admin/contenttypes/sessions as they exist
echo "📦 Migrating Huddle apps..."
python manage.py migrate meetings --settings=config.settings.development
python manage.py migrate audio --settings=config.settings.development  
python manage.py migrate coordination --settings=config.settings.development

echo ""
echo "✅ Huddle migrations complete!"
echo ""
echo "Verifying Huddle tables..."
python -c "
from decouple import config
import psycopg2

conn = psycopg2.connect(
    dbname=config('DB_NAME'),
    user=config('DB_USER'), 
    password=config('DB_PASSWORD'),
    host=config('DB_HOST'),
    port=config('DB_PORT'),
    sslmode='require'
)
cur = conn.cursor()
cur.execute(\"\"\"
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'huddle_%'
    ORDER BY table_name
\"\"\")
tables = cur.fetchall()
print('\\n📋 Huddle tables created:')
for table in tables:
    print(f'  ✓ {table[0]}')
cur.close()
conn.close()
"