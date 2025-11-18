#!/usr/bin/env bash

export NEO4J_URI=bolt://localhost:17687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password

# Reinitialize database for clean test state
echo "Reinitializing database..."
docker exec -i neo4j44 cypher-shell -u neo4j -p password --encryption=false < cypher_init.cypher > /dev/null 2>&1

# Run tests
echo "Running tests..."
python3.11 -m pytest test_scoring.py test_graph_model.py test_agent_runtime.py "$@"
