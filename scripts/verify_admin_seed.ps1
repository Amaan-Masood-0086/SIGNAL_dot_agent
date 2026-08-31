# Verify dev DB state after migration 0003 + admin seed.
$ErrorActionPreference = 'Stop'
$sql = "select (select count(id) from staff where email='root@signal.example') as admins, (select count(id) from usage_log) as usage_rows, (select version_num from alembic_version) as rev, (select count(id) from audit_log) as audit_rows, (select count(sequence) from audit_log a where a.action='staff.seed_admin') as seed_events;"
docker exec signal_dot_agent-db-1 psql -U signal -d signal_dev -t -c $sql
