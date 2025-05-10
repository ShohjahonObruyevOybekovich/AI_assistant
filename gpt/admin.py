from django.contrib import admin

from gpt.models import GptSession, GptMessage


# Register your models here.
@admin.register(GptSession)
class GptSessionAdmin(admin.ModelAdmin):
    pass

@admin.register(GptMessage)
class GptMessageAdmin(admin.ModelAdmin):
    pass