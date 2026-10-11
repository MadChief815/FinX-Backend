from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dashboard
from .serializers import DashboardSerializer
from .services import build_dashboard_summary


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get_dashboard(self, user):
        dashboard, _ = Dashboard.objects.get_or_create(user=user)
        return dashboard

    def get(self, request):
        dashboard = self.get_dashboard(request.user)
        return Response(build_dashboard_summary(dashboard))

    def patch(self, request):
        dashboard = self.get_dashboard(request.user)
        serializer = DashboardSerializer(
            dashboard,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(build_dashboard_summary(dashboard))
