# Run the backend suite against real PostgreSQL (SIGNAL tests never use SQLite).
$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\backend"
$env:SIGNAL_TEST_DATABASE_URL = 'postgresql+psycopg://signal:signal_dev_only@localhost:5432/signal_dev'
# -ra: report xfail/skip reasons in the summary so known-divergence
# markers (e.g. T6/R14) stay visibly flagged in every run.
& .\.venv\Scripts\python.exe -m pytest -q -ra @args
exit $LASTEXITCODE
