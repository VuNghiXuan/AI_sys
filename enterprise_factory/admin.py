# File: enterprise_factory/admin.py
from django.contrib import admin
from .models import (
    Company, AgentRegistry, DirectiveLog, 
    AgentDiscussion, CodePatchProposal, ProjectNode
)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at')

@admin.register(AgentRegistry)
class AgentRegistryAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'display_name', 'role_type', 'version')
    list_filter = ('role_type',)

@admin.register(DirectiveLog)
class DirectiveLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'directive_text', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(AgentDiscussion)
class AgentDiscussionAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'phase', 'created_at')
    list_filter = ('phase',)

@admin.register(CodePatchProposal)
class CodePatchProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_file', 'proposed_by_agent', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = ('path', 'line_count', 'created_by_agent', 'updated_at')