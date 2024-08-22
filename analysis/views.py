# analysis/views.py

import os
import pandas as pd
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import Group
from rest_framework import permissions, viewsets
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.contrib.auth.views import PasswordChangeView

from .models import UserInfo, GaitAnalysis, PoseAnalysis
from .forms import UploadFileForm, CustomPasswordChangeForm
from .serializers import GroupSerializer, UserSerializer, GaitAnalysisSerializer, PoseAnalysisSerializer

def home(request):
    if request.user.is_authenticated:
        return redirect('upload_file')
    else:
        return redirect('login')

@login_required
def upload_file(request):
    users = []  # Initialize an empty list to hold user data

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            file_path = default_storage.save('temp.xlsx', excel_file)
            full_path = os.path.join(settings.MEDIA_ROOT, 'temp.xlsx')

            # Read the Excel file
            df = pd.read_excel(full_path)
            
            for _, row in df.iterrows():
                try:
                    # Find or create the UserInfo
                    user_info, created = UserInfo.objects.update_or_create(
                        username=row['username'].replace(' ', ''),
                        phone=row['phone'],
                        defaults=dict(
                            school=row['school'],
                            class_name=row['class'],
                            student_number=row['number'],
                            password=make_password(os.environ['DEFAULT_PASSWORD'])
                        ),
                    )

                    users.append(user_info)

                except IntegrityError:
                    # Handle potential duplicate entry errors gracefully
                    pass

            # Cleanup
            default_storage.delete(file_path)

            return render(request, 'upload.html', {
                'form': form,
                'users': users
            })
    else:
        form = UploadFileForm()
    
    return render(request, 'upload.html', {'form': form})

@login_required
def report(request):
    grades = UserInfo.objects.values_list('class_name', flat=True).distinct()
    if request.method == 'POST':
        selected_grade = request.POST.get('grade')
        users = UserInfo.objects.filter(class_name=selected_grade)
    else:
        users = UserInfo.objects.none()
        selected_grade = None
    return render(request, 'report.html', {'grades': grades, 'users': users, 'selected_grade': selected_grade})

def policy(request):
    return render(request, 'policy.html')


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = UserInfo.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class GaitAnalysisViewSet(viewsets.ModelViewSet):
    queryset = GaitAnalysis.objects.all().order_by('-created_at')
    serializer_class = GaitAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        try:
            # Ensure the user has a corresponding UserInfo instance
            user_info = UserInfo.objects.get(username=user.username)
        except UserInfo.DoesNotExist:
            return Response({"detail": "UserInfo does not exist for the current user."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Save the GaitAnalysis instance with the associated UserInfo
        serializer.save(user=user_info)

    def get_queryset(self):
        # Filter the queryset to show only entries for the current user
        return GaitAnalysis.objects.filter(user__username=self.request.user.username).order_by('-created_at')
    
class PoseAnalysisViewSet(viewsets.ModelViewSet):
    queryset = PoseAnalysis.objects.all().order_by('-created_at')
    serializer_class = PoseAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter the queryset to show only entries for the current user
        return PoseAnalysis.objects.filter(user__username=self.request.user.username).order_by('-created_at')
    
class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'password_change.html'
    success_url = '/password-change-done/'