import os
import re

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import requests
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from analysis.custom.metrics import calculate_active_users
from analysis.helpers import generate_presigned_url, measure_time, parse_userinfo_mobile, upload_image_to_s3, verify_image, check_sms_code, send_sms
from analysis.models import GaitResult, AuthInfo, UserInfo, CodeInfo, BodyResult, SessionInfo, SchoolInfo
from analysis.serializers import GaitResultSerializer, CodeInfoSerializer, BodyResultSerializer, KeypointSerializer

import pytz
from django.core.paginator import Paginator  # 페이지네이션
from concurrent.futures import ThreadPoolExecutor  # 병렬 처리
from django.db.models import Subquery
from datetime import datetime as dt
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

import re

from analysis.swagger import (login_mobile_, login_mobile_id_pw_, login_mobile_uuid_, delete_user_, get_user_, get_code_, get_gait_result_, login_mobile_qr_, get_body_result_, delete_gait_result_, delete_body_result_
                              , mobile_send_auth_sms_, mobile_check_auth_sms_, mobile_signup_)

kst = pytz.timezone('Asia/Seoul')


@swagger_auto_schema(**login_mobile_)
@api_view(['POST'])
def login_mobile(request): # 데이브님 쪽 로직 --> 로그인만 가능 (회원가입 불가)
    mobile_uid = request.data.get('mobile_uid')
    if not mobile_uid:
        return Response({'data': {'message': 'mobile_uid_required', 'status': status.HTTP_400_BAD_REQUEST}}, status=status.HTTP_400_BAD_REQUEST)

    try:
        auth_info = AuthInfo.objects.get(uid=mobile_uid) # AuthInfo 테이블에서 mobile_uid로 검색
    except AuthInfo.DoesNotExist:
        # AuthInfo를 찾을 수 없는 경우 처리 (인증번호 안옴)
        return Response({'data': {'message': 'Not received', 'status': status.HTTP_404_NOT_FOUND}}, status=status.HTTP_200_OK)
    
    # 로그인 로직
    # 인증번호 발신자 전화번호로 DB 쿼리
    # check_user_info = UserInfo.objects.filter(phone_number=auth_info.phone_number)

    # if check_user_info.exists():                            # 회원이 존재한다면
    #     authorized_user_info = check_user_info.first() # 쿼리셋 당김 
    # else:                                                   # 회원이 존재하지 않는다면
    #     auth_info.delete()                # 인증테이블에서 인증번호 정보 삭제                                   
    #     return Response({'data': {'message': 'unregistered user', 'status': status.HTTP_403_FORBIDDEN}}, status=status.HTTP_200_OK)

    # 회원가입 or 로그인 로직
    authorized_user_info, user_created = UserInfo.objects.get_or_create(
        phone_number=auth_info.phone_number,
        defaults=dict(
            username=auth_info.phone_number,
            password=make_password(os.environ['DEFAULT_PASSWORD']),
        ))
        

    if authorized_user_info.school is not None:
        authorized_user_info.user_type = 'S'
    elif authorized_user_info.organization is not None:
        authorized_user_info.user_type = 'O'
    else:
        authorized_user_info.user_type = 'G'

    # authenticate 사용안함 -> last_login 직접 갱신
    authorized_user_info.last_login = dt.now()
    authorized_user_info.save()

    token = TokenObtainPairSerializer.get_token(authorized_user_info)
    refresh_token = str(token)
    access_token = str(token.access_token)

    data_obj = {
        'user_info': parse_userinfo_mobile(authorized_user_info),
        'jwt_tokens': {
            'access_token': access_token,
            'refresh_token': refresh_token,
        },
        'message': 'success',
        'status': status.HTTP_200_OK,
    }

    auth_info.delete()

    return Response({'data': {k: v for k, v in data_obj.items() if v is not None}}, status=status.HTTP_200_OK)



