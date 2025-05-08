from django.contrib import admin

from finance.models import FinanceAction


# Register your models here.
@admin.register(FinanceAction)
class FinanceActionAdmin(admin.ModelAdmin):
    list_display = ('user__full_name',"action_type","amount","currency","date")
    list_filter = ('action_type',)
    search_fields = ['user__full_name',"action_type","amount","currency","date"]