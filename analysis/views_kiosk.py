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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.views import PasswordChangeView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta
from .helpers import extract_digits, generate_presigned_url, parse_userinfo_kiosk, upload_image_to_s3, verify_image, \
    calculate_normal_ratio, create_excel_report, session_check_expired, check_sms_code, send_sms
from .models import BodyResult, CodeInfo, GaitResult, OrganizationInfo, SchoolInfo, UserInfo, SessionInfo, UserHist, KioskInfo, KioskCount
from .forms import UploadFileForm, CustomPasswordChangeForm, CustomUserCreationForm, CustomPasswordResetForm
from .serializers import BodyResultSerializer, GaitResponseSerializer, GaitResultSerializer, SessionInfoSerializer, KioskInfoSerializer, KeypointSerializer

from django.db.models import Min, Max, Exists, OuterRef, Count
from django.db.models.functions import ExtractYear
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from datetime import datetime as dt
from collections import defaultdict
from django.http import JsonResponse, HttpResponse
from urllib.parse import quote
from django.db.models import Q

from analysis.swagger import (
    kiosk_create_gait_result_, kiosk_get_gait_result_, kiosk_get_info_, kiosk_create_body_result_, kiosk_get_body_result_, kiosk_login_kiosk_, kiosk_login_kiosk_id, kiosk_get_userinfo_session_, 
    kiosk_end_session_, kiosk_check_session_, kiosk_use_count_, kiosk_signup_, kiosk_check_sms_, kiosk_send_sms_)


# from .custom.sms_send import NCPSMSSender
# from .custom.redis_func import RedisClient

# 응답코드 관련
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, \
    HTTP_500_INTERNAL_SERVER_ERROR



# KIOSK_LATEST_VERSION = get_kiosk_latest_version()



@swagger_auto_schema(**kiosk_create_gait_result_)
@api_view(['POST'])
def create_gait_result(request):
    session_key = request.data.get('session_key')
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': 400}})
    gait_data = request.data.get('gait_data')
    if not gait_data:
        return Response({'data': {'message': 'gait_data_required', 'status': 400}})

    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return Response({'data': {'message': 'session_key_not_found', 'status': 404}})

    if session_check_expired(session_info): # 세션 만료 체크 및 갱신
        return Response({'data': {'message': 'session_expired', 'status': 403}})

    try:
        user_info = UserInfo.objects.get(id=session_info.user_id)
    except UserInfo.DoesNotExist:
        return Response({'data': {'message': 'user_not_found', 'status': 401}})

    # Retrieve or create a fixed "null school" instance
    null_school, created = SchoolInfo.objects.get_or_create(
        id=-1,
        school_name='N/A',
        contact_number='N/A'
    )

    data = gait_data.copy()

    if user_info.school is None:
        data['school'] = null_school.id
    else:
        data['school'] = user_info.school.id
    data['user'] = user_info.id
    serializer = GaitResultSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response({'data': {'message': 'created_gait_result', 'status': 200}})
    else:
        return Response({'data': {'message': serializer.errors, 'status': 500}})



