.PHONY: help install neo4j-start neo4j-stop neo4j-restart neo4j-status neo4j-logs neo4j-shell clean

# --- Configuration ---
CONTAINER_NAME ?= neo4j44
NEO4J_USER ?= neo4j
NEO4J_PASS ?= password
HTTP_PORT ?= 17474
BOLT_PORT ?= 17687

help: ## Show this help message
	@echo "MacGyver Active Inference Demo - Make targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

neo4j-start: ## Start Neo4j container with APOC
	@bash scripts/dev_neo4j_demo.sh

neo4j-stop: ## Stop and remove Neo4j container
	@echo "==> Stopping Neo4j container..."
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "==> Neo4j stopped"

neo4j-restart: neo4j-stop neo4j-start ## Restart Neo4j container

neo4j-status: ## Check Neo4j container status
	@docker ps -a | grep $(CONTAINER_NAME) || echo "Container $(CONTAINER_NAME) not found"

neo4j-logs: ## View Neo4j container logs
	@docker logs -f $(CONTAINER_NAME)

neo4j-shell: ## Open cypher-shell in Neo4j container
	@docker exec -it $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false

neo4j-query: ## Run a quick test query (verify connection)
	@docker exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PASS) --encryption=false \
		"RETURN 'Connected!' AS status, datetime() AS timestamp"

clean: neo4j-stop ## Stop Neo4j and clean up
	@echo "==> Cleaning up..."
	@rm -rf __pycache__ .pytest_cache *.pyc
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "==> Clean complete"
	@echo "Note: To remove .neo4j44/ (if exists), run: sudo rm -rf .neo4j44/"

# --- Development targets ---
dev-init: install neo4j-start ## Initialize development environment
	@echo ""
	@echo "==> Development environment ready!"
	@echo "    Neo4j Browser: http://localhost:$(HTTP_PORT)"
	@echo "    Bolt:          bolt://localhost:$(BOLT_PORT)"
	@echo "    Credentials:   $(NEO4J_USER) / $(NEO4J_PASS)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make neo4j-shell' to interact with Neo4j"
	@echo "  2. Create cypher_init.cypher to initialize your graph"
	@echo "  3. Run 'python runner.py' when ready"
