import pytest
import platform
import os

from django.conf import settings
from pytest_postgresql.executor import PostgreSQLExecutor


# pytest-postgresql uses single quotes inside the `-o "..."` argument for pg_ctl,
# which breaks on Windows (postgres receives "'stderr'" literally).
if platform.system() == "Windows":
    if not hasattr(os, "killpg"):
        def _killpg(pid: int, sig: int) -> None:
            try:
                os.kill(pid, sig)
            except (PermissionError, ProcessLookupError):
                # pytest-postgresql already stops the server via `pg_ctl stop`.
                # This avoids Windows-specific issues with process groups.
                return

        os.killpg = _killpg

    PostgreSQLExecutor.BASE_PROC_START_COMMAND = (
        '{executable} start -D "{datadir}" '
        '-o "-F -p {port} -c log_destination=stderr '
        "-c logging_collector=off "
        "-c unix_socket_directories={unixsocketdir} {postgres_options}\" "
        '-l "{logfile}" {startparams}'
    )


@pytest.fixture(scope='session')
def django_db_modify_db_settings(postgresql_proc):
    from django.db import connections
    from asgiref.local import Local

    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'bo2005ok',
        'HOST': postgresql_proc.host,
        'PORT': postgresql_proc.port,
        'ATOMIC_REQUESTS': True,
    }

    # pytest-django/Django may have already cached DB settings in the connection handler.
    connections._settings = None
    connections.__dict__.pop("settings", None)
    connections._connections = Local()
