from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PurchaseRequest, Approval, RequestItem

User = get_user_model()


class RequestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ["id", "name", "quantity", "unit_price"]


class ApprovalSerializer(serializers.ModelSerializer):
    approver = serializers.StringRelatedField()

    class Meta:
        model = Approval
        fields = ["id", "approver", "level", "approved", "comment", "created_at"]


class PurchaseRequestSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    items = RequestItemSerializer(many=True, read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    final_approved_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            "id",
            "title",
            "description",
            "amount",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "proforma",
            "purchase_order",
            "receipt",
            "final_approved_by",
            "items",
            "approvals",
            # New AI processing fields
            "department",
            "urgency", 
            "justification",
            "proforma_data",
            "purchase_order_data",
            "receipt_validation_data",
            "po_generated_at",
        ]


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    items = RequestItemSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = ["title", "description", "amount", "proforma", "items", "department", "urgency", "justification"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        user = self.context["request"].user
        pr = PurchaseRequest.objects.create(created_by=user, **validated_data)
        for item in items_data:
            RequestItem.objects.create(request=pr, **item)
        return pr


class PurchaseRequestUpdateSerializer(serializers.ModelSerializer):
    items = RequestItemSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = ["title", "description", "amount", "proforma", "items", "department", "urgency", "justification"]

    def validate(self, data):
        if self.instance.status != "PENDING":
            raise serializers.ValidationError("Only pending requests can be updated.")
        return data

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.items.all().delete()
        for item in items_data:
            RequestItem.objects.create(request=instance, **item)
        return instance


class ApproveRequestSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        pr = self.context.get("purchase_request")
        if pr.status != "PENDING":
            raise serializers.ValidationError("Request is not pending.")
        return data


class RejectRequestSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        pr = self.context.get("purchase_request")
        if pr.status != "PENDING":
            raise serializers.ValidationError("Request is not pending.")
        return data


class ReceiptUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequest
        fields = ["receipt"]

    def validate(self, data):
        if self.instance.status != "APPROVED":
            raise serializers.ValidationError("Receipt can only be submitted for approved requests.")
        return data
