import psutil
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
    try:
        if 'python' in p.info['name'].lower() and p.info['cmdline']:
            if 'app.py' in ' '.join(p.info['cmdline']):
                print(f"PID: {p.info['pid']} | CWD: {p.info['cwd']} | CMD: {' '.join(p.info['cmdline'])}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
