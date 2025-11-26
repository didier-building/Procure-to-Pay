from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PurchaseRequest(models.Model):
    """Purchase Request model - exactly as specified in original requirements"""
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    # Core fields from original spec
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    
    # User relationships
    created_by = models.ForeignKey(
        User, related_name="created_requests", on_delete=models.CASCADE
    )
    approved_by = models.ForeignKey(
        User,
        related_name="approved_requests", 
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # File uploads - as specified in original requirements
    proforma = models.FileField(upload_to="proformas/", null=True, blank=True)
    purchase_order = models.FileField(upload_to="purchase_orders/", null=True, blank=True)
    receipt = models.FileField(upload_to="receipts/", null=True, blank=True)
    
    # AI processing data storage - for document processing feature
    proforma_data = models.JSONField(null=True, blank=True, help_text="AI-extracted data from proforma")
    purchase_order_data = models.JSONField(null=True, blank=True, help_text="Generated PO data")
    receipt_validation_data = models.JSONField(null=True, blank=True, help_text="Receipt validation results")
    po_generated_at = models.DateTimeField(null=True, blank=True, help_text="When PO was generated")

    def __str__(self):
        return f"{self.title} ({self.status})"


class Approval(models.Model):
    LEVEL_CHOICES = [
        (1, "Level 1 Approver"),
        (2, "Level 2 Approver"),
    ]

    request = models.ForeignKey(
        PurchaseRequest, related_name="approvals", on_delete=models.CASCADE
    )
    approver = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    level = models.IntegerField(choices=LEVEL_CHOICES)
    approved = models.BooleanField(null=True)  # True=approved, False=rejected, None=pending
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("request", "level")
        constraints = [
            models.CheckConstraint(
                check=models.Q(approved__in=[True, False]),
                name='valid_approval_status'
            )
        ]

    def __str__(self):
        return f"Request {self.request.id} | Level {self.level} | {self.approved}"


class RequestItem(models.Model):
    """Optional RequestItem model - mentioned in original spec as optional"""
    request = models.ForeignKey(
        PurchaseRequest, related_name="items", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.name} ({self.quantity} x {self.unit_price})"