@swagger_auto_schema(**kiosk_get_gait_result_)
@api_view(['GET'])
def get_gait_result(request):
    if request.user.id is None:
        session_key = request.query_params.get('session_key')
        if not session_key:
            return Response({'data': {'message': 'session_key_required', 'status': 400}})

        try:
            session_info = SessionInfo.objects.get(session_key=session_key)
        except SessionInfo.DoesNotExist:
            return Response({'data': {'message': 'session_key_not_found', 'status': 404}})

        if session_check_expired(session_info):  # 세션 만료 체크 및 갱신
            return Response({'data': {'message': 'session_expired', 'status': 403}})

        try:
            user_info = UserInfo.objects.get(id=session_info.user_id)
        except UserInfo.DoesNotExist:
            return Response({'data': {'message': 'user_not_found', 'status': 401}})
        user_id = user_info.id
    else:
        # for JWT authorized user
        user_id = request.user.id

    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)

    if start_date is not None or end_date is not None:
        # Ensure start_date and end_date are datetime objects
        if not isinstance(start_date, datetime):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if not isinstance(end_date, datetime):
            end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        gait_results = GaitResult.objects.filter(user_id=user_id, created_dt__range=(start_date, end_date)).order_by(
            '-created_dt')
    else:
        gait_results = GaitResult.objects.filter(user_id=user_id).order_by('-created_dt')
        # id 값이 들어오면 해당 검사일자 이전 데이터를 가져온다.(240903 BS)
        id = request.query_params.get('id', None)
        if id is not None:
            current_result = GaitResult.objects.filter(user_id=user_id, id=id).first()
            if not current_result:
                return Response({'data': {"message": "gait_result_not_found"}})
            gait_results = GaitResult.objects.filter(
                user_id=user_id,
                created_dt__lte=current_result.created_dt
            ).order_by('-created_dt')

    if not gait_results.exists():
        return Response({'data': {"message": "gait_result_not_found", "status": 404}})
    count = request.query_params.get('count', None)
    if count is not None:
        gait_results = gait_results.all()[:int(count)]

    # Serialize the GaitResult objects
    serializer = GaitResultSerializer(gait_results, many=True)

    return Response({'data': serializer.data, 'message': 'OK', 'status': 200})



@swagger_auto_schema(**kiosk_get_info_)
@api_view(['GET'])
def get_info(requests):
    name = requests.query_params.get('name')
    if name == 'body':
        group_id = '01'
    elif name == 'gait':
        group_id = '02'
    else:
        return Response({'data': {'message': 'Bad Request. Invalid name!', 'status': 400}})
    codeinfo = CodeInfo.objects.filter(group_id=group_id)
    info = {}
    for item in codeinfo.values():
        info[item['code_id']] = {
            'value_range_min': codeinfo.get(code_id=item['code_id']).min_value,
            'value_range_max': codeinfo.get(code_id=item['code_id']).max_value,
            'normal_range_min': codeinfo.get(code_id=item['code_id']).normal_min_value,
            'normal_range_max': codeinfo.get(code_id=item['code_id']).normal_max_value,
            'caution_range_min': codeinfo.get(code_id=item['code_id']).caution_min_value,
            'caution_range_max': codeinfo.get(code_id=item['code_id']).caution_max_value,
            'unit_name': item['unit_name'],
        }
        if name == 'body':
            info[item['code_id']].update({
                'outline': item['outline'],
                'risk': item['risk'],
                'improve': item['improve'],
                'recommended': item['recommended'],
                'title': item['title'],
                'title_outline': item['title_outline'],
                'title_risk': item['title_risk'],
                'title_improve': item['title_improve'],
                'title_recommended': item['title_recommended'],
            })
        if name == 'gait':
            info[item['code_id']].update({
                'display_ticks': codeinfo.get(code_id=item['code_id']).display_ticks
            })

    return Response({'data': info, 'message': 'OK', 'status': 200})



