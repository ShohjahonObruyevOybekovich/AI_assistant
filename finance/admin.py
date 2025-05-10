from django.contrib import admin

from finance.models import FinanceAction


# Register your models here.
@admin.register(FinanceAction)
class FinanceActionAdmin(admin.ModelAdmin):
    list_display = ('get_user_full_name', "action", "amount", "currency", "created_at")
    list_filter = ('action',)
    search_fields = ['user__full_name', "action", "amount", "currency", "created_at"]

    def get_user_full_name(self, obj):
        return obj.user.full_name if obj.user else "-"
    get_user_full_name.short_description = "Foydalanuvchi"
