from django.db import transaction
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import PurchaseRequest, Approval
from .serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
    ApproveRequestSerializer,
    RejectRequestSerializer,
    ReceiptUploadSerializer,
)

class PurchaseRequestViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequest.objects.all().select_related('created_by')
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseRequestCreateSerializer
        if self.action in ['update', 'partial_update']:
            return PurchaseRequestUpdateSerializer
        return PurchaseRequestSerializer

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and getattr(profile, 'role', None) == 'staff':
            return self.queryset.filter(created_by=user).order_by('-created_at')
        return self.queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        user = request.user
        profile = getattr(user, 'profile', None)
        if not profile or not str(profile.role).startswith('approver'):
            return Response({"detail":"Not authorized to approve."}, status=status.HTTP_403_FORBIDDEN)

        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = ApproveRequestSerializer(data=request.data, context={'purchase_request': pr})
        serializer.is_valid(raise_exception=True)

        level = 1 if profile.role == 'approver1' else 2

        with transaction.atomic():
            pr_locked = PurchaseRequest.objects.select_for_update().get(pk=pr.pk)
            if pr_locked.status != 'PENDING':
                return Response({"detail":"Cannot approve non-pending request."}, status=status.HTTP_400_BAD_REQUEST)
            Approval.objects.create(request=pr_locked, approver=user, level=level, approved=True, comment=request.data.get('comment',''))
            if level == 2:
                pr_locked.status = 'APPROVED'
                pr_locked.final_approved_by = user
                pr_locked.save()
                # TODO: generate PO sync/async (placeholder)
                return Response({"status":"APPROVED"}, status=status.HTTP_200_OK)
            return Response({"status":"PENDING", "message":"Level 1 approved; awaiting final approval."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        user = request.user
        profile = getattr(user, 'profile', None)
        if not profile or not str(profile.role).startswith('approver'):
            return Response({"detail":"Not authorized to reject."}, status=status.HTTP_403_FORBIDDEN)

        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = RejectRequestSerializer(data=request.data, context={'purchase_request': pr})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            pr_locked = PurchaseRequest.objects.select_for_update().get(pk=pr.pk)
            if pr_locked.status != 'PENDING':
                return Response({"detail":"Cannot reject non-pending request."}, status=status.HTTP_400_BAD_REQUEST)
            lvl = 1 if profile.role == 'approver1' else 2
            Approval.objects.create(request=pr_locked, approver=user, level=lvl, approved=False, comment=request.data.get('comment',''))
            pr_locked.status = 'REJECTED'
            pr_locked.save()
            return Response({"status":"REJECTED"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='submit-receipt')
    def submit_receipt(self, request, pk=None):
        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = ReceiptUploadSerializer(instance=pr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # TODO: run receipt validation/extraction here or queue async
        return Response({"status":"RECEIPT_UPLOADED"}, status=status.HTTP_200_OK)
