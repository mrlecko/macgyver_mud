#!/usr/bin/env bash
set -Eeuo pipefail

# --- MacGyver Active Inference Demo - Neo4j Setup -------------------------------
# This script starts a Neo4j 4.4 instance with APOC for the demo

# --- Config (override via env if needed) ----------------------------------------
CONTAINER_NAME="${CONTAINER_NAME:-neo4j44}"
IMAGE="${IMAGE:-neo4j:4.4}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASS="${NEO4J_PASS:-password}"
HTTP_PORT="${HTTP_PORT:-17474}"
BOLT_PORT="${BOLT_PORT:-17687}"

# --- Helpers --------------------------------------------------------------------
say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

# --- Robust Bolt wait: retry until ready ---------------------------------------
bolt_wait() {
  say "Waiting for Bolt to be ready (may take 30-60 seconds)..."
  local tries=0
  while true; do
    if docker exec "$CONTAINER_NAME" cypher-shell \
        -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false \
        "RETURN 1 AS ok" >/dev/null 2>&1; then
      say "Neo4j is ready!"
      return 0
    fi
    tries=$((tries+1))
    if [ "$tries" -ge 120 ]; then
      die "Neo4j did not become ready in 120 seconds."
    fi
    sleep 1
  done
}

# --- Cypher helper --------------------------------------------------------------
cypher() {
  docker exec "$CONTAINER_NAME" cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false "$@"
}

# --- Start fresh container ------------------------------------------------------
say "Stopping/removing any old container: $CONTAINER_NAME"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

say "Starting $IMAGE with APOC enabled"
docker run -d --name "$CONTAINER_NAME" \
  -p "${HTTP_PORT}:7474" -p "${BOLT_PORT}:7687" \
  -e NEO4J_AUTH="${NEO4J_USER}/${NEO4J_PASS}" \
  -e NEO4JLABS_PLUGINS='["apoc"]' \
  -e NEO4J_dbms_security_procedures_allowlist='apoc.*' \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_export_file_enabled=true \
  "$IMAGE" >/dev/null

bolt_wait

# --- Check APOC -----------------------------------------------------------------
say "Verifying APOC availability..."
cypher "RETURN apoc.version() AS apoc_version;"

# --- Initialize graph (if cypher_init.cypher exists) ----------------------------
if [ -f "cypher_init.cypher" ]; then
  say "Loading initial graph from cypher_init.cypher..."
  docker exec -i "$CONTAINER_NAME" cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASS" --encryption=false \
    < cypher_init.cypher || say "Warning: cypher_init.cypher failed or doesn't exist"
else
  say "No cypher_init.cypher found - skipping graph initialization"
fi

# --- Done -----------------------------------------------------------------------
say "Done! Access Neo4j at:"
say "  Browser: http://localhost:${HTTP_PORT}"
say "  Bolt:    bolt://localhost:${BOLT_PORT}"
say "  User:    $NEO4J_USER / Pass: $NEO4J_PASS"
