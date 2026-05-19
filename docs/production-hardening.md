# Production Hardening

## Environment validation before startup

Use the environment guard before bringing the stack up:

```bash
make check-env
```

`make up` runs this check automatically and blocks startup if
`GRAFANA_ADMIN_PASSWORD` is unset, empty, or a default value.

If the check fails, remediate with:

```bash
cp .env.example .env
$EDITOR .env
```
