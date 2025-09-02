#!/bin/bash

echo "🚀 Migrating Huddle tables to shared simplyAsk database..."
echo ""
echo "This script will:"
echo "1. Apply only Huddle-specific migrations"
echo "2. Skip Django core migrations (already exist from simplyAsk)"
echo ""

# Only migrate Huddle apps, skip auth/admin/contenttypes/sessions as they exist
echo "📦 Migrating Huddle apps..."
python manage.py migrate meetings
python manage.py migrate audio
python manage.py migrate coordination

echo ""
echo "✅ Huddle migrations complete!"
echo ""
echo "Verifying Huddle tables..."
python -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.environ.get('DB_NAME'),
    user=os.environ.get('DB_USER'), 
    password=os.environ.get('DB_PASSWORD'),
    host=os.environ.get('DB_HOST'),
    port=os.environ.get('DB_PORT'),
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