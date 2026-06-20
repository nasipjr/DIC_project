import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from flask import current_app

BACKUP_DIR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'backups')

def run_database_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if db_uri.startswith('mysql'):
        import re
        match = re.match(r'mysql(?:\+[\w]+)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/([\w\-_]+)', db_uri)
        if match:
            user, password, host, port, dbname = match.groups()
            port = port or "3306"
            backup_filename = f"backup_{dbname}_{timestamp}.sql"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            
            cmd = [
                'mysqldump',
                f'--host={host}',
                f'--port={port}',
                f'--user={user}',
                f'--password={password}',
                dbname
            ]
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
                
            if result.returncode != 0:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                raise Exception(f"mysqldump failed: {result.stderr}")
                
            rotate_backups()
            return backup_filename
        else:
            raise Exception("Failed to parse MySQL URI configuration.")
            
    elif db_uri.startswith('sqlite'):
        import re
        match = re.match(r'sqlite:///(.+)', db_uri)
        if match:
            db_path = match.group(1)
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
                
            if os.path.exists(db_path):
                backup_filename = f"backup_sqlite_{timestamp}.db"
                backup_path = os.path.join(BACKUP_DIR, backup_filename)
                shutil.copy2(db_path, backup_path)
                
                rotate_backups()
                return backup_filename
            else:
                raise Exception(f"SQLite database file not found at: {db_path}")
        else:
            raise Exception("Cannot backup memory-only SQLite database.")
    else:
        raise Exception(f"Unsupported database system: {db_uri}")

def rotate_backups():
    if not os.path.exists(BACKUP_DIR):
        return
        
    backups = []
    for f in os.listdir(BACKUP_DIR):
        p = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(p) and f.startswith('backup_') and (f.endswith('.sql') or f.endswith('.db')):
            backups.append((p, os.path.getmtime(p)))
            
    backups.sort(key=lambda x: x[1])
    
    if len(backups) > 10:
        for i in range(len(backups) - 10):
            try:
                os.remove(backups[i][0])
            except Exception:
                pass

def schedule_daily_backups(app):
    def run_backup_loop():
        # wait a bit for app startup
        time.sleep(10)
        while True:
            with app.app_context():
                try:
                    run_database_backup()
                    app.logger.info("Daily database backup executed successfully.")
                except Exception as e:
                    app.logger.error(f"Failed to execute daily database backup: {e}")
            time.sleep(86400)
    
    thread = threading.Thread(target=run_backup_loop, daemon=True)
    thread.start()