@swagger_auto_schema(**kiosk_create_body_result_)
@api_view(['POST'])
def create_body_result(request):
    session_key = request.data.get('session_key')
    # session_key가 없는 경우
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': HTTP_400_BAD_REQUEST}},
                        status=HTTP_400_BAD_REQUEST)

    body_data = request.data.get('body_data')

    # body_data가 없는 경우
    if not body_data:
        return Response({'data': {'message': 'body_data_required', 'status': HTTP_400_BAD_REQUEST}},
                        status=HTTP_400_BAD_REQUEST)

    try:
        # session_key를 기반으로 세션 정보 조회
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        # 세션 정보가 없는 경우
        return Response({'data': {'message': 'session_key_not_found', 'status': HTTP_404_NOT_FOUND}},
                        status=HTTP_404_NOT_FOUND)

    if session_check_expired(session_info): # 세션 만료 체크 및 갱신
        return Response({'data': {'message': 'session_expired', 'status': 403}})

    try:
        # 세션 정보에서 사용자 정보 조회
        user_info = UserInfo.objects.get(id=session_info.user_id)
    except UserInfo.DoesNotExist:
        # 사용자 정보가 없는 경우
        return Response({'data': {'message': 'user_not_found', 'status': HTTP_401_UNAUTHORIZED}},
                        status=HTTP_401_UNAUTHORIZED)

    # 사용자의 학교 정보가 없는 경우에 채울 Temp School 정보
    null_school, created = SchoolInfo.objects.update_or_create(
        id=-1,
        defaults=dict(
            school_name='N/A',
            contact_number='N/A'
        )
    )

    data = body_data.copy()
    if user_info.school is None:  # 회원의 학교 정보가 없는 경우
        data['school'] = null_school.id
    else:  # 회원의 학교 정보가 있는 경우
        # 학교 id, 학년, 반, 번호를 저장
        data['school'] = user_info.school.id
        data['student_grade'] = user_info.student_grade
        data['student_class'] = user_info.student_class
        data['student_number'] = user_info.student_number
        data['image_front_url'] = 'Not_yet_queried'
        data['image_side_url'] = 'Not yet queried'

    data['user'] = user_info.id
    serializer = BodyResultSerializer(data=data)

    if serializer.is_valid():
        # 데이터 저장
        serializer.save()
        print(serializer.data)
        # 저장된 데이터의 생성 시간으로 파일 이름 생성
        created_dt = dt.strptime(serializer.data['created_dt'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y%m%dT%H%M%S%f')
        image_front_bytes = request.data.get('image_front', None)
        image_side_bytes = request.data.get('image_side', None)

        try:
            # 이미지 검증 및 업로드
            if image_front_bytes and image_side_bytes:
                try:
                    # 이미지 검증
                    verified_front = verify_image(image_front_bytes)
                    verified_side = verify_image(image_side_bytes)

                    # 검증된 이미지만 업로드
                    upload_image_to_s3(verified_front, file_keys=['front', created_dt])
                    upload_image_to_s3(verified_side, file_keys=['side', created_dt])
                except ValueError as ve:
                    # 이미지 형식이 잘못된 경우
                    return Response(
                        {'data': {'message': f"Invalid image format: {str(ve)}", 'status': HTTP_400_BAD_REQUEST}},
                        status=HTTP_400_BAD_REQUEST)
            else:
                # 누락된 이미지 확인
                missing_images = []
                if not image_front_bytes:
                    missing_images.append("image_front")
                if not image_side_bytes:
                    missing_images.append("image_side")
                return Response({'data': {'message': f"Missing images: {', '.join(missing_images)}",
                                          'status': HTTP_400_BAD_REQUEST}}, status=HTTP_400_BAD_REQUEST)

        except Exception as e:
            # 기타 예외 발생 시
            return Response({'data': {'message': str(e), 'status': HTTP_500_INTERNAL_SERVER_ERROR}},
                            status=HTTP_500_INTERNAL_SERVER_ERROR)

        # 성공 응답
        return Response({'data': {'message': 'created_body_result', 'status': HTTP_200_OK}}, status=HTTP_200_OK)
    else:
        # Serializer 유효성 검사 실패
        return Response({'data': {'message': serializer.errors, 'status': HTTP_500_INTERNAL_SERVER_ERROR}},
                        status=HTTP_500_INTERNAL_SERVER_ERROR)


# @swagger_auto_schema(**kiosk_create_body_result_)
# @api_view(['POST'])
# def create_body_result(request):
#     session_key = request.data.get('session_key')
#     # session_key가 없는 경우
#     if not session_key:
#         return Response({'data': {'message': 'session_key_required', 'status': HTTP_400_BAD_REQUEST}},
#                         status=HTTP_400_BAD_REQUEST)


#     body_data = request.data.get('body_data')
#     front_data = request.data.get('front_data', {})
#     side_data = request.data.get('side_data', {})

#     # body_data가 없는 경우
#     if not body_data:
#         return Response({'data': {'message': 'body_data_required', 'status': HTTP_400_BAD_REQUEST}},
#                         status=HTTP_400_BAD_REQUEST)

#     if not front_data or not side_data:
#         return Response({'data': {'message': 'front_and_side_data_required', 'status': HTTP_400_BAD_REQUEST}},
#                         status=HTTP_400_BAD_REQUEST)

#     try:
#         # session_key를 기반으로 세션 정보 조회
#         session_info = SessionInfo.objects.get(session_key=session_key)
#     except SessionInfo.DoesNotExist:
#         # 세션 정보가 없는 경우
#         return Response({'data': {'message': 'session_key_not_found', 'status': HTTP_404_NOT_FOUND}},
#                         status=HTTP_404_NOT_FOUND)

#     if session_check_expired(session_info): # 세션 만료 체크 및 갱신
#         return Response({'data': {'message': 'session_expired', 'status': 403}})

#     try:
#         # 세션 정보에서 사용자 정보 조회
#         user_info = UserInfo.objects.get(id=session_info.user_id)
#     except UserInfo.DoesNotExist:
#         # 사용자 정보가 없는 경우
#         return Response({'data': {'message': 'user_not_found', 'status': HTTP_401_UNAUTHORIZED}},
#                         status=HTTP_401_UNAUTHORIZED)

#     # 사용자의 학교 정보가 없는 경우에 채울 Temp School 정보
#     null_school, created = SchoolInfo.objects.update_or_create(
#         id=-1,
#         defaults=dict(
#             school_name='N/A',
#             contact_number='N/A'
#         )
#     )

#     data = body_data.copy()
#     if user_info.school is None:  # 회원의 학교 정보가 없는 경우
#         data['school'] = null_school.id
#     else:  # 회원의 학교 정보가 있는 경우
#         # 학교 id, 학년, 반, 번호를 저장
#         data['school'] = user_info.school.id
#         data['student_grade'] = user_info.student_grade
#         data['student_class'] = user_info.student_class
#         data['student_number'] = user_info.student_number
#         data['image_front_url'] = 'N'
#         data['image_side_url'] = 'N'
#         data['front_data'] = front_data.get('results', {}),
#         data['side_data'] = side_data.get('results', {}),

#     data['user'] = user_info.id
#     serializer = BodyResultSerializer(data=data)

#     if serializer.is_valid():
#         # 데이터 저장
#         body_result = serializer.save()
#         # print(serializer.data)

#         # 저장된 데이터의 생성 시간으로 파일 이름 생성
#         created_dt = dt.strptime(serializer.data['created_dt'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y%m%dT%H%M%S%f')
#         image_front_bytes = request.data.get('image_front', None)
#         image_side_bytes = request.data.get('image_side', None)

#         try:
#             # 이미지 검증 및 업로드
#             if image_front_bytes and image_side_bytes:
#                 try:
#                     # 이미지 검증
#                     verified_front = verify_image(image_front_bytes)
#                     verified_side = verify_image(image_side_bytes)

#                     # 검증된 이미지만 업로드
#                     upload_image_to_s3(verified_front, file_keys=['front', created_dt])
#                     upload_image_to_s3(verified_side, file_keys=['side', created_dt])
#                 except ValueError as ve:
#                     # 이미지 형식이 잘못된 경우
#                     return Response(
#                         {'data': {'message': f"Invalid image format: {str(ve)}", 'status': HTTP_400_BAD_REQUEST}},
#                         status=HTTP_400_BAD_REQUEST)
#             else:
#                 # 누락된 이미지 확인
#                 missing_images = []
#                 if not image_front_bytes:
#                     missing_images.append("image_front")
#                 if not image_side_bytes:
#                     missing_images.append("image_side")
#                 return Response({'data': {'message': f"Missing images: {', '.join(missing_images)}",
#                                           'status': HTTP_400_BAD_REQUEST}}, status=HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             # 기타 예외 발생 시
#             return Response({'data': {'message': str(e), 'status': HTTP_500_INTERNAL_SERVER_ERROR}},
#                             status=HTTP_500_INTERNAL_SERVER_ERROR)


#         try:
#             # Front Keypoints 저장
#             front_keypoints = front_data.get('keypoints', [])
#             if len(front_keypoints) == 33:  # keypoints는 총 33개의 데이터여야 함
#                 front_keypoint_data = {
#                     'body_result': body_result.id,
#                     'pose_type': 'front',
#                     'x': [float(kp['x']) for kp in front_keypoints],
#                     'y': [float(kp['y']) for kp in front_keypoints],
#                     'z': [float(kp['z']) for kp in front_keypoints],
#                     'visibility': [float(kp['visibility']) for kp in front_keypoints],
#                     'presence': [float(kp['presence']) for kp in front_keypoints]
#                     }
#                 front_keypoint_serializer = KeypointSerializer(data=front_keypoint_data)
#                 if not front_keypoint_serializer.is_valid():
#                     raise ValueError(f"Invalid front keypoints: {front_keypoint_serializer.errors}")
#                 front_response = front_keypoint_serializer.save()
#                 print(front_response)
#             else:
#                 raise ValueError(f"Invalid front keypoints: {front_keypoints}")  # front_keypoints != 33

#             # Side Keypoints 저장
#             side_keypoints = side_data.get('keypoints', [])
#             if len(side_keypoints) == 33:
#                 side_keypoint_data = {
#                     'body_result': body_result.id,
#                     'pose_type': 'side',
#                     'x': [float(kp['x']) for kp in side_keypoints],
#                     'y': [float(kp['y']) for kp in side_keypoints],
#                     'z': [float(kp['z']) for kp in side_keypoints],
#                     'visibility': [float(kp['visibility']) for kp in side_keypoints],
#                     'presence': [float(kp['presence']) for kp in side_keypoints]
#                 }
#                 side_keypoint_serializer = KeypointSerializer(data=side_keypoint_data)
#                 if not side_keypoint_serializer.is_valid():
#                     raise ValueError(f"Invalid side keypoints: {side_keypoint_serializer.errors}")
#                 side_response = side_keypoint_serializer.save()
#                 print(side_response)
#             else:
#                 raise ValueError(f"Invalid side keypoints: {side_keypoints}")
#         except Exception as e:
#         # 기타 예외 발생 시
#             return Response({'data': {'message': str(e), 'status': HTTP_500_INTERNAL_SERVER_ERROR}},
#                             status=HTTP_500_INTERNAL_SERVER_ERROR)


#         # 성공 응답
#         return Response({'data': {'message': 'created_body_result', 'status': HTTP_200_OK}}, status=HTTP_200_OK)
#     else:
#         # Serializer 유효성 검사 실패
#         return Response({'data': {'message': serializer.errors, 'status': HTTP_500_INTERNAL_SERVER_ERROR}},
#                         status=HTTP_500_INTERNAL_SERVER_ERROR)




@swagger_auto_schema(**kiosk_get_body_result_)
@api_view(['GET'])
def get_body_result(request):
    if request.user.id is None:
        session_key = request.query_params.get('session_key')
        if not session_key:
            return Response({'data': {'message': 'session_key_required', 'status': 400}})

        try:
            session_info = SessionInfo.objects.get(session_key=session_key)
        except SessionInfo.DoesNotExist:
            return Response({'data': {'message': 'session_key_not_found', 'status': 404}})

        if session_check_expired(session_info):  # 세션 만료 체크 및 갱신
            return Response({'data': {'message': 'session_expired', 'status': 403}})

        try:
            user_info = UserInfo.objects.get(id=session_info.user_id)
        except UserInfo.DoesNotExist:
            return Response({'data': {'message': 'user_not_found', 'status': 401}})
        user_id = user_info.id
    else:
        # for JWT authorized user
        user_id = request.user.id
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)

    if start_date is not None or end_date is not None:
        # Ensure start_date and end_date are datetime objects
        if not isinstance(start_date, datetime):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if not isinstance(end_date, datetime):
            end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        body_results = BodyResult.objects.filter(user_id=user_id, created_dt__range=(start_date, end_date), mobile_yn='n').order_by(
            '-created_dt')
    else:
        body_results = BodyResult.objects.filter(user_id=user_id).order_by('-created_dt')
        id = request.query_params.get('id', None)
        if id is not None:
            body_results = body_results.filter(id=id)

    if not body_results.exists():
        return Response({'data': {"message": "body_result_not_found", "status": 404}})

    count = request.query_params.get('count', None)
    if count is not None:
        body_results = body_results.all()[:int(count)]

    # 수정된 body_results를 리스트로 저장
    updated_body_results = []

    for body_result in body_results:
        created_dt = body_result.created_dt.strftime('%Y%m%dT%H%M%S%f')
        # Presigned URL 생성 (일정 시간 동안)
        body_result.image_front_url = generate_presigned_url(file_keys=['front', created_dt])
        body_result.image_side_url = generate_presigned_url(file_keys=['side', created_dt])

        if body_result.image_front_url is not None and requests.get(body_result.image_front_url).status_code in [400,
                                                                                                                 404]:
            body_result.image_front_url = None
        if body_result.image_side_url is not None and requests.get(body_result.image_side_url).status_code in [400,
                                                                                                               404]:
            body_result.image_side_url = None

        updated_body_results.append(body_result)

    # 모든 객체를 한 번에 업데이트
    BodyResult.objects.bulk_update(updated_body_results, ['image_front_url', 'image_side_url'])

    # Serialize the BodyResult objects
    serializer = BodyResultSerializer(body_results, many=True)

    return Response({'data': serializer.data, 'message': 'OK', 'status': 200})


from django.db import IntegrityError

@swagger_auto_schema(**kiosk_login_kiosk_)
@api_view(['POST'])
def login_kiosk(request):
    kiosk_id = request.data.get('kiosk_id')
    kiosk_version = request.data.get('version')
    if not kiosk_id:
        return Response({'data': {'message': 'kiosk_id_required', 'status': 400}})

    print(kiosk_id)

    try:
        kiosk_info, created = KioskInfo.objects.update_or_create(
            kiosk_id=kiosk_id,
            defaults={'version': kiosk_version}
        )

        # 키오스크 활성화 여부 체크
        if not kiosk_info.active:
            return Response({'data': {'message': 'kiosk_inactive', 'status': 401}})

        # POST 메소드를 사용하여 키오스크 로그인 요청 처리
        session_key = uuid.uuid4().hex
        
        # 여기가 수정된 부분 - kiosk_id 필드에 kiosk_info 객체를 직접 전달
        SessionInfo.objects.update_or_create(
            session_key=session_key,
            defaults={'kiosk_id': kiosk_info.kiosk_id}
        )

        return Response({'data': {'session_key': session_key, 'message': 'success', 'status': 200}})
    
    except IntegrityError as e:
        print(f"IntegrityError: {e}")
        return Response({'data': {'message': 'database_error', 'status': 500}})




@swagger_auto_schema(**kiosk_login_kiosk_id)
@api_view(['POST'])
def login_kiosk_id(request):
    session_key = request.data.get('session_key')
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': 400}})

    phone_number = request.data.get('phone_number')
    password = request.data.get('password')

    if not phone_number or not password:
        return Response({'data': {'message': 'phone_number_and_password_required', 'status': 400}})

    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return Response({'data': {'message': 'session_key_not_found', 'status': 404}})

    if session_check_expired(session_info): # 세션 만료 체크 및 갱신
        return Response({'data': {'message': 'session_expired', 'status': 403}})

    try:
        user_info = UserInfo.objects.get(phone_number=phone_number)
    except UserInfo.DoesNotExist:
        return Response({'data': {"message": "user_not_found", 'status': 401}})

    if not check_password(password, user_info.password) and (phone_number == user_info.phone_number):
        return Response(
            {'data': {'message': 'incorrect_password', 'status': 401}, 'message': 'incorrect_password', 'status': 401})
    else:
        user_info.last_login = dt.now()  # 마지막 로그인 시간 업데이트
        user_info.save()
        session_info.user_id = user_info.id
        session_info.save()
        return Response(
            {'data': {'message': 'login_success', 'status': 200}, 'message': 'login_success', 'status': 200})



@swagger_auto_schema(**kiosk_get_userinfo_session_)
@api_view(['GET'])
def get_userinfo_session(request):
    session_key = request.query_params.get('session_key')
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': 400}})
    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return Response({'data': {'message': 'session_key_not_found', 'status': 404}})

    if session_check_expired(session_info): # 세션 만료 체크 및 갱신
        return Response({'data': {'message': 'session_expired', 'status': 403}})

    try:
        user_info = UserInfo.objects.get(id=session_info.user_id)
    except UserInfo.DoesNotExist:
        return Response({"data": {"message": "user_not_found", "status": 401}})

    return Response({'data': parse_userinfo_kiosk(user_info), 'message': 'OK', 'status': 200})



@swagger_auto_schema(**kiosk_end_session_)
@api_view(['POST'])
def end_session(request):
    session_key = request.data.get('session_key')
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': 400}})
    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return Response({'data': {'message': 'session_key_not_found', 'status': 404}})

    session_info.delete()
    return Response({'data': {'message': 'session_closed', 'status': 200}, 'message': 'session_closed', 'status': 200})




@swagger_auto_schema(**kiosk_check_session_)
@api_view(['GET'])
def check_session(request):
    session_key = request.query_params.get('session_key')
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': 400}})
    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return Response({'data': {'message': 'session_key_not_found', 'status': 404}})


    if session_check_expired(session_info, check=True): # 체크만 수행하고 갱신하지 않음
        return Response({'data': {'message': 'session_expired', 'status': 403}})
    return Response({'data': {'message': 'session_valid', 'status': 200}})


@swagger_auto_schema(**kiosk_use_count_)
@api_view(['POST'])
def kiosk_use_count(request):
    session_key = request.data.get("session_key")
    if not session_key:
        return Response({'data': {'message': 'session_key_required', 'status': 400}})
    
    count_type = request.data.get("type")
    
    try:
        session_info = SessionInfo.objects.get(session_key=session_key)  # 현재 키오스크 세션 정보 조회

        session_info_serialized = SessionInfoSerializer(session_info).data
        print("Session Info:", session_info_serialized)  # 디버그 출력

        request_kiosk = session_info.kiosk  # 수정: kiosk_id를 가져옴
       
        # type1, type2 = 회원 보행 / 체형
        # type3, type4 = 비회원 보행 / 체형
        # Requset의 type별로 KioskCount의 req{n}의 컬럼을 1씩 증감
        # KioskCount 객체 생성 시 KioskInfo 객체를 전달
        kiosk_count, created = KioskCount.objects.get_or_create(kiosk=request_kiosk)  # kiosk 필드에 KioskInfo 객체 전달
    
        # 기존 값에 1을 더함
        current_value = getattr(kiosk_count, f'type{count_type}', 0)
        setattr(kiosk_count, f'type{count_type}', current_value + 1)
        kiosk_count.save()
    
        return Response({'data': {'message': 'success', 'status': 200}})
    
    except SessionInfo.DoesNotExist:
        return Response({'data': {'message': 'session_key_not_found', 'status': 404}})
    
    except KioskCount.DoesNotExist:
        return Response({'data': {'message': 'kiosk_id_not_found', 'status': 404}})

    

@swagger_auto_schema(**kiosk_signup_)
@api_view(['POST'])
def kiosk_signup(request):
    session_key = request.data.get('session_key')
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    dob = request.data.get('dob', None)
    gender = request.data.get('gender', None)
    auth_code = request.data.get('auth_code')

    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return JsonResponse({'data': {'message': 'session_key_not_found', 'status': 1}}) # 세션 키 없음 - Error Code 1

    # 전화번호 형식 검사 (010으로 시작하는 11자리)
    if not phone_number or not re.match(r'^010\d{8}$', phone_number):
        return JsonResponse({'message': 'invalid_phone_number_format', 'status': 2}) # 잘못된 전화번호 형식 - Error Code 2

    try:
        UserInfo.objects.get(phone_number=phone_number)
        return JsonResponse({'message': 'phone_number_already_exists', 'status': 3}) # 전화번호 중복 - Error Code 3
    except UserInfo.DoesNotExist:
        pass

    if not phone_number or not password:
        return JsonResponse({'message': 'phone_number_and_password_required', 'status': 4}) # 전화번호와 비밀번호 필수 - Error Code 4

    if dob is not None:
        # YYYY 형태의 문자열인지 확인 (년도만 입력받음)
        if len(str(dob)) != 4:
            return JsonResponse({'message': 'invalid_dob_format', 'status': 2}) # 잘못된 생년월일 형식 - Error Code 2
    
    if gender is not None:
        # 0, 1로 입력 받아서 확인을 거치고, 0: M, 1: F로 변환
        if gender not in ['0', '1']:
            return JsonResponse({'message': 'invalid_gender_format', 'status': 2}) # 잘못된 성별 형식 - Error Code 2
        else:
            gender_format = 'M' if gender == '0' else 'F'  # Correct assignment

    # 세션 키로 해당 키오스크가 사용되고 있는 기관 정보 조회
    kiosk_id = session_info.kiosk_id
    kiosk_info = KioskInfo.objects.filter(kiosk_id=kiosk_id).first()
    if not kiosk_info:
        return JsonResponse({'message': 'kiosk_not_found', 'status': 5})
    
    try:
        result = check_sms_code(phone_number, auth_code)

        if result:
            pass
        else:
            return JsonResponse({'message': 'auth_code not equals', 'status': 5}, status=HTTP_200_OK) # 인증번호 불일치 - Error Code 5 
    
    except Exception as e:
        return JsonResponse({'message': str(e), 'status': 500})

    kiosk_use_org = kiosk_info.Org

    
    if phone_number == '01065751635':
        return JsonResponse({'message': 'success', 'status': 0}) # 테스트용 전화번호 - Error Code 0

    authorized_user_info, user_created = UserInfo.objects.get_or_create(
        phone_number=phone_number,
        defaults=dict(
            username=phone_number,
            password=make_password(password),
            department='방문자',
            student_name=phone_number,
            user_type='O',
            organization=kiosk_use_org if not kiosk_use_org else None,
            dob=dob if dob is not None else None, 
            gender=gender_format if gender is not None else None
        ))

    if authorized_user_info.school is not None:
        authorized_user_info.user_type = 'S'
    elif authorized_user_info.organization is not None:
        authorized_user_info.user_type = 'O'
    else:
        authorized_user_info.user_type = 'G'

    authorized_user_info.save()  # 사용자 타입 변경 후 저장 추가

    return JsonResponse({'message': 'success', 'status': 0})


@swagger_auto_schema(**kiosk_send_sms_)
@api_view(['POST'])
def kiosk_send_sms(request):
    phone_number = request.data.get('phone_number')
    session_key = request.data.get('session_key')

    if not phone_number or not session_key:
        return JsonResponse({'message': 'phone_number_or_session_key_required', 'status': 400}, status=HTTP_200_OK)
    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return JsonResponse({'data': {'message': 'session_key_not_found', 'status': 3}}, status=HTTP_200_OK)

    # 전화번호 형식 검사 (010으로 시작하는 11자리 문자열)
    if not re.match(r'^010\d{8}$', phone_number):
        return JsonResponse({'message': 'invalid_phone_number_format', 'status': 1}, status=HTTP_200_OK)
    
    try:
        user = UserInfo.objects.get(phone_number=phone_number)

        if user.phone_number == '01065751635':
            pass

        return JsonResponse({'message': 'phone_number_already_exists', 'status': 2}, status=HTTP_200_OK)
    except UserInfo.DoesNotExist:
        pass

    
    result = send_sms(phone_number)

    if (result == 'send'):
        return JsonResponse({'message': 'success', 'status': 0}, status=HTTP_200_OK)
    else:
        return JsonResponse({'message': 'failed', 'status': 500}, status=HTTP_200_OK)


@swagger_auto_schema(**kiosk_check_sms_)
@api_view(['POST'])
def kiosk_check_sms(request):
    phone_number = request.data.get('phone_number')
    session_key = request.data.get('session_key')
    auth_code = request.data.get('auth_code')

    if not phone_number or not session_key or not auth_code:
        return JsonResponse({'message': 'phone_number_or_session_key_or_auth_code_required', 'status': 400}, status=HTTP_200_OK)

    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return JsonResponse({'data': {'message': 'session_key_not_found', 'status': 400}}, status=HTTP_200_OK)
    
    try:
        result = check_sms_code(phone_number, auth_code)

        if result:
            return JsonResponse({'message': 'success', 'status': 200}, status=HTTP_200_OK)
        else:
            return JsonResponse({'message': 'failed', 'status': 400}, status=HTTP_200_OK)
    
    except Exception as e:
        return JsonResponse({'message': str(e), 'status': 500})