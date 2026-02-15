# Grafana Dashboards (Provisioned)

This folder is mounted into the Grafana container at `/etc/grafana/dashboards` (read-only) via `docker-compose.infra.yml`.

## How it works

- Grafana provisions dashboards from JSON files under this directory.
- Provider config: `docker/grafana/provisioning/dashboards/dashboards.yml`
- By default dashboards appear under the **Wordloom** folder in Grafana.
- Dashboards auto-refresh from disk every ~10 seconds (see `updateIntervalSeconds`).

## Add / update a dashboard

1. Put a dashboard JSON file in this folder (example: `wordloom-outbox-bulk.json`).
2. If Grafana is running, it should pick up changes automatically within ~10 seconds.
   - If you changed provisioning YAML (not just JSON), restart the Grafana container.

## Open Grafana

- URL: `http://localhost:3000`
- Default credentials (from compose): `admin` / `admin`

## Open Prometheus

- URL: `http://localhost:9090`

## Start monitoring stack

From repo root:

- `docker compose -f docker-compose.infra.yml --profile monitoring up -d`

If you want only Elasticsearch (no monitoring):

- `docker compose -f docker-compose.infra.yml up -d es`
