# PROJECT MAP & CODE KNOWLEDGE GRAPH - VNXBOX ENTERPRISE
# Tự động quét và cập nhật lần cuối: 09:01:38 ngày 15/11/2026
# Quản lý bởi: Ký ức Sâu Mã nguồn (Code Graph & Incremental Memory)

## 📁 1. Sơ đồ Cấu trúc Thư mục & Chi tiết Mã nguồn

  - `0001_initial.py` *(Classes: Migration)*
  - `__init__.py`
  - `_chat_stream copy.html`
  - `_chat_stream.html`
  - `_input_bar.html`
  - `_sidebar_agents.html`
  - `admin.py` *(Classes: SystemConfigAdmin, CompanyAdmin, AgentRoleAdmin, AgentRegistryAdmin, JobOpeningAdmin, DirectiveLogAdmin, AgentDiscussionAdmin, CodePatchProposalAdmin, AgentTaskDAGAdmin, ProjectNodeAdmin, IntentMemoryAdmin, ToolRegistryAdmin, WorkflowBlueprintAdmin)*
  - `agent.py` *(Classes: AgentRole, AgentRegistry, JobOpening)*
  - `apps.py` *(Classes: EnterpriseFactoryConfig, Funcs: ready)*
  - `asgi.py`
  - `ast_scanner.py` *(Classes: ASTCodeScanner, Funcs: scan_file, scan_project)*
  - `base.html`
  - `base.py` *(Classes: SystemConfig, Company, Meta, Meta)*
  - `chat_handler.py` *(Classes: ChatHandlerConsumer)*
  - `client.py` *(Funcs: ask_local_agent)*
  - `config_loader.py` *(Classes: ModelHardwareInspector, Funcs: get_active_hardware_profile, get_dynamic_ollama_options, get_model_endpoint_and_name)*
  - `dag_executor.py` *(Classes: DAGTaskEngine, Funcs: decompose_and_create)*
  - `dashboard.py` *(Funcs: war_room_dashboard)*
  - `directive_api.py` *(Funcs: api_submit_directive, api_viber_execute_directive, api_init_war_room_data)*
- **`dynamic_app/`**
- **`enterprise_factory/`**
  - **`consumers/`**
  - **`management/`**
    - **`commands/`**
  - **`migrations/`**
  - **`models/`**
  - **`services/`**
    - **`orchestrator/`**
  - **`static/`**
    - **`enterprise_factory/`**
      - **`js/`**
  - **`utils/`**
  - **`views/`**
  - `hr_spawner.py` *(Classes: HRSpawner, Funcs: spawn_agent_if_needed)*
  - `intent_cache_middleware.py` *(Classes: IntentCacheMiddleware, Funcs: get_cached_response, save_to_cache)*
  - `intent_router.py` *(Classes: IntentRouter, Funcs: classify_user_intent, route, classify)*
  - `knowledge.py` *(Classes: ProjectNode, IntentMemory)*
  - `long_prompt_handler.py` *(Classes: LongPromptHandler, Funcs: chunk_spec_by_headers)*
  - `manage.py` *(Funcs: main)*
  - `memory_loader.py` *(Classes: MemoryLoaderMixin, Funcs: save_and_get_context, get_historical_context_summary, save_intent_memory)*
  - `models_gen.py` *(Classes: PhieuNhapVangNguyenLieu, ItemLine, Funcs: save, save)*
  - `patch_api.py` *(Funcs: api_viber_approve_patch, api_viber_reject_patch)*
  - `reset_system.py` *(Funcs: clean_migrations, clean_database)*
  - `routing.py`
  - `runner.py` *(Funcs: execute_agent_task)*
  - `sandbox.py` *(Classes: SandboxExecutionError, PythonSandbox, Funcs: execute, target_execution)*
  - `scan_project_map.py` *(Funcs: parse_python_file, scan_codebase, generate_markdown_map, build_tree)*
  - `semantic_router.py` *(Classes: HybridSemanticRouter, Funcs: tokenize, get_term_frequency, cosine_similarity, semantic_match, route)*
  - `services_gen.py`
  - `settings.py`
  - `state_api.py` *(Funcs: api_viber_state, war_room_init_data, api_war_room_feedback)*
  - `sync_code_graph.py` *(Classes: Command, Funcs: handle)*
  - `system_bootstrap.py` *(Classes: SystemBootstrapEngine, Funcs: run_full_bootstrap)*
- **`templates/`**
  - **`enterprise_factory/`**
    - **`components/`**
  - `tests.py`
  - `ui_component_gen.html`
  - `urls.py`
- **`vnxbox_core/`**
  - `war_room.html`
  - `war_room.js`
  - `web_search.py` *(Funcs: search_web)*
  - `workflow.py` *(Classes: DirectiveLog, AgentDiscussion, CodePatchProposal, AgentTaskDAG, ToolRegistry, WorkflowBlueprint, Funcs: get_sender_display_name)*
  - `wsgi.py`

## 🧠 2. Các Thành Phần Trọng Tâm Đã Định Hình
- **HybridSemanticRouter** (`enterprise_factory/services/semantic_router.py`): Định tuyến 3 tầng + Cosine Similarity.
- **ChatHandlerConsumer** (`enterprise_factory/consumers/chat_handler.py`): Xử lý WebSocket & Map-Reduce spec dài.
- **LongPromptHandler** (`enterprise_factory/services/long_prompt_handler.py`): Hierarchical Chunker cho đặc tả 10k ký tự.

## 🔒 3. Trạng thái Môi trường & Phần cứng
- **Model LLM:** `qwen2.5-coder:7b-instruct` (Ollama local, port 11434).
- **Core Pinning:** `OLLAMA_NUM_THREAD=10`, `OLLAMA_KEEP_ALIVE=-1`.
- **Database:** SQLite (`db.sqlite3`).