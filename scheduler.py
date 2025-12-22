import time
import datetime
import subprocess
import sys
import os

def run_overdue_update():
    """Запускает Django-команду обновления просрочек"""
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'update_overdue_loans'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('logs/scheduler.log', 'a') as f:
            f.write(f"[{timestamp}] STDOUT: {result.stdout}\n")
            if result.stderr:
                f.write(f"[{timestamp}] STDERR: {result.stderr}\n")
                
        print(f"[{timestamp}] Задача выполнена")
    except Exception as e:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('logs/scheduler.log', 'a') as f:
            f.write(f"[{timestamp}] ERROR: {str(e)}\n")
        print(f"[{timestamp}] Ошибка: {e}")

def main():
    """Запускает задачу каждый день в 9:00"""
    os.makedirs('logs', exist_ok=True)
    print("Сервис автоматического обновления просрочек запущен...")
    print("Задача будет выполняться ежедневно в 9:00")
    
    while True:
        now = datetime.datetime.now()
        # Следующий запуск — сегодня в 9:00 или завтра в 9:00
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > next_run:
            next_run += datetime.timedelta(days=1)
            
        sleep_seconds = (next_run - now).total_seconds()
        print(f"Следующий запуск: {next_run} (через {int(sleep_seconds)} секунд)")
        
        time.sleep(sleep_seconds)
        run_overdue_update()

if __name__ == "__main__":
    main()