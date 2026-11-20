"""Erase only this repository's disposable browser-test database, never an env URL."""
from pathlib import Path
import sqlite3
root=Path(__file__).resolve().parents[1]
path=root/'e2e.db'
if path.exists():
    connection=sqlite3.connect(path)
    counts={}
    for table in ['users','tickets','comments','attachments','history','ratings','categories','saved_replies']:
        try: counts[table]=connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
        except sqlite3.OperationalError: counts[table]=0
    connection.close()
    print('Deleting disposable project-local e2e.db. Row counts:',counts)
    path.unlink()
    for suffix in ['-wal','-shm','-journal']:
        sidecar=Path(str(path)+suffix)
        if sidecar.exists(): sidecar.unlink()
    print('All E2E accounts, tickets, uploads and configuration fixtures removed. Development ticketdesk.db untouched.')
else:
    print('No disposable E2E database exists. Nothing deleted.')
