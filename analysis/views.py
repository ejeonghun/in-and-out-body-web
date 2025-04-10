# analysis/views.py

import json
import os
import re
import uuid
import pandas as pd
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
import requests
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.views import PasswordChangeView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta

from rest_framework_simplejwt.authentication import JWTAuthentication

from .helpers import extract_digits, generate_presigned_url, parse_userinfo_kiosk, upload_image_to_s3, verify_image, \
    calculate_normal_ratio, create_excel_report, session_check_expired
from .models import BodyResult, CodeInfo, GaitResult, OrganizationInfo, SchoolInfo, UserInfo, SessionInfo, UserHist, \
    KioskInfo, GaitResult
from .forms import UploadFileForm, CustomPasswordChangeForm, CustomUserCreationForm, CustomPasswordResetForm
from .serializers import BodyResultSerializer, GaitResponseSerializer, GaitResultSerializer, UserInfoSerializer, \
    CodeInfoSerializer

from django.db.models import Min, Max, Exists, OuterRef, Count
from django.db.models.functions import ExtractYear
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from datetime import datetime as dt
from collections import defaultdict
from django.http import JsonResponse, HttpResponse
from urllib.parse import quote
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder

# 응답코드 관련
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, \
    HTTP_500_INTERNAL_SERVER_ERROR


def home(request):
    if request.user.is_authenticated:
        return redirect('main')
    else:
        return redirect('login')


from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.urls import reverse_lazy


@login_required
def main(request):  # 추후 캐싱 기법 적용
    user = request.user
    context = {}

    # 기관 등록 여부 확인
    has_affiliation = bool(user.school or user.organization)

    # 기관이 등록된 경우
    if has_affiliation:
        # 학교
        if user.user_type == 'S':
            # 유저 소속
            user_affil = user.school.school_name  # 유저 소속(학교이름)

            # 총 회원 수
            members = UserInfo.objects.filter(
                school__school_name=user.school.school_name
            ).count()

            # 체형 총 검사 수
            total_results = BodyResult.objects.filter(
                user__school__school_name=user.school.school_name,
                image_front_url__isnull=False,
                image_side_url__isnull=False
            ).count()

            # 이번달 검사 수
            current_month_results = BodyResult.objects.filter(
                user__school__school_name=user.school.school_name,
                image_front_url__isnull=False,
                image_side_url__isnull=False,
                created_dt__month=dt.now().month
            ).count()

            # 미완료 검사 수
            # 소속된 학교의 모든 사용자 중 검사를 받지 않은 사용자 수
            pending_tests = UserInfo.objects.filter(
                school__id=user.school.id,
                year=dt.now().year
            ).exclude(
                id__in=BodyResult.objects.filter(
                    user__school__id=user.school.id,
                    image_front_url__isnull=False,
                    image_side_url__isnull=False,
                    created_dt__year=dt.now().year
                ).values('user_id')
            ).count()

            # 학교의 그룹 정보 가져오기
            groups = UserInfo.objects.filter(
                school__school_name=user.school.school_name,
                year=dt.now().year
            ).values('student_grade', 'student_class').annotate(student_count=Count('id')).order_by('student_grade',
                                                                                                    'student_class')

            # 학년-반 별 구성원 수를 포함하는 딕셔너리 초기화
            group_structure = {}

            # 학년별로 반 정보 구조화 및 구성원 수 추가
            for group in groups:
                if group['student_grade'] and group['student_class']:  # None 값 제외
                    grade = str(group['student_grade'])
                    class_num = str(group['student_class'])

                    # 학년이 group_structure에 없으면 초기화
                    if grade not in group_structure:
                        group_structure[grade] = {}

                    # 반이 학년의 딕셔너리에 없으면 초기화
                    if class_num not in group_structure[grade]:
                        group_structure[grade][class_num] = 0  # 초기화

                    # 구성원 수 증가
                    group_structure[grade][class_num] = group['student_count']  # 쿼리에서 가져온 학생 수로 설정

        else:
            # 유저 소속 - 기관
            user_affil = user.organization.organization_name  # 유저 소속(기관이름)

            # 총 회원 수
            members = UserInfo.objects.filter(
                organization__id=user.organization.id
            ).count()

            # 체형 총 검사 수
            total_results = BodyResult.objects.filter(
                user__organization__id=user.organization.id,
                image_front_url__isnull=False,
                image_side_url__isnull=False
            ).count()

            # 이번달 체형 검사 수
            current_month_results = BodyResult.objects.filter(
                user__organization__organization_name=user.organization.organization_name,
                image_front_url__isnull=False,
                image_side_url__isnull=False,
                created_dt__month=dt.now().month
            ).count()

            # 보행 총 검사 수
            org_users = UserInfo.objects.filter(organization__id=user.organization.id)

            # for문을 순회하며 gait_result에 해당하는 user_id가 있는지 확인
            total_gait_results = GaitResult.objects.filter(
                user_id__in=org_users.values('id')
            ).count()

            # 미완료 검사 수
            # 소속된 기관의 모든 사용자 중 검사를 받지 않은 사용자 수(문제점 : 작년도 유저까지 포함될 수 있음 - 2023년 가입인데 2024년에 갱신이 안된 경우)
            # userInfo에서 organization__id=user.organization.id인 것 들 중에 BodyResult에 있는 user_id와 일치하지 않는 것들을 제외하고 count
            pending_tests = UserInfo.objects.filter(
                organization__id=user.organization.id
            ).exclude(
                id__in=BodyResult.objects.filter(
                    user_id=OuterRef('id'),
                    image_front_url__isnull=False,
                    image_side_url__isnull=False
                ).values('user_id')
            ).count()

            # 부서 : 구성원 수 구조화
            group_structure = UserInfo.objects.filter(
                organization__organization_name=user.organization.organization_name
            ).values('department').annotate(count=Count('id')).order_by('department')

            # None 결과(부서에 속해있지 않은) 제외한 딕셔너리로 변환
            group_structure = {item['department']: item['count'] for item in group_structure if
                               item['department'] is not None}

            # 검사 완료율 계산 (퍼센트)
            # test_completion_rate = ((members - pending_tests) / members * 100) if members > 0 else 0

        year = dt.now().year
        context.update({
            'user_affil': user_affil,
            'total_members': members,
            'total_results': total_results,
            'current_month_results': current_month_results,
            'user_type': user.user_type,
            'pending_tests': pending_tests,
            'group_structure': group_structure,
            'year': year,
            **({'total_gait_results': total_gait_results} if user.user_type == 'O' else {})  # 수정된 부분
        })

    context['has_affiliation'] = has_affiliation
    return render(request, 'main.html', context)


@login_required
def search_user(request):
    user_id = request.user.id
    user = UserInfo.objects.get(id=user_id)
    user_type = user.user_type

    query = request.GET.get('query', '')

    user_dept = user.school.school_name if user_type == 'S' else user.organization.organization_name

    if not query:
        return JsonResponse({'results': []})

    if user_type == 'S':  # 학교
        users = UserInfo.objects.filter(Q(student_name__icontains=query),
                                        Q(school__school_name__icontains=user_dept))  # 이름으로 검색

        results = [{'id': user.id, 'student_name': user.student_name, 'student_grade': user.student_grade,
                    'student_class': user.student_class} for user in users]

    elif user_type == 'O':
        users = UserInfo.objects.filter(Q(student_name__icontains=query),
                                        Q(organization__organization_name__icontains=user_dept))
        results = [{'id': user.id, 'student_name': user.student_name, 'department': user.department} for user in users]

    return JsonResponse({'results': results, 'user_type': user_type})


def org_register(request):
    return render(request, 'org_register.html')


