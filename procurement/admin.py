from django.contrib import admin
from .models import PurchaseRequest, RequestItem, Approval

class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 0

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id','title','status','created_by','amount','created_at')
    inlines = [RequestItemInline]
    readonly_fields = ('purchase_order',)

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('id','request','approver','level','approved','created_at')
