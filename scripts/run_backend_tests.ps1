# Run the backend suite against real PostgreSQL (SIGNAL tests never use SQLite).
$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\backend"
$env:SIGNAL_TEST_DATABASE_URL = 'postgresql+psycopg://signal:signal_dev_only@localhost:5432/signal_dev'
# TEST-ONLY Fernet key for ADR-10's required CREDENTIAL_ENCRYPTION_KEY.
# Generated with Fernet.generate_key(); it encrypts nothing real (throwaway
# test databases only) and is committed on purpose so the suite is
# reproducible — never reuse it outside tests.
$env:CREDENTIAL_ENCRYPTION_KEY = 'MeogHhAdoVZ279u9hf3BlSQxH3rqq89e538bAoC8tQg='
# -ra: report xfail/skip reasons in the summary so known-divergence
# markers (e.g. T6/R14) stay visibly flagged in every run.
& .\.venv\Scripts\python.exe -m pytest -q -ra @args
exit $LASTEXITCODE