@login_required
def member_register(request):
    existing_member = 0  # 기존 회원 카운팅
    new_member = 0  # 신규 회원 카운팅

    user_id = request.user.id
    user = UserInfo.objects.get(id=user_id)
    type = user.user_type

    if type not in ['S', 'O']:  # 'G' == 게스트(일반 사용자)
        return render(request, 'main.html', context={"message": "먼저 기관을 등록해주세요."})  # 'home' URL로 리디렉션

    orgName = user.organization.organization_name if user.organization else user.school.school_name  # 기관명(학교명) 가져오기

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['file']
                df = pd.read_excel(excel_file,
                                   dtype={'전화번호': str})  # 전화번호를 문자열로 읽음

                # 컬럼 검증
                expected_columns = ['학년', '반', '번호', '이름', '전화번호'] if type == 'S' else ['부서명', '이름', '전화번호']
                if not all(col in df.columns for col in expected_columns):
                    user_type_str = '교직원용' if type == 'S' else '일반 기관용'
                    raise ValueError(f"올바른 템플릿이 아닙니다. {user_type_str} 템플릿을 다운로드 받아서 다시 시도해주세요.")

                # NaN 값을 가진 행 제거
                df = df.dropna(subset=['이름', '전화번호'])  # 이름과 전화번호는 필수값으로 처리

                # 데이터 전처리
                users = []
                phone_numbers = df['전화번호'].unique()  # 중복 제거된 전화번호 리스트
                cleaned_phone_numbers = [extract_digits(phone_number) for phone_number in phone_numbers]  # 숫자만 추출
                existing_users = UserInfo.objects.filter(phone_number__in=cleaned_phone_numbers)  # DB에서 존재하는 전화번호 필터링
                expected_columns.append('상태')  # 상태 컬럼 추가
                other_org = None  # 다른 학교/기관 에 소속된 유저가 있는 경우 확인 용도

                df['상태'] = ''  # 상태 컬럼 초기화

                for _, row in df.iterrows():
                    user_data = {}

                    for col in expected_columns:
                        if pd.notna(row[col]):
                            # 숫자형 컬럼 처리
                            if col in ['학년', '번호'] and pd.notna(row[col]):
                                user_data[col] = str(int(row[col]))  # float를 int로 변환 후 문자열로
                            else:
                                user_data[col] = str(row[col]).strip()

                    if len(user_data) == len(expected_columns):  # 모든 필수 컬럼이 있는 경우만 추가
                        phone_number = cleaned_phone_numbers.pop(0)  # 맨 앞 요소를 꺼내고 리스트에서 제거
                        existing_user = existing_users.filter(phone_number=phone_number).first()

                        if existing_user:
                            existing_member += 1
                            # 존재하는 유저의 소속 정보 추가
                            if existing_user.school:  # 학교 소속이 있는 경우
                                if existing_user.school.school_name != orgName:  # 다른 학교에 소속된 경우
                                    user_data['상태'] = f"이전 학교 - {existing_user.school.school_name}"  # 이전 학교 정보 추가
                                    other_org = True  # 다른 학교에 소속된 경우
                                else:
                                    user_data['상태'] = '기존 유저 갱신'
                            else:
                                if existing_user.organization:  # 기관 소속이 있는 경우
                                    user_data[
                                        '상태'] = f'이전 소속 - {existing_user.organization.organization_name}'  # 이전 기관 정보 추가
                        else:  # 신규 등록인 경우 빈 문자열 설정
                            user_data['상태'] = '신규 등록'  # 신규 등록 상태 추가
                            new_member += 1

                        # 중복 추가 방지
                        if user_data not in users:
                            users.append(user_data)  # 사용자 데이터 추가

                # 저장 요청인 경우
                if request.POST.get('save') == 'true':
                    existing_member = 0;  # 기존 회원 초기화
                    new_member = 0;
                    with transaction.atomic():  # 트랜잭션 시작
                        for user_data in users:
                            phone_number = extract_digits(user_data['전화번호'])

                            if type == 'S':  # 학생인 경우
                                school_info = SchoolInfo.objects.get(school_name=user.school.school_name)

                                # 기존 사용자 확인 및 이력 저장
                                existing_user = UserInfo.objects.filter(phone_number=phone_number).first()
                                if existing_user:  # 기존 사용자가 있는 경우
                                    if existing_user.created_dt.year != dt.now().year or existing_user.year != dt.now().year:  # 작년도 사용자인 경우
                                        UserHist.objects.update_or_create(
                                            user=existing_user,
                                            school=existing_user.school,
                                            student_grade=existing_user.student_grade,
                                            student_class=existing_user.student_class,
                                            student_number=existing_user.student_number,
                                            student_name=existing_user.student_name,
                                            year=existing_user.year
                                        )
                                    existing_member += 1

                                new_member += 1
                                # 사용자 정보 업데이트 또는 생성
                                UserInfo.objects.update_or_create(
                                    phone_number=phone_number,
                                    defaults={
                                        'school': school_info,
                                        'student_grade': user_data['학년'],
                                        'student_class': user_data['반'],
                                        'student_number': user_data['번호'],
                                        'student_name': user_data['이름'],
                                        'username': phone_number,
                                        'password': make_password(os.environ['DEFAULT_PASSWORD']),
                                        'user_type': type,
                                        'user_display_name': f"{school_info.school_name} {user_data['학년']}학년 {user_data['반']}반 {user_data['번호']}번 {user_data['이름']}",
                                        'organization': None,
                                        'department': None,
                                        'year': dt.now().year
                                    }
                                )
                            else:  # user_type == 'O' (기관인 경우)
                                organization_info = OrganizationInfo.objects.get(
                                    organization_name=user.organization.organization_name)  # 기관 정보 가져오기

                                # 기존 사용자 확인 및 이력 저장
                                existing_user = UserInfo.objects.filter(phone_number=phone_number).first()
                                if existing_user:  # 기존 유저
                                    if existing_user.created_dt.year != dt.now().year or existing_user.year != dt.now().year:  # 작년도 사용자인 경우
                                        UserHist.objects.update_or_create(
                                            user=existing_user,
                                            organization=existing_user.organization,
                                            department=existing_user.department,
                                            student_name=existing_user.student_name,  # 기관회원의 이름도 student_name에 저장
                                            year=existing_user.year
                                        )
                                    existing_member += 1

                                new_member += 1
                                UserInfo.objects.update_or_create(  # 기존 사용자가 없는 경우 -> 신규 생성 및 갱신
                                    phone_number=phone_number,
                                    defaults={
                                        'organization': organization_info,
                                        'department': user_data['부서명'],
                                        'student_name': user_data['이름'],
                                        'username': phone_number,
                                        'password': make_password(os.environ['DEFAULT_PASSWORD']),
                                        'user_type': type,
                                        'user_display_name': f"{organization_info.organization_name} {user_data['이름']}",
                                        'school': None,
                                        'year': dt.now().year
                                    }
                                )

                        new_member = new_member - existing_member
                        return JsonResponse(
                            {'message': '성공적으로 저장되었습니다.', 'existing_member': existing_member, 'new_member': new_member})

                # 미리보기 요청인 경우
                return JsonResponse({
                    'users': users,
                    'columns': expected_columns,
                    'new_member': new_member,
                    'existing_member': existing_member
                })

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
    else:
        form = UploadFileForm()

    return render(request, 'member_register.html', {
        'form': form,
        'orgName': orgName,
        'user_type': type,
    })


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log the user in after registration
            login(request, user)
            # Redirect to the desired page after registration
            return redirect(reverse_lazy('home'))  # Redirect to 'home' or any other page
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup.html', {'form': form})


def password_reset(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)

        # 1. 아이디 검증 (폼 유효성 검증 이전에 수행)
        username = request.POST.get('username')
        try:
            user = UserInfo.objects.get(username=username)
        except UserInfo.DoesNotExist:
            # 존재하지 않는 아이디일 때 오류 메시지 추가
            form.add_error('username', '존재하지 않는 아이디입니다.')
            # 유효하지 않은 경우는 기존 에러 메시지와 함께 출력
            return render(request, 'password_reset.html', {'form': form})

        # 2. 폼 유효성 검증
        if form.is_valid():
            # 3. 비밀번호 변경
            new_password = form.cleaned_data.get('new_password1')
            user.password = make_password(new_password)
            user.save()

            return redirect('password_reset_done')

        # 폼이 유효하지 않은 경우 오류 메시지를 표시
        return render(request, 'password_reset.html', {'form': form})

    # GET 요청일 경우 빈 폼을 렌더링
    form = CustomPasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})


def password_reset_done(request):
    return render(request, 'password_reset_done.html')


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'password_change.html'
    success_url = '/password-change-done/'


@login_required
def register(request):
    users = []  # Initialize an empty list to hold user data
    columns = []  # Initialize an empty list for dynamic columns

    user = request.user  # 현재 로그인된 사용자 가져오기
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['file']
                # Read the Excel file
                df = pd.read_excel(excel_file)
                user_type = user.user_type

                # Define columns based on user type
                if user_type == 'S':
                    columns = ['학년', '반', '번호', '이름', '전화번호']
                    if not (df.columns.values.tolist() == columns):
                        user_type_str = '교직원용' if user_type == 'S' else '일반 기관용'
                        raise ValueError(f"올바른 템플릿이 아닙니다. {user_type_str} 템플릿을 다운로드 받아서 다시 시도해주세요.")
                    for _, row in df.iterrows():
                        school_info, created = SchoolInfo.objects.update_or_create(
                            school_name=user.school.school_name,
                            defaults={
                                'contact_number': user.school.contact_number,
                                'address': user.school.address,
                            }
                        )
                        phone_number = extract_digits(row['전화번호'])

                        # 회원가입이 되어 있는지 확인
                        user_info = UserInfo.objects.filter(phone_number=phone_number).first()

                        if user_info:
                            # 기존의 반 정보를 UserHist로 저장
                            UserHist.objects.create(
                                phone_number=user_info.phone_number,
                                user=user_info.id,
                                school=user_info.school,
                                student_grade=user_info.student_grade,
                                student_class=user_info.student_class,
                                student_number=user_info.student_number,
                                student_name=user_info.student_name,
                                year=user_info.year,
                            )

                        user_info, created = UserInfo.objects.update_or_create(
                            phone_number=phone_number,
                            defaults=dict(
                                school=school_info,
                                student_grade=row['학년'],
                                student_class=row['반'],
                                student_number=row['번호'],
                                student_name=row['이름'].strip().replace(' ', ''),
                                username=phone_number,
                                password=make_password(os.environ['DEFAULT_PASSWORD']),
                                user_type=user_type,
                                user_display_name=f"{school_info.school_name} {row['학년']}학년 {row['반']}반 {row['번호']}번 {row['이름']}",
                                organization=None,
                                department=None,
                                year=dt.now().year  # 현재 년도 int 값으로 저장
                            ),
                        )
                        users.append({
                            '학년': row['학년'],
                            '반': row['반'],
                            '번호': row['번호'],
                            '이름': row['이름'],
                            '전화번호': row['전화번호'],
                        })
                else:
                    columns = ['부서명', '이름', '전화번호']
                    if not (df.columns.values.tolist() == columns):
                        user_type_str = '교직원용' if user_type == 'S' else '일반 기관용'
                        raise ValueError(f"올바른 템플릿이 아닙니다. {user_type_str} 템플릿을 다운로드 받아서 다시 시도해주세요.")
                    for _, row in df.iterrows():
                        organization_info, created = OrganizationInfo.objects.update_or_create(
                            organization_name=user.organization.organization_name,
                            defaults={
                                'contact_number': user.organization.contact_number,
                                'address': user.organization.address
                            },
                        )
                        phone_number = extract_digits(row['전화번호'])
                        user_info, created = UserInfo.objects.update_or_create(
                            phone_number=phone_number,
                            defaults=dict(
                                organization=organization_info,
                                department=row['부서명'].strip(),
                                student_name=row['이름'].strip().replace(' ', ''),
                                username=phone_number,
                                password=make_password(os.environ['DEFAULT_PASSWORD']),
                                user_type=user_type,
                                user_display_name=f"{organization_info.organization_name} {row['이름']}",
                                school=None,
                                year=dt.now().year  # 현재 년도 int 값으로 저장
                            ),
                        )
                        users.append({
                            '부서명': row['부서명'],
                            '이름': row['이름'],
                            '전화번호': row['전화번호'],
                        })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
    else:
        form = UploadFileForm()

    return render(request, 'register.html', {
        'form': form,
        'users': users,
        'columns': columns,  # Pass dynamic columns
        'total_users': len(users),
    })


