# File: enterprise_factory/admin.py
from django.contrib import admin
from .models import Company, AgentRole, AgentRegistry, DirectiveLog, AgentTaskDAG, AgentDiscussion, CodePatchProposal

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at')

@admin.register(AgentRole)
class AgentRoleAdmin(admin.ModelAdmin):
    list_display = ('role_code', 'role_name', 'created_at')
    search_fields = ('role_code', 'role_name')

@admin.register(AgentRegistry)
class AgentRegistryAdmin(admin.ModelAdmin):
    # Đã sửa 'role_type' thành 'role' cho khớp với model mới
    list_display = ('agent_id', 'display_name', 'role', 'domain_scope', 'risk_threshold', 'version')
    list_filter = ('role', 'risk_threshold', 'company')
    search_fields = ('agent_id', 'display_name', 'domain_scope')

@admin.register(DirectiveLog)
class DirectiveLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'status', 'created_at')
    list_filter = ('status', 'company')

@admin.register(AgentTaskDAG)
class AgentTaskDAGAdmin(admin.ModelAdmin):
    list_display = ('id', 'directive', 'assigned_agent', 'step_order', 'step_name', 'status')
    list_filter = ('status', 'assigned_agent')

@admin.register(AgentDiscussion)
class AgentDiscussionAdmin(admin.ModelAdmin):
    list_display = ('id', 'directive', 'agent', 'phase', 'created_at')
    list_filter = ('phase', 'agent')

@admin.register(CodePatchProposal)
class CodePatchProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at')
    list_filter = ('status', 'created_at')