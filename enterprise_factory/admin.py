# File: enterprise_factory/admin.py
"""
Quản lý giao diện Django Admin cho toàn bộ hệ thống vnxBox Enterprise.
"""

import logging
from django.contrib import admin
from enterprise_factory.models import (
    SystemConfig, Company, AgentRole, AgentRegistry, JobOpening,
    DirectiveLog, AgentDiscussion, CodePatchProposal, AgentTaskDAG,
    ProjectNode, IntentMemory, ToolRegistry, WorkflowBlueprint
)

logger = logging.getLogger(__name__)

# Đăng ký các Model lên trang quản trị Django Admin
@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'description')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    search_fields = ('code', 'name')

@admin.register(AgentRole)
class AgentRoleAdmin(admin.ModelAdmin):
    list_display = ('role_code', 'role_name')
    search_fields = ('role_code', 'role_name')

@admin.register(AgentRegistry)
class AgentRegistryAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'display_name', 'title_name', 'role', 'version')
    search_fields = ('agent_id', 'display_name')
    list_filter = ('role',)

@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('id', 'position_title', 'required_domain', 'status', 'created_at')
    search_fields = ('position_title', 'required_domain')
    list_filter = ('status',)

@admin.register(DirectiveLog)
class DirectiveLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(AgentDiscussion)
class AgentDiscussionAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'sender_type', 'agent', 'phase', 'created_at')
    list_filter = ('sender_type', 'phase')

@admin.register(CodePatchProposal)
class CodePatchProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_file', 'proposed_by_agent', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(AgentTaskDAG)
class AgentTaskDAGAdmin(admin.ModelAdmin):
    list_display = ('id', 'directive', 'step_order', 'step_name', 'assigned_agent', 'status')
    list_filter = ('status',)

@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = ('path', 'line_count', 'updated_at')
    search_fields = ('path',)
    list_filter = ('line_count',)

@admin.register(IntentMemory)
class IntentMemoryAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'intent_code', 'target_agent', 'tier', 'feedback_type')
    search_fields = ('query_text', 'intent_code')

@admin.register(ToolRegistry)
class ToolRegistryAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'display_name', 'is_active', 'created_at')
    search_fields = ('tool_name', 'display_name', 'description')
    list_filter = ('is_active', 'created_at')


@admin.register(WorkflowBlueprint)
class WorkflowBlueprintAdmin(admin.ModelAdmin):
    list_display = ('workflow_code', 'workflow_name', 'is_active', 'created_at')
    search_fields = ('workflow_code', 'workflow_name')
    list_filter = ('is_active', 'created_at')