from django.http import JsonResponse


def search_organization(request):
    query = request.GET.get('query', '')  # 사용자가 입력한 검색어를 가져옴
    if not query:
        return JsonResponse({'error': 'Query parameter is required'}, status=400)

    # 카카오 키워드 검색 API 호출
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {os.environ['KAKAO_MAP_REST_API_KEY']}"
    }

    params = {
        "query": query,  # 검색어
        "size": 5  # 검색 결과 최대 5개
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # API 호출 결과에서 필요 정보만 추출하여 반환
    results = []
    for document in data.get('documents', []):
        results.append({
            'name': document.get('place_name'),
            'address': document.get('address_name'),
            'contact': document.get('phone'),
            'x': document.get('x'),
            'y': document.get('y'),
        })

    return JsonResponse({'results': results})


# @login_required
def register_organization(request):
    if request.method == 'POST':
        user = request.user  # 현재 로그인된 사용자 가져오기
        data = json.loads(request.body)  # JSON 요청 본문을 파싱

        org_name = data.get('org_name')
        address = data.get('address')
        contact_number = data.get('contact_number')

        # 기관이 학교인지 확인
        if org_name.endswith('학교'):
            school_info, created = SchoolInfo.objects.update_or_create(
                school_name=org_name,
                defaults={'contact_number': contact_number, 'address': address}
            )
            user.school = school_info
            user.organization = None  # 학교 등록 시 다른 기관 정보 초기화
            user.department = None
            user.user_type = 'S'
        else:
            org_info, created = OrganizationInfo.objects.update_or_create(
                organization_name=org_name,
                defaults={'contact_number': contact_number, 'address': address}
            )
            user.organization = org_info
            user.school = None  # 다른 기관 등록 시 학교 정보 초기화
            user.department = None
            user.user_type = 'O'

        user.save()  # 사용자 정보 저장

        return JsonResponse({'message': '기관이 성공적으로 등록되었습니다.'}, status=200)

    return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)


# @login_required
def get_organization_info(request):
    user_id = request.user.id  # 관리자 계정의 고유 id
    user = UserInfo.objects.get(id=user_id)

    org_info = {}
    if user.school is not None:
        org_info = {
            'org_name': user.school.school_name,
            'address': user.school.address,
            'contact': user.school.contact_number,
            'type': 'school'
        }
    elif user.organization is not None:
        org_info = {
            'org_name': user.organization.organization_name,
            'address': user.organization.address,
            'contact': user.organization.contact_number,
            'type': 'organization'
        }

    return JsonResponse(org_info)





def no_result(request):
    return render(request, 'no_result.html')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import re


@login_required
def report(request):
    user = request.user  # 현재 유저
    error_message = None
    selected_group = request.session.get('selected_group', None)  # 세션에서 그룹 정보 가져오기
    selected_year = request.session.get('selected_year', None)  # 세션에서 년도 정보 가져오기
    user_results = []
    groups = []  # 해당 School의 현재 연도 그룹 정보 저장
    years = []  # 해당 School의 BodyResult에 있는 최소 연도, 최대 연도 저장
    year_group_map = defaultdict(list)  # 연도별 그룹 정보 저장 ('연도': ['그룹1', '그룹2', ...])

    if request.method == 'POST':
        selected_group = request.POST.get('group')
        selected_year = request.POST.get('year')

        if not selected_group:
            return redirect('report')  # PRG 패턴을 위해 POST 처리 후 리다이렉트
        else:
            # 선택된 그룹을 세션에 저장하여 리다이렉트 후에도 유지
            request.session['selected_group'] = selected_group
            request.session['selected_year'] = selected_year
            return redirect('report')  # 리다이렉트 후 GET 요청으로 변환

    # GET 요청 처리 (리다이렉트 후 처리)
    if user.user_type == 'S':
        # 학교별 학년/반 정보 가져오기 -> select 태그에 들어가는 값
        groups = UserInfo.objects.filter(
            school__school_name=user.school.school_name,
        ).values_list(
            'student_grade', 'student_class', 'year', named=True
        ).distinct().order_by('year', 'student_grade', 'student_class')

        # 연도별 그룹 정보 생성
        user_hists = UserHist.objects.filter(school__id=user.school.id)
        for hist in user_hists:
            year = str(hist.year)  # UserHist의 연도 정보
            year_group = f"{hist.student_grade}학년 {hist.student_class}반"

            # 해당 연도가 year_group_map에 없으면 초기화
            if year not in year_group_map:
                year_group_map[year] = []

            # 중복되지 않게 추가
            if year_group not in year_group_map[year]:
                year_group_map[year].append(year_group)

        # UserInfo의 연도 데이터 추가
        for group in groups:
            year = str(group.year)  # UserInfo의 연도 정보
            year_group = f"{group.student_grade}학년 {group.student_class}반"

            if year not in year_group_map:
                year_group_map[year] = []

            if year_group not in year_group_map[year]:
                year_group_map[year].append(year_group)

        """ 현재 연도의 데이터가 실제로 존재하는지 확인하는 과정 """
        current_year = str(dt.now().year)

        existing_years_in_db = set(UserHist.objects.values_list('year', flat=True))

        # 현재 연도가 DB에 있는 연도에 포함될 경우만 처리
        if current_year in existing_years_in_db:
            # year_group_map에 현재 연도가 없으면 초기화
            if current_year not in year_group_map:
                year_group_map[current_year] = []

            for group in groups:
                current_group = f"{group.student_grade}학년 {group.student_class}반"
                # 현재 연도에 해당 반 정보가 없으면 추가
                if current_group not in year_group_map[current_year]:
                    year_group_map[current_year].append(current_group)

        # 학교별 년도 정보 가져오기 -> select 태그에 들어가는 값
        # school_id에 해당하는 BodyResult 데이터에서 created_dt의 최소/최대 연도를 가져오기

        years = [year for year in year_group_map.keys() if
                 year != 'None' and isinstance(year, str)]  # year_group_map의 키에서 None을 제외하고 int만 포함

        if selected_year and selected_group:
            if selected_year != str(dt.now().year) and selected_year not in year_group_map:
                error_message = '해당 연도는 검사 결과가 없습니다.'

            # 정규 표현식으로 학년과 반 추출
            match = re.search(r"(\d+)학년 (\w+)반", selected_group)

            # 당년도
            if selected_year == str(dt.now().year) and match:
                user_results.clear()  # 기존 결과 초기화

                body_result_subquery = BodyResult.objects.filter(
                    user_id=OuterRef('id'),
                    image_front_url__isnull=False,
                    image_side_url__isnull=False,
                    created_dt__year=selected_year
                )

                users = UserInfo.objects.filter(
                    school__school_name=user.school.school_name,
                    student_grade=match.group(1),
                    student_class=match.group(2),
                    year=selected_year
                ).annotate(
                    analysis_valid=Exists(body_result_subquery)
                ).order_by('student_number')

                user_results = [{
                    'user': user,
                    'analysis_valid': user.analysis_valid
                } for user in users]

            elif selected_year != str(dt.now().year) and match:
                user_results.clear()  # 기존 결과 초기화

                # UserHist에서 데이터 조회
                user_hists = UserHist.objects.filter(
                    school__id=user.school.id,
                    student_grade=match.group(1),
                    student_class=match.group(2),
                    year=selected_year
                ).order_by('student_number')

                # UserInfo에서 데이터 조회
                user_infos = UserInfo.objects.filter(
                    school__id=user.school.id,
                    student_grade=match.group(1),
                    student_class=match.group(2),
                    year=selected_year
                ).order_by('student_number')

                # UserHist에서 조회된 user_id 목록
                hist_user_ids = set(user_hists.values_list('user_id', flat=True))

                # UserInfo에서 UserHist에 없는 데이터만 필터링
                unique_user_infos = user_infos.exclude(id__in=hist_user_ids)

                # UserHist 데이터 처리
                for user_hist in user_hists:
                    body_result_queryset = BodyResult.objects.filter(
                        user_id=user_hist.user.id,
                        created_dt__year=selected_year,
                        image_front_url__isnull=False,
                        image_side_url__isnull=False,
                    )
                    analysis_valid = len(body_result_queryset) > 0

                    user_results.append({
                        'user': {
                            'id': user_hist.user.id,
                            'student_grade': user_hist.student_grade,
                            'student_class': user_hist.student_class,
                            'student_number': user_hist.student_number,
                            'student_name': user_hist.user.student_name
                        },
                        'analysis_valid': analysis_valid,
                        'created_dt': body_result_queryset[0].created_dt.strftime(
                            '%Y-%m-%d %H:%M:%S') if analysis_valid else None
                    })

                # UserInfo 데이터 처리 (UserHist에 없는 데이터만)
                for user_info in unique_user_infos:
                    body_result_queryset = BodyResult.objects.filter(
                        user_id=user_info.id,
                        created_dt__year=selected_year,
                        image_front_url__isnull=False,
                        image_side_url__isnull=False,
                    )
                    analysis_valid = len(body_result_queryset) > 0

                    user_results.append({
                        'user': {
                            'id': user_info.id,
                            'student_grade': user_info.student_grade,
                            'student_class': user_info.student_class,
                            'student_number': user_info.student_number,
                            'student_name': user_info.student_name
                        },
                        'analysis_valid': analysis_valid,
                        'created_dt': body_result_queryset[0].created_dt.strftime(
                            '%Y-%m-%d %H:%M:%S') if analysis_valid else None
                    })


    elif user.user_type == 'O':
        groups = UserInfo.objects.filter(
            organization__organization_name=user.organization.organization_name).values_list('department',
                                                                                             named=True).distinct().order_by(
            'department')
        groups = [g.department for g in groups if ((g.department is not None))]

        if selected_group:
            users = UserInfo.objects.filter(organization__organization_name=user.organization.organization_name,
                                            department=selected_group).order_by('student_name')

            # 각 user에 대한 검사 결과 여부를 확인하여 user_results에 추가
            for user in users:
                body_result_queryset = BodyResult.objects.filter(
                    user_id=user.id,
                    image_front_url__isnull=False,
                    image_side_url__isnull=False,
                )

                analysis_valid = (len(body_result_queryset) > 0)

                user_results.append({
                    'user': user,
                    'analysis_valid': analysis_valid
                })

    if user.user_type == '' or len(user_results) == 0:  # 초기 렌더링
        return render(request, 'report.html', {
            'groups': groups,  # 그룹을 초기화
            'years': years,
            'year_group_map': json.dumps(dict(year_group_map), ensure_ascii=False),
            'user_results': [],  # 테이블 초기화
            'selected_year': str(dt.now().year),
            'selected_group': None,
            'error_message': error_message,
            'valid_count': 0,
            'total_users': 0,
            'progress_percentage': 0,
            'is_registered': len(groups) > 0,
        })

    # 분석 진행률 계산
    total_users = len(user_results)
    valid_count = sum(1 for result in user_results if result['analysis_valid'])

    if total_users > 0:
        progress_percentage = (valid_count / total_users) * 100
    else:
        progress_percentage = 0

    if len(groups) == 0 or total_users == 0:
        selected_group = None
        user_results = []  # 테이블 초기화
        selected_group = None
        valid_count = 0
        total_users = 0
        progress_percentage = 0
        error_message = '그룹이 선택되지 않았습니다. 그룹 선택 후 조회 해주세요!'

    return render(request, 'report.html', {
        'groups': groups,
        'years': years,
        'year_group_map': json.dumps(dict(year_group_map), ensure_ascii=False),
        'user_results': user_results,
        'selected_year': selected_year,
        'selected_group': selected_group,
        'error_message': error_message,
        'valid_count': valid_count,
        'total_users': total_users,
        'progress_percentage': progress_percentage,
        'is_registered': True,
    })


