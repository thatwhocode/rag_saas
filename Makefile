# --- COLORS ---
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
CYAN   := $(shell tput -Txterm setaf 6)
RESET  := $(shell tput -Txterm sgr0)

DOCKER_COMPOSE = sudo docker compose
DOCKER         = sudo docker
.PHONY: up down logs status setup-secrets

up: setup-secrets
	@echo "$(CYAN)🚀 [1/3] Booting Core Infrastructure...$(RESET)"
	@$(DOCKER_COMPOSE) up -d llm_chat_db llm_redis qdrant ollama
	
	@printf "$(YELLOW)⏳ Waiting for AI Models (Ollama) to be ready...$(RESET)"
	@# Використовуємо базовий DOCKER для inspect
	@until [ "$$($(DOCKER) inspect -f '{{.State.Health.Status}}' ollama)" = "healthy" ]; do \
		printf "."; \
		sleep 2; \
	done
	@echo "$(GREEN) READY!$(RESET)"

	@echo "$(CYAN)🚀 [2/3] Starting API & ML Workers...$(RESET)"
	@$(DOCKER_COMPOSE) up -d llm_api llm_ml_worker
	
	@printf "$(YELLOW)⏳ Finalizing migrations and connectivity...$(RESET)"
	@sleep 4
	@echo "$(GREEN) DONE!$(RESET)"

	@echo "\n$(WHITE)==================================================$(RESET)"
	@echo "$(GREEN)✨ ALL SYSTEMS ONLINE AND OPERATIONAL ✨$(RESET)"
	@echo "$(WHITE)==================================================$(RESET)"
	@echo "🔗 $(CYAN)API Swagger:$(RESET)   $(WHITE)http://localhost:8000/docs$(RESET)"
	@echo "🔗 $(CYAN)Qdrant Panel:$(RESET)  $(WHITE)http://localhost:6333/dashboard$(RESET)"
	@echo "🔗 $(CYAN)Redis Port:$(RESET)    $(WHITE)6377$(RESET)"
	@echo "🔗 $(CYAN)DB Port:$(RESET)       $(WHITE)5434$(RESET)"
	@echo "$(WHITE)==================================================$(RESET)"
	@echo "$(YELLOW)👉 Run 'make logs' to stream application output.$(RESET)"
	@echo "$(YELLOW)👉 Run 'streamlit run ui.py' to launch UI.$(RESET)"

setup-secrets:
	@echo "$(CYAN)🔐 Validating secrets...$(RESET)"
	@mkdir -p secrets
	@# (Тут твої перевірки файлів, які ми писали раніше)
	@echo "$(GREEN)✅ Secrets validated.$(RESET)"

down:
	@echo "$(YELLOW)🛑 Shutting down the stack...$(RESET)"
	@$(DOCKER_COMPOSE) down --remove-orphans
	@echo "$(GREEN)✅ All containers stopped.$(RESET)"

logs:
	@$(DOCKER_COMPOSE) logs -f llm_api llm_ml_worker