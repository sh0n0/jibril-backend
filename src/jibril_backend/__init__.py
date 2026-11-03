import os
import sys


def main() -> None:
    """Run Django administrative tasks (the `jibril-backend` console script)."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jibril_backend.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
