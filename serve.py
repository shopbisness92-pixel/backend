import os
import sys
from django.core.management import execute_from_command_line

# --------------------------------------------------
# Set Django settings
# --------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "escc_backend.settings")

# --------------------------------------------------
# Run server on all interfaces
# --------------------------------------------------
execute_from_command_line([sys.argv[0], "runserver", "0.0.0.0:8000"])
