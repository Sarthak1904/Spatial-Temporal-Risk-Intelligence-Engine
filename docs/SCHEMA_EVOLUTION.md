# Schema Evolution

- Use Alembic for all DDL changes
- Never modify existing migrations; add new ones
- Test downgrade path before merging
