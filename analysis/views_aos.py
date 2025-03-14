import os
from concurrent.futures import ThreadPoolExecutor
from django.contrib.auth.hashers import make_password
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from drf_yasg.utils import swagger_auto_schema

from analysis.custom.metrics import calculate_active_users
from analysis.helpers import (
     upload_image_to_s3, verify_image, parse_userinfo_mobile
)
from analysis.models import (
    BodyResult, SchoolInfo, UserInfo, AuthInfo
)
from analysis.serializers import (
    BodyResultSerializer, KeypointSerializer,
)

from datetime import datetime as dt


# / *********************************************************************** /

# / ***********************  (체형분석앱) 로직   ****************************** /

from analysis.swagger import login_mobile_register_, mobile_create_body_result_, mobile_body_sync_

import pytz

kst = pytz.timezone('Asia/Seoul')


@swagger_auto_schema(**login_mobile_register_)
@api_view(['POST'])
def login_mobile_register(request):  # 제리님 쪽 로직 --> 로그인 / 회원가입 가능
    mobile_uid = request.data.get('mobile_uid')
    if not mobile_uid:
        return Response({'data': {'message': 'mobile_uid_required', 'status': status.HTTP_400_BAD_REQUEST}},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        auth_info = AuthInfo.objects.get(uid=mobile_uid)  # AuthInfo 테이블에서 mobile_uid로 검색
    except AuthInfo.DoesNotExist:
        # AuthInfo를 찾을 수 없는 경우 처리 (인증번호 안옴)
        return Response({'message': 'user_not_found'}, status=status.HTTP_200_OK)

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


@swagger_auto_schema(**mobile_body_sync_)
@api_view(['GET'])
###### 해당 코드는 ['Jerry']님 쪽에서 사용되는 로직 ######
@permission_classes([permissions.IsAuthenticated])
def mobile_body_sync(request):
    # 사용자 Id
    user_id = request.user.id
    try:
        user_body_id_list = BodyResult.objects.filter(user_id=user_id, mobile_yn='y').values_list('id', flat=True)

        return Response(
            {'data': {'message': 'success', 'body_results': user_body_id_list, 'items': len(user_body_id_list)}},
            status=status.HTTP_200_OK)

    except UserInfo.DoesNotExist:
        return Response({'data': {'message': 'user_not_found'}}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({'data': {'message': str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(**mobile_create_body_result_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_body_result(request) -> Response:
    user_id = request.user.id
    if not user_id:
        return Response({'data': {'message': 'token_required'}}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 데이터 추출
        front_data = request.data.get('front_data', {})
        side_data = request.data.get('side_data', {})

        # results 데이터 병합
        body_data = {
            **front_data.get('results', {}),
            **side_data.get('results', {}),
            'mobile_yn': 'y',
            'user': user_id
        }

        # 사용자 정보 확인
        try:
            user_info = UserInfo.objects.get(id=user_id)
        except UserInfo.DoesNotExist:  # 유저가 존재하지 않는 경우
            return Response({'data': {'message': 'user_not_found'}}, status=status.HTTP_401_UNAUTHORIZED)

        # null_school 처리
        null_school, created = SchoolInfo.objects.get_or_create(
            id=-1,
            defaults={'school_name': 'N/A', 'contact_number': 'N/A'}
        )

        # 학교 정보 설정
        if user_info.school is None:
            body_data['school'] = null_school.id  # 학교가 없는 경우 id -1로 저장
        else:  # 학교가 있는 경우 해당 유저의 반, 학년, 학번을 저장
            body_data['school'] = user_info.school.id
            body_data['student_grade'] = user_info.student_grade
            body_data['student_class'] = user_info.student_number
            body_data['student_number'] = user_info.student_number

        body_data['image_front_url'] = 'Not_yet_queried'  # 임시 데이터
        body_data['image_side_url'] = 'Not_yet_queried'  # 추후 체형 분석 결과 쿼리 시 Image URL로 변경됨

        # BodyResult 생성
        serializer = BodyResultSerializer(data=body_data)
        if not serializer.is_valid():
            return Response({'data': {'message': serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            body_result = serializer.save()  # BodyResult 저장

            # 이미지 처리
            # created_dt = dt.now().strftime('%Y%m%dT%H%M%S%f')
            # String -> datetime 변환 후 날짜포맷 설정
            _db_created_dt = dt.strptime(serializer.data['created_dt'], '%Y-%m-%dT%H:%M:%S.%f')

            created_dt = _db_created_dt.strftime('%Y%m%dT%H%M%S%f')

            image_front = request.data.get('image_front')
            image_side = request.data.get('image_side')

            if image_front and image_side:
                try:
                    verified_front = verify_image(image_front)
                    verified_side = verify_image(image_side)

                    # 병렬로 이미지 업로드
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        futures = [
                            executor.submit(upload_image_to_s3, verified_front, ['front', created_dt]),
                            executor.submit(upload_image_to_s3, verified_side, ['side', created_dt])
                        ]
                        for future in futures:
                            future.result()  # 모든 업로드가 완료될 때까지 대기

                except ValueError as ve:
                    raise ValueError(f"Invalid image format: {str(ve)}")
            else:  # 이미지 누락 처리
                missing_images = []
                if not image_front: missing_images.append("image_front")
                if not image_side: missing_images.append("image_side")
                raise ValueError(f"Missing images: {', '.join(missing_images)}")

            # Front Keypoints 저장
            front_keypoints = front_data.get('keypoints', [])
            if len(front_keypoints) == 33:  # keypoints는 총 33개의 데이터여야 함
                front_keypoint_data = {
                    'body_result': body_result.id,
                    'pose_type': 'front',
                    'x': [float(kp['x']) for kp in front_keypoints],
                    'y': [float(kp['y']) for kp in front_keypoints],
                    'z': [float(kp['z']) for kp in front_keypoints],
                    'visibility': [float(kp['visibility']) for kp in front_keypoints],
                    'presence': [float(kp['presence']) for kp in front_keypoints]
                }
                front_keypoint_serializer = KeypointSerializer(data=front_keypoint_data)
                if not front_keypoint_serializer.is_valid():
                    raise ValueError(f"Invalid front keypoints: {front_keypoint_serializer.errors}")
                front_keypoint_serializer.save()
            else:
                raise ValueError(f"Invalid front keypoints: {front_keypoints}")  # front_keypoints != 33

            # Side Keypoints 저장
            side_keypoints = side_data.get('keypoints', [])
            if len(side_keypoints) == 33:
                side_keypoint_data = {
                    'body_result': body_result.id,
                    'pose_type': 'side',
                    'x': [float(kp['x']) for kp in side_keypoints],
                    'y': [float(kp['y']) for kp in side_keypoints],
                    'z': [float(kp['z']) for kp in side_keypoints],
                    'visibility': [float(kp['visibility']) for kp in side_keypoints],
                    'presence': [float(kp['presence']) for kp in side_keypoints]
                }
                side_keypoint_serializer = KeypointSerializer(data=side_keypoint_data)
                if not side_keypoint_serializer.is_valid():
                    raise ValueError(f"Invalid side keypoints: {side_keypoint_serializer.errors}")
                side_keypoint_serializer.save()
            else:
                raise ValueError(f"Invalid side keypoints: {side_keypoints}")

        calculate_active_users()  # 활성 사용자 갱신

        return Response(  # 200(생성) 응답
            {'data': {'message': 'created_body_result', 'id': serializer.data['id']}},
            status=status.HTTP_200_OK
        )

    except ValueError as ve:
        return Response({'data': {'message': str(ve)}}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'data': {'message': str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
