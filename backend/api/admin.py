from django.contrib import admin

from .models import AIAnalysisRecord, CommunityComment, CommunityPost, OwnedCard, PurchasePlan, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'merchant_name', 'category', 'amount', 'card_id', 'approved_at')
    list_filter = ('category', 'card_id', 'is_cancelled')
    search_fields = ('public_id', 'merchant_name', 'address')


@admin.register(OwnedCard)
class OwnedCardAdmin(admin.ModelAdmin):
    list_display = ('card_id', 'nickname', 'display_order', 'created_at')
    search_fields = ('card_id', 'nickname')
    ordering = ('display_order', 'id')


@admin.register(PurchasePlan)
class PurchasePlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'plan_type', 'expense_mode', 'total_budget', 'status', 'created_at')
    list_filter = ('plan_type', 'expense_mode', 'status')
    search_fields = ('title',)


admin.site.register(CommunityPost)
admin.site.register(CommunityComment)
admin.site.register(AIAnalysisRecord)