@login_required
def report_download(request):
    user_request = request.user
    selected_group = request.GET.get('group', None)
    selected_year = request.GET.get('year', None)

    user = UserInfo.objects.get(id=user_request.id)
    user_type = user.user_type

    if not selected_group or not selected_year or not user.is_authenticated or user is None:
        return redirect('report')

    # 사용자 목록 조회
    if user_type == 'S':  # 학교 사용자
        match = re.search(r"(\d+)학년 (\w+)반", selected_group)
        if selected_year == str(dt.now().year) and match:  # 현재 년도 조회
            users = UserInfo.objects.filter(
                school__school_name=user.school.school_name,
                student_grade=match.group(1),
                student_class=match.group(2),
                year=selected_year
            ).order_by('student_number')
        else:  # 이전 년도 조회
            # UserHist에서 데이터 조회
            user_hists = UserHist.objects.filter(
                school__id=user.school.id,
                student_grade=match.group(1),
                student_class=match.group(2),
                year=selected_year
            ).order_by('student_number')

            # UserInfo에서 데이터 조회
            user_infos = UserInfo.objects.filter(
                school__id=user.school.id,
                student_grade=match.group(1),
                student_class=match.group(2),
                year=selected_year
            ).order_by('student_number')

            # UserHist에서 조회된 user_id 목록
            hist_user_ids = set(user_hists.values_list('user_id', flat=True))

            # UserInfo에서 UserHist에 없는 데이터만 필터링
            unique_user_infos = user_infos.exclude(id__in=hist_user_ids)

            # 최종 사용자 목록 생성
            users = list(user_hists) + list(unique_user_infos)

    elif user_type == 'O':  # 기관 사용자
        users = UserInfo.objects.filter(
            organization__organization_name=user.organization.organization_name,
            department=selected_group
        ).order_by('student_name')

    # 한 번에 모든 사용자의 ID 리스트 생성
    if user_type == 'S':  # 학교 사용자의 경우 (이전 년도가 포함될 수 있음 (UserHist))
        user_ids = [user.user_id for user in user_hists] + [user.id for user in
                                                            unique_user_infos] if selected_year != str(
            dt.now().year) else [user.id for user in users]
    else:  # 기관 사용자의 경우
        user_ids = [user.id for user in users]

    if user_type == 'S':
        # 한 번의 쿼리로 모든 BodyResult 데이터 조회
        body_results = BodyResult.objects.filter(  # user_id로 필터링 (선택된 년도에 생성된 bodyResult)
            user_id__in=user_ids,
            created_dt__year=selected_year,
            image_front_url__isnull=False,
            image_side_url__isnull=False,
        ).select_related('user')
    else:  # 기관은 모든 년도의 데이터를 사용
        body_results = BodyResult.objects.filter(  # user_id로 필터링 (선택된 년도에 생성된 bodyResult)
            user_id__in=user_ids,
            image_front_url__isnull=False,
            image_side_url__isnull=False,
        ).select_related('user')

    # {user_id : <BodyResult:QuerySet> }
    body_results_dict = {}
    for br in body_results:
        if br.user_id not in body_results_dict:
            body_results_dict[br.user_id] = br

    # code_name 목록 가져오기
    code_names = []
    if body_results:
        first_result = next(iter(body_results))
        _, status_results = calculate_normal_ratio(first_result)
        code_names = list(status_results.keys())

    # 엑셀 데이터 생성
    excel_data = []
    for user in users:
        # UserHist에서 가져온 경우 user_id를 user.user_id로 설정
        if hasattr(user, 'user_id'):
            user_id = user.user_id
        else:  # UserInfo에서 가져온 경우
            user_id = user.id

        body_result = body_results_dict.get(user_id)

        if user_type == 'S':
            row_data = {
                '학년': user.student_grade,
                '반': user.student_class,
                '번호': user.student_number,
                '이름': user.student_name,
                '검사일': body_result.created_dt.strftime('%Y-%m-%d %H:%M:%S') if body_result else None,
                '검사결과': 'O' if body_result else 'X',
            }
        else:
            row_data = {
                '부서명': user.department,
                '이름': user.student_name,
                '검사일': body_result.created_dt.strftime('%Y-%m-%d %H:%M:%S') if body_result else None,
                '검사결과': 'O' if body_result else 'X',
            }

        if body_result:
            ratio, status_results = calculate_normal_ratio(body_result)
            row_data['정상범위'] = ratio
            # 각 측정 항목의 상태(양호/주의)를 추가
            for code_name, status in status_results.items():
                row_data[code_name] = status
        else:
            row_data['정상범위'] = None
            for code_name in code_names:
                row_data[code_name] = None

        excel_data.append(row_data)

    # 데이터프레임 생성 (기본 컬럼 + code_name 컬럼들)
    df = pd.DataFrame(excel_data)

    # 컬럼 순서 설정
    if user_type == 'S':
        columns = ['학년', '반', '번호', '이름', '검사일', '검사결과', '정상범위'] + code_names
    else:
        columns = ['부서명', '이름', '검사일', '검사결과', '정상범위'] + code_names
    df = df[columns]

    # 엑셀 커스텀마이징(열 폭, 색상)
    workbook = create_excel_report(df, user_type, code_names)

    # 파일명 생성 및 응답 반환
    if user_type == 'S':
        file_name = f"{selected_year}_{user.school.school_name}_{selected_group}.xlsx"
    else:
        file_name = f"{selected_year}_{user.organization.organization_name}_{selected_group}.xlsx"
    encoded_file_name = quote(file_name)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_file_name}"
    workbook.save(response)

    return response


