from django.contrib import admin
from .models import Debt
# Register your models here.
@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ["user__full_name","target_person","type","amount","currency"]
    list_filter = ["type"]
    search_fields = ["user__full_name","target_person"]