"""Os testes usam um banco separado, para nunca apagarem o banco de trabalho."""

import os

os.environ.setdefault("RADAR_BANCO_URL", "postgresql://localhost:5433/radar_goias_teste")