# Example report items
# TODO: get from actual DB
from django.shortcuts import render, get_object_or_404
from .models import UserInfo

import pytz

kst = pytz.timezone('Asia/Seoul')


@login_required
def report_detail(request, id):
    user_id = id
    return generate_report(request, user_id)


@login_required
def report_detail_protected(request):
    user_id = request.user.id
    return generate_report(request, user_id)


@login_required
def report_detail_report_id(request, id, report_id):
    user_id = id
    return generate_report(request, user_id, report_id)


def generate_report(request, id, report_id=None):
    max_count = 20
    body_info_queryset = CodeInfo.objects.filter(group_id='01').order_by('seq_no')

    # 해당 유저의 모든 검사 결과를 가져옴
    body_result_queryset = BodyResult.objects.filter(
        user_id=id,
        image_front_url__isnull=False,
        image_side_url__isnull=False,
    )

    # body result 최신 순 정렬 후 날짜만 뽑아오기
    body_result_queryset = body_result_queryset.order_by('created_dt')[
                           max(0, len(body_result_queryset) - int(max_count)):]

    if len(body_result_queryset) == 0:
        return render(request, 'no_result.html', status=404)

    body_result_latest = body_result_queryset[len(body_result_queryset) - 1]

    # body result에서 날짜만 뽑아서 정렬하기
    result_dates = [result.created_dt.strftime('%Y-%m-%d %H:%M:%S') for result in body_result_queryset]
    sorted_dates = sorted(result_dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'), reverse=True)

    # 사용자가 선택한 날짜 처리
    selected_date = request.GET.get('selected_date')
    selected_result = []
    select_report_date = None

    if selected_date:
        # 전체 쿼리셋은 유지하면서 선택된 날짜의 결과만 latest로 설정
        selected_result = [
            result for result in body_result_queryset
            if result.created_dt.strftime('%Y-%m-%d %H:%M:%S') == selected_date
        ]

        if len(selected_result) == 0:
            return render(request, 'no_result.html', status=404)

        # 선택된 날짜의 결과만 latest로 설정하고, 전체 쿼리셋은 유지
        # selected_result의 순서를 맨 앞으로 가져오고, 나머지는 뒤에 배치
        body_result_queryset = [result for result in body_result_queryset if
                                result not in selected_result] + selected_result
        body_result_latest = selected_result[0]

    elif report_id:
        # report_id에 해당하는 BodyResult를 가져옴
        tmp = list(BodyResult.objects.filter(id=report_id))

        # body_result_queryset과 tmp의 차집합을 유지하고, tmp를 뒤에 추가
        body_result_queryset = [result for result in body_result_queryset if result not in tmp] + tmp
        select_report_date = body_result_queryset[-1].created_dt.astimezone(kst).strftime(
            '%Y-%m-%d %H:%M:%S') if body_result_queryset else None

    else:
        select_report_date = body_result_latest.created_dt.astimezone(kst).strftime('%Y-%m-%d %H:%M:%S')

    report_items = []

    for body_info in body_info_queryset:
        trend_data = []
        is_paired = False

        for body_result in body_result_queryset:
            body_code_id_ = body_info.code_id
            alias = body_info.code_id
            if 'leg_alignment' in body_code_id_ or 'back_knee' in body_code_id_ or 'scoliosis' in body_code_id_:
                is_paired = True
                if 'scoliosis' in body_code_id_:
                    code_parts = body_code_id_.split('_')
                    pair_names = ['shoulder', 'hip']
                    paired_body_code_id_list = ['_'.join([code_parts[0], pair, code_parts[2]]) for pair in pair_names]

                else:
                    pair_names = ['left', 'right']
                    paired_body_code_id_list = [f'{pair}_' + '_'.join(body_code_id_.split('_')[1:]) for pair in
                                                pair_names]

                if 'leg_alignment' in body_code_id_:
                    alias = 'o_x_legs'
                if 'back_knee' in body_code_id_:
                    alias = 'knee_angle'
                if 'scoliosis' in body_code_id_:
                    alias = 'spinal_imbalance'

                trend_samples = [getattr(body_result, paired_body_code_id_list[0]),
                                 getattr(body_result, paired_body_code_id_list[1]),
                                 body_result.created_dt.strftime('%Y-%m-%d %H:%M:%S')]
            else:
                trend_samples = [getattr(body_result, body_code_id_),
                                 body_result.created_dt.strftime('%Y-%m-%d %H:%M:%S')]
            trend_data.append(trend_samples)

        if is_paired:
            result_val1, result_val2, *_ = trend_data[-1]
            result1 = None
            if result_val1 is not None:
                result1 = round(result_val1, 2)
            result2 = None
            if result_val2 is not None:
                result2 = round(result_val2, 2)

            description_list = []
            unit_name = body_info.unit_name
            normal_range = [body_info.normal_min_value, body_info.normal_max_value]
            for i, val in enumerate([result1, result2]):
                if alias == 'o_x_legs':
                    title = body_info.code_name.replace('(좌)', '').replace('(우)', '')
                    metric = '각도 [°]'
                    pair_name = '왼쪽' if i == 0 else '오른쪽'
                    if val:
                        if normal_range[0] < val < normal_range[1]:
                            description = '양호'
                        else:
                            description = 'O 다리 의심' if val < 180 else 'X 다리 의심'
                    else:
                        description = "측정값 없음"
                if alias == 'knee_angle':
                    title = body_info.code_name.replace('(좌)', '').replace('(우)', '')
                    metric = '각도 [°]'
                    pair_name = '왼쪽' if i == 0 else '오른쪽'
                    if val:
                        if normal_range[0] < val < normal_range[1]:
                            description = '양호'
                        else:
                            description = '반장슬 의심'
                    else:
                        description = "측정값 없음"
                if alias == 'spinal_imbalance':
                    title = '척추 균형'
                    metric = '척추 기준 좌우 비율 차이 [%]'
                    pair_name = '척추-어깨' if i == 0 else '척추-골반'
                    if val:
                        if normal_range[0] < val < normal_range[1]:
                            description = '양호'
                        else:
                            description = '왼쪽 편향' if val < 0 else '오른쪽 편향'
                    else:
                        description = "측정값 없음"

                description_list.append(f'{pair_name} : ' + description)

            if not result1:
                result1 = "?"
            else:
                status_desc = ""
                if alias == 'spinal_imbalance':
                    if result1 < 0:
                        status_desc += "왼쪽으로" + " "
                    else:
                        status_desc += "오른쪽으로" + " "
                result1 = f'{status_desc}{abs(result1)}{unit_name}'

            if not result2:
                result2 = "?"
            else:
                status_desc = ""
                if alias == 'spinal_imbalance':
                    if result2 < 0:
                        status_desc += "왼쪽으로" + " "
                    else:
                        status_desc += "오른쪽으로" + " "
                result2 = f'{status_desc}{abs(result2)}{unit_name}'

            if alias == 'spinal_imbalance':
                result = f'· 척추-어깨: {result1}의 편향, · 척추-골반: {result2}의 편향'
            else:
                result = f'{result1} / {result2}'
            if all([i['title'] != title for i in report_items]):
                report_items.append({
                    'title': title,
                    'alias': alias,
                    'result': result,
                    'description': description_list,
                    'description_list': True,
                    'metric': metric,
                    'summary': [re.sub(r'\(.*?\)', '', x) for x in description_list],
                    'normal_range': [body_info.normal_min_value, body_info.normal_max_value],
                    'value_range': [body_info.min_value, body_info.max_value],
                    'trend': trend_data,
                    'sections': {getattr(body_info, f'title_{name}'): getattr(body_info, name) for name in
                                 ['outline', 'risk', 'improve', 'recommended']}
                })
        else:
            result_val = getattr(body_result_latest, body_info.code_id)
            result = None
            if result_val is not None:
                result = round(result_val, 2)
            unit_name = body_info.unit_name
            normal_range = [body_info.normal_min_value, body_info.normal_max_value]
            if 'angle' in alias:
                if result:
                    description = '왼쪽으로' if result < 0 else '오른쪽으로'
                else:
                    description = "측정값 없음"
                metric = '각도 [°]'

            if alias == 'forward_head_angle':
                if result:
                    description = '양호' if normal_range[0] < result < normal_range[1] else '거북목 진행형'
                else:
                    description = "측정값 없음"

            if alias == 'leg_length_ratio':
                if result:
                    description = '왼쪽이 더 짧음' if result < 0 else '오른쪽이 더 짧음'
                else:
                    description = "측정값 없음"
                metric = '다리 길이 차이 [%]'

            if not result:
                result = "?"
            else:
                status_desc = ""
                if normal_range[0] < result < normal_range[1]:
                    status_desc += " " + "(정상)"
                else:
                    status_desc += " " + "(유의)"

                result = f'{abs(result)}{unit_name}{status_desc}'  # show absolute value
            report_items.append({
                'title': body_info.code_name,
                'alias': alias,
                'result': result,
                'description': description,
                'description_list': False,
                'metric': metric,
                'summary': re.sub(r'\(.*?\)', '', description),
                'normal_range': normal_range,
                'value_range': [body_info.min_value, body_info.max_value],
                'trend': trend_data,
                'sections': {getattr(body_info, f'title_{name}'): getattr(body_info, name) for name in
                             ['outline', 'risk', 'improve', 'recommended']}
            })

    user = get_object_or_404(UserInfo, id=id)

    if not report_items:
        return render(request, '404.html', status=404)

    # Prepare trend data for each report item
    trend_data_dict = {}
    for item in report_items:
        alias = item['alias']
        trend_data = item['trend']

        if alias in ['spinal_imbalance', 'o_x_legs', 'knee_angle']:
            trend_data_dict[alias] = {
                'val1': [value[0] for value in trend_data],  # 왼쪽 또는 상부
                'val2': [value[1] for value in trend_data],  # 오른쪽 또는 하부
                'dates': [value[2] for value in trend_data],  # 날짜 (세 번째 요소)
                'part': ['어깨', '골반'] if alias == 'spinal_imbalance' else ['왼쪽', '오른쪽']
            }
        else:
            trend_data_dict[alias] = {
                'values': [value[0] for value in trend_data],
                'dates': [value[1] for value in trend_data]
            }

    created_dt = body_result_latest.created_dt.strftime('%Y%m%dT%H%M%S%f')

    front_img_url = generate_presigned_url(file_keys=['front', created_dt])
    side_img_url = generate_presigned_url(file_keys=['side', created_dt])

    context = {
        'user': user,
        'report_items': report_items,
        'trend_data_dict': trend_data_dict,
        'image_front_url': front_img_url,
        'image_side_url': side_img_url,
        'sorted_dates': sorted_dates,  # 날짜 리스트
        'selected_date': selected_date,  # 선택한 날짜
    }

    context['report_date'] = select_report_date

    return render(request, 'report_detail.html', context)


def policy(request):
    return render(request, 'policy.html')


######################################################################
################## 게이트(보행) 관련 뷰 페이지 로직 ##########################

@login_required
def get_user_gait_data(request, user_id):
    request_user = request.user
    user = UserInfo.objects.get(id=user_id)
    gait_results = GaitResult.objects.filter(user_id=user_id).order_by('-created_dt')

    results_data = []
    for result in gait_results:
        results_data.append({
            'created_dt': result.created_dt.strftime('%Y-%m-%d'),
            'velocity': result.velocity,
            'cadence': result.cadence,
            'stride_len_l': result.stride_len_l,
            'stride_len_r': result.stride_len_r,
            'cycle_time_l': result.cycle_time_l,
            'cycle_time_r': result.cycle_time_r,
            'swing_perc_l': result.swing_perc_l,
            'swing_perc_r': result.swing_perc_r,
            'stance_perc_l': result.stance_perc_l,
            'stance_perc_r': result.stance_perc_r
        })

    return JsonResponse({
        'user_name': user.student_name,
        'results': results_data
    })


# JSON 인코더 확장
class RoundingJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            return round(obj, 1)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


@login_required
def gait_report(request):
    user = request.user  # 현재 로그인한 유저
    error_message = None

    user_results = []  # 사용자 결과

    selected_group = request.session.get('selected_group', None)  # 세션에서 그룹 정보 가져오기
    groups = []

    if request.method == 'POST':
        selected_group = request.POST.get('group')

        if not selected_group:
            return redirect('gait_report')
        else:
            request.session['selected_group'] = selected_group
            return redirect('gait_report')

    if user.user_type == 'O':
        groups = UserInfo.objects.filter(
            organization__organization_name=user.organization.organization_name).values_list('department',
                                                                                             named=True).distinct().order_by(
            'department')
        groups = [g.department for g in groups if ((g.department is not None))]  # 해당 기관의 그룹 목록

        if selected_group:
            users = UserInfo.objects.filter(organization__organization_name=user.organization.organization_name,
                                            department=selected_group).order_by('student_name')

            for user in users:
                gate_result_queryset = GaitResult.objects.filter(user_id=user.id)
                analysis_valid = len(gate_result_queryset) > 0

                user_results.append({
                    'user': UserInfoSerializer(user).data,
                    'analysis_valid': analysis_valid,
                    'gait_results': GaitResultSerializer(gate_result_queryset, many=True).data,  # 수정된 부분
                    'first_gait_dt': gate_result_queryset[0].created_dt.strftime(
                        '%Y-%m-%d %H:%M:%S') if gate_result_queryset else None
                })

        # 분석 진행률 계산
    total_users = len(user_results)
    valid_count = sum(1 for result in user_results if result['analysis_valid'])

    if total_users > 0:
        progress_percentage = (valid_count / total_users) * 100
    else:
        progress_percentage = 0

    if user.user_type == '' or len(user_results) == 0:  # 초기 렌더링
        return render(request, 'gait_report.html', {
            'groups': groups,
            'user_results': [],
            'selected_group': None,
            'error_message': error_message,
            'is_registered': len(groups) > 0,
            'progress_percentage': 0,
            'total_users': 0,  # 총 사용자 수
            'valid_count': valid_count
        })

    return render(request, 'gait_report.html', {
        'groups': groups,
        'user_results': user_results,
        'user_results_json': json.dumps(user_results, cls=RoundingJSONEncoder, ensure_ascii=False),
        'selected_group': selected_group,
        'error_message': error_message,
        'is_registered': len(groups) > 0,
        'total_users': total_users,  # 총 사용자 수
        'valid_count': valid_count,
        'progress_percentage': progress_percentage
    })


@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
@login_required
def body_print(request, id, detail=None):
    max_count = 4 # 최대 4개까지 보여줌
    body_info_queryset = CodeInfo.objects.filter(group_id='01').order_by('seq_no')

    user = get_object_or_404(UserInfo, id=id)

    # 해당 유저의 모든 검사 결과를 쿼리
    body_result_queryset = BodyResult.objects.filter(
        user_id=id,
        image_front_url__isnull=False,
        image_side_url__isnull=False,
    )
    body_result_queryset = body_result_queryset.order_by('created_dt')[
                           max(0, len(body_result_queryset) - int(max_count)):]

    if len(body_result_queryset) == 0:
        return render(request, 'no_result.html', status=404)
    body_result_latest = body_result_queryset[len(body_result_queryset) - 1]

    report_items = []
    dates = ''

    for body_info in body_info_queryset:
        trend_data = []
        is_paired = False

        for body_result in body_result_queryset:
            body_code_id_ = body_info.code_id
            alias = body_info.code_id
            unit = body_info.unit_name

            if 'leg_alignment' in body_code_id_ or 'back_knee' in body_code_id_ or 'scoliosis' in body_code_id_:
                is_paired = True
                if 'scoliosis' in body_code_id_:
                    code_parts = body_code_id_.split('_')
                    pair_names = ['shoulder', 'hip']
                    paired_body_code_id_list = ['_'.join([code_parts[0], pair, code_parts[2]]) for pair in pair_names]

                else:
                    pair_names = ['left', 'right']
                    paired_body_code_id_list = [f'{pair}_' + '_'.join(body_code_id_.split('_')[1:]) for pair in
                                                pair_names]

                if 'leg_alignment' in body_code_id_:
                    alias = 'o_x_legs'
                if 'back_knee' in body_code_id_:
                    alias = 'knee_angle'
                if 'scoliosis' in body_code_id_:
                    alias = 'spinal_imbalance'

                trend_samples = [getattr(body_result, paired_body_code_id_list[0]),
                                 getattr(body_result, paired_body_code_id_list[1]),
                                 body_result.created_dt.strftime('%Y-%m-%d %H:%M:%S')]
            else:
                trend_samples = [getattr(body_result, body_code_id_),
                                 body_result.created_dt.strftime('%Y-%m-%d %H:%M:%S')]
            trend_data.append(trend_samples)

        if is_paired:
            result_val1, result_val2, *_ = trend_data[-1]
            result1 = None
            if result_val1 is not None:
                result1 = round(result_val1, 2)
            result2 = None
            if result_val2 is not None:
                result2 = round(result_val2, 2)

            description_list = []
            unit_name = body_info.unit_name
            normal_range = [body_info.normal_min_value, body_info.normal_max_value]
            for i, val in enumerate([result1, result2]):
                if alias == 'o_x_legs':
                    title = body_info.code_name.replace('(좌)', '').replace('(우)', '')
                    metric = '각도 [°]'
                    pair_name = '왼쪽' if i == 0 else '오른쪽'
                    if val:
                        if normal_range[0] < val < normal_range[1]:
                            description = '양호'
                        else:
                            description = 'O 다리 의심' if val < 180 else 'X 다리 의심'
                    else:
                        description = "측정값 없음"
                if alias == 'knee_angle':
                    title = body_info.code_name.replace('(좌)', '').replace('(우)', '')
                    metric = '각도 [°]'
                    pair_name = '왼쪽' if i == 0 else '오른쪽'
                    if val:
                        if normal_range[0] < val < normal_range[1]:
                            description = '양호'
                        else:
                            description = '반장슬 의심'
                    else:
                        description = "측정값 없음"
                if alias == 'spinal_imbalance':
                    title = '척추 균형'
                    metric = '척추 기준 좌우 비율 차이 [%]'
                    pair_name = '척추-어깨' if i == 0 else '척추-골반'
                    if val:
                        if normal_range[0] < val < normal_range[1]:
                            description = '양호'
                        else:
                            description = '왼쪽 편향' if val < 0 else '오른쪽 편향'
                    else:
                        description = "측정값 없음"

                description_list.append(f'{pair_name} : ' + description)

            if not result1:
                result1 = "?"
            else:
                status_desc = ""
                if alias == 'spinal_imbalance':
                    if result1 < 0:
                        status_desc += "왼쪽으로" + " "
                    else:
                        status_desc += "오른쪽으로" + " "
                result1 = f'{status_desc}{abs(result1)}{unit_name}'

            if not result2:
                result2 = "?"
            else:
                status_desc = ""
                if alias == 'spinal_imbalance':
                    if result2 < 0:
                        status_desc += "왼쪽으로" + " "
                    else:
                        status_desc += "오른쪽으로" + " "
                result2 = f'{status_desc}{abs(result2)}{unit_name}'

            if alias == 'spinal_imbalance':
                result = f'· 척추-어깨: {result1}의 편향, · 척추-골반: {result2}의 편향'
            else:
                result = f'{result1} / {result2}'
            if all([i['title'] != title for i in report_items]):
                # 특수 항목들에 대한 측정 항목 설정
                custom_measurement_type = None
                if alias == 'spinal_imbalance':
                    if i == 0:  # 척추-어깨
                        custom_measurement_type = ''
                    else:  # 척추-골반
                        custom_measurement_type = '척추-(골반/어깨) 정렬비율'
                elif alias == 'o_x_legs':
                    custom_measurement_type = '다리가 굽어진 정도'
                elif alias == 'knee_angle':
                    custom_measurement_type = '다리가 굽어진 정도'

                report_items.append({
                    'title': title,
                    'alias': alias,
                    'result': result,
                    'description': description_list,
                    'description_list': True,
                    'metric': metric,
                    'measurement_type': custom_measurement_type or body_info.measurement_type,
                    'summary': [re.sub(r'\(.*?\)', '', x) for x in description_list],
                    'normal_range': [body_info.normal_min_value, body_info.normal_max_value],
                    'value_range': [body_info.min_value, body_info.max_value],
                    'trend': trend_data,
                    'sections': {getattr(body_info, f'title_{name}'): getattr(body_info, name) for name in
                                 ['outline', 'risk', 'improve', 'recommended']},
                    "unit": unit
                })
        else:
            result_val = getattr(body_result_latest, body_info.code_id)
            result = None
            if result_val is not None:
                result = round(result_val, 2)
            unit_name = body_info.unit_name
            normal_range = [body_info.normal_min_value, body_info.normal_max_value]
            if 'angle' in alias:
                if result:
                    description = '왼쪽으로' if result < 0 else '오른쪽으로'
                else:
                    description = "측정값 없음"
                metric = '각도 [°]'

            if alias == 'forward_head_angle':
                if result:
                    description = '양호' if normal_range[0] < result < normal_range[1] else '거북목 진행형'
                else:
                    description = "측정값 없음"

            if alias == 'leg_length_ratio':
                if result:
                    description = '왼쪽이 더 짧음' if result < 0 else '오른쪽이 더 짧음'
                else:
                    description = "측정값 없음"
                metric = '다리 길이 차이 [%]'

            if not result:
                result = "?"
            else:
                status_desc = ""
                if normal_range[0] < result < normal_range[1]:
                    status_desc += " " + "(정상)"
                else:
                    status_desc += " " + "(유의)"

                result = f'{abs(result)}{unit_name}{status_desc}'  # show absolute value
            report_items.append({
                'title': body_info.code_name,
                'alias': alias,
                'result': result,
                'description': description,
                'description_list': False,
                'metric': metric,
                'measurement_type': body_info.measurement_type,
                'summary': re.sub(r'\(.*?\)', '', description),
                'normal_range': normal_range,
                'value_range': [body_info.min_value, body_info.max_value],
                'trend': trend_data,
                'sections': {getattr(body_info, f'title_{name}'): getattr(body_info, name) for name in
                             ['outline', 'risk', 'improve', 'recommended']},
                "unit": unit
            })

    user = UserInfo.objects.filter(id=id).first()
    if not user:
        return render(request, '404.html', status=404)

    if not report_items:
        return render(request, '404.html', status=404)

    # Prepare trend data for each report item
    trend_data_dict = {}
    side_data_dict = {}
    for item in report_items:
        alias = item['alias']
        trend_data = item['trend']

        if alias in ['spinal_imbalance', 'o_x_legs', 'knee_angle']: # 어깨-골반, 휜다리, 무릎 기울기
            trend_data_dict[alias] = {
                'val1': [value[0] for value in trend_data],  # 왼쪽 또는 상부
                'val2': [value[1] for value in trend_data],  # 오른쪽 또는 하부
                'dates': [value[2] for value in trend_data],  # 날짜 (세 번째 요소)
                'part': ['어깨', '골반'] if alias == 'spinal_imbalance' else ['왼쪽', '오른쪽']
            }

            if alias == 'knee_angle':
                side_data_dict[alias + "_left"] = {
                    'val1': [value[0] for value in trend_data],  # 왼쪽
                    'dates': [value[2] for value in trend_data],  # 날짜 (세 번째 요소)
                    'part': ['왼쪽']
                }

                side_data_dict[alias + "_right"] = {
                    'val2': [value[1] for value in trend_data],  # 오른쪽
                    'dates': [value[2] for value in trend_data],  # 날짜 (세 번째 요소)
                    'part': ['오른쪽']
                }

        else:
            trend_data_dict[alias] = {
                'values': [value[0] for value in trend_data],
                'dates': [value[1] for value in trend_data]
            }
            dates = trend_data[-1][1]  # 마지막 날짜를 가져옴

    created_dt = body_result_latest.created_dt.strftime('%Y%m%dT%H%M%S%f')

    front_img_url = generate_presigned_url(file_keys=['front', created_dt])
    side_img_url = generate_presigned_url(file_keys=['side', created_dt])

    # 날짜 형식 변경 YYYY년 MM월 DD일
    dates = datetime.strptime(dates, '%Y-%m-%d %H:%M:%S').strftime('%Y년 %m월 %d일')

    context = {
        'user': user,
        'report_items': report_items,
        'trend_data_dict': trend_data_dict,
        'side_data_dict': side_data_dict,
        'image_front_url': front_img_url,
        'image_side_url': side_img_url,
        'dates': dates,
    }

    if detail is not None:
        return render(request, 'body_print_kiosk.html', context)
    return render(request, 'body_print.html', context)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
@login_required()
def body_print_kiosk(request, id):
    return body_print(request._request, id, detail=True)



@login_required
def gait_print(request, id, detail=None):
    user = UserInfo.objects.filter(id=id).first()
    if not user:
        return render(request, '404.html', status=404)

    # 해당 사용자의 보행 검사 결과 조회 (최신 결과)
    gait_result_queryset = GaitResult.objects.filter(user_id=id).order_by('-created_dt')

    if len(gait_result_queryset) == 0:
        return render(request, 'no_result.html', status=404)

    # 최신 결과와 생성 일자 가져오기
    gait_result_latest = gait_result_queryset[0]
    created_dt = gait_result_latest.created_dt

    # CodeInfo에서 보행 관련 코드 정보 가져오기 (그룹 ID '02'는 보행 관련 코드)
    gait_code_info = CodeInfo.objects.filter(group_id='02').order_by('seq_no')

    # 코드 정보를 code_id를 키로 하는 dictionary로 변환
    code_info_dict = {code.code_id: code for code in gait_code_info}

    # 정상 범위 데이터 가져오기
    normal_ranges = {
        'velocity': {
            'normal_min': code_info_dict['velocity'].normal_min_value,
            'normal_max': code_info_dict['velocity'].normal_max_value,
            'min': code_info_dict['velocity'].min_value,
            'max': code_info_dict['velocity'].max_value,
            'direction': code_info_dict['velocity'].direction
        },
        'cadence': {
            'normal_min': 90, 'normal_max': 120, 'min': 60, 'max': 150,
            'direction': 'positive'
        },
        'stride_len': {
            'normal_min': code_info_dict['stride_len_l'].normal_min_value,
            'normal_max': code_info_dict['stride_len_l'].normal_max_value,
            'min': code_info_dict['stride_len_l'].min_value,
            'max': code_info_dict['stride_len_l'].max_value,
            'direction': code_info_dict['stride_len_l'].direction
        },
        'cycle_time': {
            'normal_min': 0.9, 'normal_max': 1.2, 'min': 0.7, 'max': 1.5,
            'direction': 'negative'
        },
        'swing_perc': {
            'normal_min': code_info_dict['swing_perc_l'].normal_min_value,
            'normal_max': code_info_dict['swing_perc_l'].normal_max_value,
            'min': code_info_dict['swing_perc_l'].min_value,
            'max': code_info_dict['swing_perc_l'].max_value,
            'direction': code_info_dict['swing_perc_l'].direction
        },
        'stance_perc': {
            'normal_min': code_info_dict['stance_perc_l'].normal_min_value,
            'normal_max': code_info_dict['stance_perc_l'].normal_max_value,
            'min': code_info_dict['stance_perc_l'].min_value,
            'max': code_info_dict['stance_perc_l'].max_value,
            'direction': code_info_dict['stance_perc_l'].direction
        },
        'd_supp_perc': {
            'normal_min': code_info_dict['d_supp_perc_l'].normal_min_value,
            'normal_max': code_info_dict['d_supp_perc_l'].normal_max_value,
            'min': code_info_dict['d_supp_perc_l'].min_value,
            'max': code_info_dict['d_supp_perc_l'].max_value,
            'direction': code_info_dict['d_supp_perc_l'].direction
        },
        'score': {
            'normal_min': code_info_dict['score'].normal_min_value,
            'normal_max': code_info_dict['score'].normal_max_value,
            'min': code_info_dict['score'].min_value,
            'max': code_info_dict['score'].max_value,
            'direction': code_info_dict['score'].direction
        }
    }

    # 기본 데이터 포맷 준비
    gait_data = {
        'velocity': gait_result_latest.velocity,
        'cadence': gait_result_latest.cadence,
        'stride_len_l': gait_result_latest.stride_len_l,
        'stride_len_r': gait_result_latest.stride_len_r,
        'cycle_time_l': gait_result_latest.cycle_time_l,
        'cycle_time_r': gait_result_latest.cycle_time_r,
        'swing_perc_l': gait_result_latest.swing_perc_l,
        'swing_perc_r': gait_result_latest.swing_perc_r,
        'stance_perc_l': gait_result_latest.stance_perc_l,
        'stance_perc_r': gait_result_latest.stance_perc_r,
        'd_supp_perc_l': gait_result_latest.d_supp_perc_l,
        'd_supp_perc_r': gait_result_latest.d_supp_perc_r,
        'score': gait_result_latest.score
    }

    # 변화 추이 데이터 준비 (최근 5개 결과)
    gait_trends = GaitResult.objects.filter(user_id=id).order_by('-created_dt')[:4]

    if len(gait_trends) >= 1:  # 추이 데이터가 1개 이상인 경우에만 차트 생성
        trend_data = {
            'dates': [],
            'velocity': [],
            'cadence': [],
            'score': []
        }

        # 가장 오래된 결과부터 표시하기 위해 역순으로 정렬
        for result in reversed(list(gait_trends)):
            trend_data['dates'].append(result.created_dt.strftime('%Y-%m-%d'))
            trend_data['velocity'].append(result.velocity)
            trend_data['cadence'].append(result.cadence)
            trend_data['score'].append(result.score)
    else:
        trend_data = None

    # 정상 범위 텍스트 포맷팅
    stride_len_normal = f"{normal_ranges['stride_len']['normal_min']}~{normal_ranges['stride_len']['normal_max']} cm"
    cycle_time_normal = f"{normal_ranges['cycle_time']['normal_min']}~{normal_ranges['cycle_time']['normal_max']} sec"
    swing_perc_normal = f"{normal_ranges['swing_perc']['normal_min']}~{normal_ranges['swing_perc']['normal_max']} %"
    stance_perc_normal = f"{normal_ranges['stance_perc']['normal_min']}~{normal_ranges['stance_perc']['normal_max']} %"
    d_supp_perc_normal = f"{normal_ranges['d_supp_perc']['normal_min']}~{normal_ranges['d_supp_perc']['normal_max']} %"
    velocity_normal = f"{normal_ranges['velocity']['normal_min']}~{normal_ranges['velocity']['normal_max']} cm/sec"
    score_normal = f"{normal_ranges['score']['normal_min']}~{normal_ranges['score']['normal_max']} 점"

    # 코드 정보를 컨텍스트에 추가
    code_info_context = {
        code.code_id: {
            'code_name': code.code_name,
            'min_value': code.min_value,
            'max_value': code.max_value,
            'normal_min_value': code.normal_min_value,
            'normal_max_value': code.normal_max_value,
            'caution_min_value': code.caution_min_value,
            'caution_max_value': code.caution_max_value,
            'unit_name': code.unit_name,
            'direction': code.direction
        }
        for code in gait_code_info
    }

    # 컨텍스트 데이터 준비
    context = {
        'user': user,
        'created_dt': created_dt,
        'current_date': dt.now(),
        'velocity': gait_result_latest.velocity,
        'cadence': gait_result_latest.cadence,
        'stride_len_l': gait_result_latest.stride_len_l,
        'stride_len_r': gait_result_latest.stride_len_r,
        'cycle_time_l': gait_result_latest.cycle_time_l,
        'cycle_time_r': gait_result_latest.cycle_time_r,
        'swing_perc_l': gait_result_latest.swing_perc_l,
        'swing_perc_r': gait_result_latest.swing_perc_r,
        'stance_perc_l': gait_result_latest.stance_perc_l,
        'stance_perc_r': gait_result_latest.stance_perc_r,
        'd_supp_perc_l': gait_result_latest.d_supp_perc_l,
        'd_supp_perc_r': gait_result_latest.d_supp_perc_r,
        'score': gait_result_latest.score,
        'stride_len_normal': stride_len_normal,
        'cycle_time_normal': cycle_time_normal,
        'swing_perc_normal': swing_perc_normal,
        'stance_perc_normal': stance_perc_normal,
        'd_supp_perc_normal': d_supp_perc_normal,
        'velocity_normal': velocity_normal,
        'score_normal': score_normal,
        'gait_data': json.dumps(gait_data),
        'gait_trend_data': json.dumps(trend_data) if trend_data else None,
        'normal_ranges': json.dumps(normal_ranges),
        'code_info': json.dumps(code_info_context, cls=DjangoJSONEncoder)
    }
    if detail is not None:
        return render(request, 'gait_print_kiosk.html', context)
    return render(request, 'gait_print.html', context)


@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
@login_required()
def gait_print_kiosk(request, id):
    return gait_print(request, id, detail=True)


def qr(request):
    return render(request, 'qr.html')






# @api_view(['POST'])
# def register_admin_organization(request):
#     """기관 등록 및 관리자 계정 생성 API

#     Python GUI(tkinter) 애플리케이션에서 호출하는 API로,
#     기관 정보와 관리자 계정 정보를 받아 한 번에 처리합니다.
#     """
#     if request.method == 'POST':
#         data = json.loads(request.body) if isinstance(request.body, bytes) else request.data

#         org_name = data.get('org_name')
#         address = data.get('address')
#         contact_number = data.get('contact_number')
#         admin_id = data.get('admin_id')
#         admin_password = data.get('admin_password')

#         # 필수 파라미터 검증
#         if not all([org_name, address, admin_id, admin_password]):
#             return JsonResponse({
#                 'message': '필수 정보가 누락되었습니다. 기관명, 주소, 관리자 ID, 비밀번호는 필수입니다.',
#                 'status': 'error'
#             }, status=400)

#         try:
#             # 1. 기관 정보 등록
#             if org_name.endswith('학교'):
#                 # 학교인 경우
#                 org, created = SchoolInfo.objects.update_or_create(
#                     school_name=org_name,
#                     defaults={'contact_number': contact_number, 'address': address}
#                 )
#                 user_type = 'S'
#             else:
#                 # 일반 기관인 경우
#                 org, created = OrganizationInfo.objects.update_or_create(
#                     organization_name=org_name,
#                     defaults={'contact_number': contact_number, 'address': address}
#                 )
#                 user_type = 'O'

#             # 2. 관리자 계정 생성
#             user, user_created = UserInfo.objects.update_or_create(
#                 username=admin_id,
#                 defaults={
#                     'password': make_password(admin_password),
#                     'phone_number': admin_id,  # 전화번호 필드에 관리자 ID 사용
#                     'user_type': user_type,
#                     'student_name': f'{org_name} 관리자',
#                     'department': '관리자',
#                 }
#             )

#             # 3. 관리자 계정에 기관 연결
#             if user_type == 'S':
#                 user.school = org
#                 user.organization = None
#             else:
#                 user.organization = org
#                 user.school = None

#             # 4. 키오스크 정보 생성 또는 업데이트
#             kiosk_id = f"kiosk_{org_name.replace(' ', '_')}"
#             kiosk, kiosk_created = KioskInfo.objects.update_or_create(
#                 kiosk_id=kiosk_id,
#                 defaults={
#                     'location': address,
#                     'remark': f'{org_name} 키오스크',
#                     'active': True,
#                     'Org': org if user_type == 'O' else None
#                 }
#             )

#             user.save()

#             return JsonResponse({
#                 'message': '기관 및 관리자 계정이 성공적으로 등록되었습니다.',
#                 'status': 'success',
#                 'data': {
#                     'org_name': org_name,
#                     'admin_id': admin_id,
#                     'kiosk_id': kiosk_id
#                 }
#             }, status=200)

#         except Exception as e:
#             return JsonResponse({
#                 'message': f'오류가 발생했습니다: {str(e)}',
#                 'status': 'error'
#             }, status=500)

#     return JsonResponse({'message': '잘못된 요청입니다.', 'status': 'error'}, status=400)