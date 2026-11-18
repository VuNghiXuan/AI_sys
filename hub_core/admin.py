from django.contrib import admin
from .models import AgentManifestModel, RequestJob, TaskExecutionLog

admin.site.register(AgentManifestModel)
admin.site.register(RequestJob)
admin.site.register(TaskExecutionLog)