@swagger_auto_schema(**login_mobile_id_pw_)
@api_view(['POST'])
##### ['데이브']쪽에서 사용하는 로직 #####
def login_mobile_id(request):
    id = request.data.get('id')  # phone_number
    password = request.data.get('password')

    if not id or not password:
        return Response({'message': 'id_password_required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        req_user_info = UserInfo.objects.filter(phone_number=id)

        # 등록된 회원이 존재하지 않을 때 처리 -> 관리자가 시스템에 회원을 등록하지 않았을 때
        if not req_user_info.exists():
            return Response({'data': {'message': 'user_not_found', 'status': status.HTTP_404_NOT_FOUND}}, status=status.HTTP_200_OK)
        else:
            req_user_info = req_user_info.first()

        if not check_password(password, req_user_info.password):
            return Response({'message': 'user_not_found', 'status': status.HTTP_404_NOT_FOUND}, status=status.HTTP_200_OK)


        # 마지막 로그인 시간 갱신
        req_user_info.last_login = dt.now()
        req_user_info.save()

        # 초기 비밀번호 상태 확인
        init_passwd_status = check_password(os.environ['DEFAULT_PASSWORD'], req_user_info.password)

        # JWT 토큰 생성
        token = TokenObtainPairSerializer.get_token(req_user_info)
        refresh_token = str(token)
        access_token = str(token.access_token)

        # 데이터 응답 준비
        data_obj = {
            'user_info': parse_userinfo_mobile(req_user_info),
            'jwt_tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token,
            },
            'is_default_password': init_passwd_status,
        }

        return Response({'data': {k: v for k, v in data_obj.items() if v is not None}}, status=status.HTTP_200_OK)

    except UserInfo.DoesNotExist:
        # UserInfo를 찾을 수 없는 경우 처리
        return Response({'message': 'user_not_found'}, status=status.HTTP_200_OK)


@swagger_auto_schema(**login_mobile_uuid_)
@api_view(['POST'])
def login_mobile_uuid(request):
    uuid = request.data.get('uuid')
    if not uuid:
        return Response({'message': 'uuid_required'}, status=status.HTTP_400_BAD_REQUEST)

    auth_info = AuthInfo.objects.update_or_create(uuid=uuid)[0]

    authorized_user_info, user_created = UserInfo.objects.get_or_create(
        phone_number=auth_info.uuid,
        defaults=dict(
            username=auth_info.uuid,
            password=make_password(os.environ['DEFAULT_PASSWORD']),
        ))

    if authorized_user_info.school is not None:
        authorized_user_info.user_type = 'S'
    elif authorized_user_info.organization is not None:
        authorized_user_info.user_type = 'O'
    else:
        authorized_user_info.user_type = 'G'

    authorized_user_info.save()

    token = TokenObtainPairSerializer.get_token(authorized_user_info)
    refresh_token = str(token)
    access_token = str(token.access_token)

    data_obj = {
        'user_info': parse_userinfo_mobile(authorized_user_info),
        'jwt_tokens': {
            'access_token': access_token,
            'refresh_token': refresh_token,
        },
    }

    return Response({'data': {k: v for k, v in data_obj.items() if v is not None}}, status=status.HTTP_200_OK)


@swagger_auto_schema(delete_user_)
@api_view(['POST'])
def delete_user(request):
    user = request.user
    user_id = user.id

    try:
        user_info = UserInfo.objects.get(id=user_id)
    except UserInfo.DoesNotExist:
        return Response(
            {
                'message': 'user_not_found'
            })

    user_info.delete()
    data_obj = {
        'message': 'success',
    }
    return Response({'data': {k: v for k, v in data_obj.items() if v is not None}}, status=status.HTTP_200_OK)


@swagger_auto_schema(**login_mobile_qr_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def login_mobile_qr(request):
    session_key = request.data.get('session_key')
    if not session_key:
        return Response({'message': 'session_key_required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        session_info = SessionInfo.objects.get(session_key=session_key)
    except SessionInfo.DoesNotExist:
        return Response({'message': 'session_key_not_found'}, status=status.HTTP_404_NOT_FOUND)

    session_info.user_id = request.user.id
    session_info.save()

    return Response({'data': {'session_key': session_key}}, status=status.HTTP_200_OK)


# access token으로 사용자 정보 가져오기
# 수정이력 : 240903 BS 작성

@swagger_auto_schema(**get_user_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def get_user(request):
    user = request.user
    user_id = user.id

    try:
        user = UserInfo.objects.get(id=user_id)
    except UserInfo.DoesNotExist:
        return Response(
            {
                'message': 'user_not_found'
            })
    user_info = parse_userinfo_mobile(user)
    data_obj = {
        'user_info': user_info,
        'message': 'success',
    }
    return Response({'data': {k: v for k, v in data_obj.items() if v is not None}}, status=status.HTTP_200_OK)


# group_id 들에 대한 CodeInfo 정보 반환
# @param List group_id_list
# 수정이력 : 240903 BS 작성
@swagger_auto_schema(**get_code_)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_code(request):
    group_id_list = request.query_params.getlist('group_id_list')

    if not group_id_list:
        return Response({'status': 'FAILURE', 'message': 'group_id_list_required'}, status=status.HTTP_400_BAD_REQUEST)

    results = CodeInfo.objects.filter(group_id__in=group_id_list)

    if not results.exists():
        return Response({"" "message": "code_not_found"}, status=status.HTTP_404_NOT_FOUND)

    # Serialize the CodeInfo objects
    serializer = CodeInfoSerializer(results, many=True)

    data = serializer.data
    return Response({'data': data}, status=status.HTTP_200_OK)


# 보행 결과 리스트 반환
# @param String? id : GaitResult의 id
# 수정이력 : 240903 BS 작성
# 수정이력 : 241205 - 페이지 네이션 추가
@swagger_auto_schema(**get_gait_result_)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_gait_result(request):
    user_id = request.user.id

    page_size = request.GET.get("page_size", 10)  # 한 페이지에 보여줄 개수 - 가변적으로 설정 가능
    page = request.GET.get("page", 1)  # 만약 GET 요청에 아무런 정보가 없으면 default 1페이지로 설정

    gait_results = GaitResult.objects.filter(user_id=user_id).order_by('-created_dt')

    # 'id'가 존재하면 created_dt를 기준으로 이전 6개의 결과를 가져오고 내림차순으로 정렬
    id = request.query_params.get('id', None)
    if id is not None:
        gait_results = GaitResult.objects.filter(
            user_id=user_id,
            created_dt__lte=Subquery(
                GaitResult.objects.filter(id=id, user_id=user_id)
                .values('created_dt')[:1]
            )
        ).order_by('-created_dt')[:6]
    else:
        if not gait_results.exists():
            return Response({"message": "gait_result_not_found"}, status=status.HTTP_200_OK)

    # 페이지네이터 선언
    paginator = Paginator(gait_results, page_size)

    try:
        current_page = paginator.page(page)  # 해당 페이지의 객체를 가져옴
    except:
        return Response({"message": "page number out of range"}, status=status.HTTP_400_BAD_REQUEST)

    minimal_gait_results = current_page.object_list  # 현재 페이지의 객체

    # Serialize the GaitResult objects
    serializer = GaitResultSerializer(minimal_gait_results, many=True)

    return Response({
        'data': serializer.data,  # 현재 페이지의 아이템 정보
        'total_pages': paginator.num_pages,  # 전체 페이지 수
        'current_page': int(page),  # 현재 페이지
        'total_items': paginator.count,  # 전체 아이템 개수
        'items': len(minimal_gait_results),  # 현재 페이지의 아이템 개수
    }, status.HTTP_200_OK)


# group_id 들에 대한 CodeInfo 정보 반환
# @param String? id : GaitResult의 id
# 수정이력 : 240903 BS 작성
# 수정이력 : 241203 - 페이지 네이션 추가
# 수정이력 : 241211 - mobile_yn 필터링 추가
# 수정이력 : 241217 - mobile_yn 디폴트 all -> n
@swagger_auto_schema(**get_body_result_)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_body_result(request):
    user_id = request.user.id
    page_size = request.GET.get("page_size", 10)  # 한 페이지에 보여줄 개수 - 가변적으로 설정 가능
    page = request.GET.get("page", 1)  # 만약 GET 요청에 아무런 정보가 없으면 default 1페이지로 설정
    mobile = request.GET.get("mobile", "n")  # mobile_yn 필터링

    # 기본 쿼리셋 정의
    query_filters = {'user_id': user_id}

    # mobile 파라미터가 있는 경우에만 필터 추가
    if mobile is not None:
        query_filters['mobile_yn'] = mobile

    body_results = BodyResult.objects.filter(**query_filters).order_by('-created_dt')

    body_id = request.query_params.get('id', None)
    if body_id is not None:
        current_result = BodyResult.objects.filter(user_id=user_id, id=body_id).first()
        if not current_result:
            return Response({"message": "body_result_not_found"})

        body_results = BodyResult.objects.filter(
            user_id=user_id,
            created_dt__lte=current_result.created_dt
        ).order_by('-created_dt')[:7]
    else:
        if not body_results.exists():
            return Response({"message": "body_result_not_found"}, status=status.HTTP_200_OK)

    paginator = Paginator(body_results, page_size)  # 페이지네이터 생성

    try:
        currnet_page = paginator.page(page)  # 해당 페이지의 객체를 n개씩 가져옴
    except:
        return Response({"message": "page number out of range"}, status=status.HTTP_400_BAD_REQUEST)

    minimal_body_results = currnet_page.object_list  # 현재 페이지의 객체의 정보를 대입

    # 수정된 body_results를 리스트로 저장
    """ body_result -> 페이지네이션 처리 후 페이지 사이즈만큼의 쿼리셋 -> 
        minimal_body_results -> S3 이미지 객체를 S3 미리 서명된 URL로 변환 ->  
        updated_body_results """
    updated_body_results = []

    # body_result 객체를 받아서 이미지 URL을 생성하고, 상태를 확인
    def process_body_result(body_result):
        # Presigned URL 생성 및 상태 확인.
        created_dt = body_result.created_dt.strftime('%Y%m%dT%H%M%S%f')
        body_result.image_front_url = generate_presigned_url(file_keys=['front', created_dt])
        body_result.image_side_url = generate_presigned_url(file_keys=['side', created_dt])

        # URL 검증
        if requests.get(body_result.image_front_url).status_code in [400, 404]:
            body_result.image_front_url = None
        if requests.get(body_result.image_side_url).status_code in [400, 404]:
            body_result.image_side_url = None

        return body_result

    # 병렬 처리로 minimal_body_results 순회
    with ThreadPoolExecutor(max_workers=10) as executor:
        updated_body_results = list(executor.map(process_body_result, minimal_body_results))
    # 모든 객체를 한 번에 업데이트
    BodyResult.objects.bulk_update(updated_body_results, ['image_front_url', 'image_side_url'])

    # Serialize the BodyResult objects
    serializer = BodyResultSerializer(minimal_body_results, many=True)

    # 페이지네이션 INFO 및 정보 가공
    response_data = {
        'data': serializer.data,  # 현재 페이지의 아이템 정보
        'total_pages': paginator.num_pages,  # 전체 페이지 수
        'current_page': int(page),  # 현재 페이지
        'total_items': paginator.count,  # 전체 아이템 개수
        'items': minimal_body_results.count(),  # 현재 페이지의 아이템 개수
    }

    return Response(response_data, status=status.HTTP_200_OK)



@swagger_auto_schema(**delete_gait_result_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_gait_result(request):
    user_id = request.user.id
    gait_id = request.query_params.get('id', None)
    if not gait_id:
        return Response({'data': {'message': 'gait_id_required', 'status': 400}})
    current_result = GaitResult.objects.filter(user_id=user_id, id=gait_id).first()
    if not current_result:
        return Response({"message": "gait_result_not_found"}, )
    current_result.delete()

    # Serialize the GaitResult objects
    serializer = GaitResultSerializer(current_result)
    return Response({'data': serializer.data}, status=status.HTTP_200_OK)


@swagger_auto_schema(**delete_body_result_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_body_result(request):
    user_id = request.user.id
    body_id = request.query_params.get('id', None)
    if not body_id:
        return Response({'data': {'message': 'body_id_required', 'status': 400}})
    current_result = BodyResult.objects.filter(user_id=user_id, id=body_id).first()

    ### 모바일 생성 바디스캐너 결과의 경우 KeyPoint도 같이 삭제됨(Keypoint의 Cascade 옵션)

    if not current_result:
        return Response({"message": "body_result_not_found", 'status': status.HTTP_404_NOT_FOUND}, )

    current_result.delete()

    # Serialize the BodyResult objects
    serializer = BodyResultSerializer(current_result)
    return Response({'data': serializer.data}, status=status.HTTP_200_OK)


# @api_view(['GET'])
# @permission_classes([permissions.IsAuthenticated])
# def mobile_gait_sync(request):  # 아직 사용 X

#     # 사용자 Id
#     user_id = request.user.id
#     try:
#         user_gait_id_list = GaitResult.objects.filter(user_id=user_id).values_list('id', flat=True)

#         return Response(
#             {'data': {'message': 'success', 'gait_results': user_gait_id_list, 'items': len(user_gait_id_list)}},
#             status=status.HTTP_200_OK)

#     except UserInfo.DoesNotExist:
#         return Response({'data': {'message': 'user_not_found'}}, status=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(**mobile_send_auth_sms_)
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mobile_send_auth_sms(request):
    phone_number = request.data.get('phone_number', None)
    # 추후 모바일의 UUID 등으로 기기 확인 처리 해야할 것 같음.

    if phone_number is None:
        return Response({'message': 'phone_number_required'}, status=status.HTTP_400_BAD_REQUEST)

    # 전화번호 형식 검사 (010으로 시작하는 11자리 문자열)
    if not re.match(r'^010\d{8}$', phone_number):
        return Response({'message': 'invalid_phone_number_format'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = UserInfo.objects.get(phone_number=phone_number)
        return Response({'message': 'phone_number_already_exists'}, status=status.HTTP_400_BAD_REQUEST)
    except UserInfo.DoesNotExist:
        pass

    result = send_sms(phone_number)

    if (result == 'sent'): # 정상 전송
        return Response({'message': 'success'}, status=status.HTTP_200_OK)
    elif (result == 'limit'): # 발송 제한(7일 총 10총 까지 가능) - 비정상 사용 방지
        return Response({"message": "too_many_requests"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    else: # 그 외 경우
        return Response({'message': 'not sent'}, status=status.HTTP_200_OK)  # 여러 오류


@swagger_auto_schema(**mobile_check_auth_sms_)
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mobile_check_auth_sms(request):
    phone_number = request.data.get('phone_number')
    auth_code = request.data.get('auth_code')

    if not phone_number or not auth_code:
        return Response({'message': 'phone_number_or_auth_code_required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = check_sms_code(phone_number, auth_code)

        if result:
            return Response({'message': 'success'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'auth_code incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({'message': str(e), 'status': 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@swagger_auto_schema(**mobile_signup_)
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mobile_signup(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    dob = request.data.get('dob', None)
    gender = request.data.get('gender', None)

    # 전화번호 형식 검사 (010으로 시작하는 11자리)
    if not phone_number or not re.match(r'^010\d{8}$', phone_number):
        return Response({'message': 'invalid_phone_number_format'}, status=status.HTTP_400_BAD_REQUEST) # 잘못된 전화번호 형식 - Error Code 2

    if not phone_number or not password:
        return Response({'message': 'phone_number_and_password_required'}, status=status.HTTP_400_BAD_REQUEST) # 전화번호와 비밀번호 필수 - Error Code 4

    if dob is not None:
        # YYYY 형태의 문자열인지 확인 (년도만 입력받음)
        if len(str(dob)) != 4:
            return Response({'message': 'invalid_dob_format'}, status=status.HTTP_400_BAD_REQUEST) # 잘못된 생년월일 형식 - Error Code 2
    
    if gender is not None:
        # 0, 1로 입력 받아서 확인을 거치고, 0: M, 1: F로 변환
        if gender not in ['0', '1']:
            return Response({'message': 'invalid_gender_format'}, status=status.HTTP_400_BAD_REQUEST) # 잘못된 성별 형식 - Error Code 2
        else:
            gender_format = 'M' if gender == '0' else 'F'  # Correct assignment


    authorized_user_info, user_created = UserInfo.objects.get_or_create(
        phone_number=phone_number,
        defaults=dict(
            username=phone_number,
            password=make_password(password),
            student_name=phone_number,
            user_type='G',
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

    return Response({'message': 'success'}, status=status.HTTP_200_OK)