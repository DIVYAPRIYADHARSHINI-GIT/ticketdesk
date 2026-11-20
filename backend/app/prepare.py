"""Remote deployment build step: migrate and optionally seed, without exposing credentials."""
import os
import sys
from alembic import command
from alembic.config import Config

def main():
    if not os.getenv('DATABASE_URL'):
        print('Deployment blocked: DATABASE_URL must be supplied securely by the hosting integration.')
        return 1
    try:
        command.upgrade(Config('alembic.ini'),'head')
        print('TicketDesk database migration complete.')
        if os.getenv('DEMO_ENABLED')=='true':
            from .db import SessionLocal
            from .seed import seed
            with SessionLocal() as db:
                created=seed(db)
                print('Fictional demo seeded (60 tickets).' if created else 'Fictional demo already seeded; unchanged.')
        return 0
    except Exception as error:
        # SQL exceptions can otherwise include sensitive connection information or parameters.
        print('Deployment database preparation failed: '+type(error).__name__+'. Check the service connection in the hosting dashboard. No credentials were logged.')
        return 1
if __name__=='__main__': sys.exit(main())
