from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PurchaseRequest, Approval, RequestItem

User = get_user_model()


class RequestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ["id", "name", "quantity", "unit_price"]


class ApprovalSerializer(serializers.ModelSerializer):
    approved_by = serializers.CharField(source='approver.username', read_only=True)

    class Meta:
        model = Approval
        fields = ["id", "approved_by", "level", "approved", "comment", "created_at"]


class PurchaseRequestSerializer(serializers.ModelSerializer):
    """Main serializer for PurchaseRequest - matches original spec exactly"""
    created_by = serializers.StringRelatedField()
    approved_by = serializers.StringRelatedField(read_only=True)
    items = RequestItemSerializer(many=True, read_only=True)  # Optional from spec
    approvals = ApprovalSerializer(many=True, read_only=True)  # Optional from spec

    class Meta:
        model = PurchaseRequest
        fields = [
            "id",
            "title", 
            "description",
            "amount",
            "status",
            "created_by",
            "approved_by",
            "created_at", 
            "updated_at",
            "proforma",
            "purchase_order", 
            "receipt",
            "items",  # Optional
            "approvals",  # Optional
            # AI processing fields for document processing feature
            "proforma_data",
            "purchase_order_data",
            "receipt_validation_data",
        ]


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """Simple create serializer matching original requirements"""
    proforma = serializers.FileField(required=False)
    
    class Meta:
        model = PurchaseRequest  
        fields = ["title", "description", "amount", "proforma"]

    def create(self, validated_data):
        user = self.context["request"].user
        # Remove created_by from validated_data if it exists to avoid conflicts
        validated_data.pop('created_by', None)
        return PurchaseRequest.objects.create(created_by=user, **validated_data)


class PurchaseRequestUpdateSerializer(serializers.ModelSerializer):
    items = RequestItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseRequest
        fields = ["title", "description", "amount", "proforma", "items"]

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
