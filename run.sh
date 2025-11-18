#!/usr/bin/env bash
# Wrapper script to run MacGyver demo with correct Neo4j connection settings
# This ensures the demo uses the Docker Neo4j instance on port 17687

export NEO4J_URI=bolt://localhost:17687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password

python3.11 runner.py "$@"
