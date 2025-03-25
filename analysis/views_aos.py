import os
from concurrent.futures import ThreadPoolExecutor
from django.contrib.auth.hashers import make_password
from django.db import transaction

import requests
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.paginator import Paginator  # 페이지네이션

from drf_yasg.utils import swagger_auto_schema

from analysis.custom.metrics import calculate_active_users
from analysis.helpers import (
     upload_image_to_s3, verify_image, parse_userinfo_mobile, generate_presigned_url
)
from analysis.models import (
    BodyResult, SchoolInfo, UserInfo, AuthInfo, FamilyUserInfo
)
from analysis.serializers import (
    BodyResultSerializer, KeypointSerializer, FamilyUserInfoSerializer, FamilyUserResponseSerializer
)

from datetime import datetime as dt





# / *********************************************************************** /

# / ***********************  (체형분석앱) 로직   ****************************** /

from analysis.swagger import login_mobile_register_, mobile_create_body_result_, mobile_body_sync_, create_family_user_, select_family_user_, get_body_result_aos_, delete_family_user_, get_body_result_aos_id_

import pytz

kst = pytz.timezone('Asia/Seoul')



# family_user_id 입력이 없으면 전체 아니면 0 이면 해당 ID만 나머지는 user_id와 family_user_id 기준으로 필터링

@swagger_auto_schema(**get_body_result_aos_)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_body_result_aos(request):
    user_id = request.user.id
    page_size = request.GET.get("page_size", 10)  # 한 페이지에 보여줄 개수 - 가변적으로 설정 가능
    page = request.GET.get("page", 1)  # 만약 GET 요청에 아무런 정보가 없으면 default 1페이지로 설정
    mobile = request.GET.get("mobile", "n")  # mobile_yn 필터링

    family_user_id = request.GET.get("family_user_id", None)  # family_yn 필터링
    

    # 기본 쿼리셋 정의
    query_filters = {'user_id': user_id}

    # mobile 파라미터가 있는 경우에만 필터 추가
    if mobile is not None:
        query_filters['mobile_yn'] = mobile
    if family_user_id is not None:
        if family_user_id == '0':
            # family_user_id가 0일 경우 모든 결과 조회
            pass
        else:
            query_filters['family_user_id'] = family_user_id
    else:
        # family_user_id가 입력되지 않았을 경우 NULL인 것 제외
        query_filters['family_user_id__isnull'] = True

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



@swagger_auto_schema(**get_body_result_aos_id_)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_body_result_aos_id(request, id):
    user_id = request.user.id

    if not id:  # body_id가 없는 경우
        return Response({'data': {'message': 'body_id_required'}}, status=status.HTTP_400_BAD_REQUEST)

    # keypoints 같이 조회
    body_result = BodyResult.objects.prefetch_related('keypoints').filter(
        user_id=user_id,
        id=id
    ).first()
    if body_result is None:  # body_result가 없는 경우(존재하지 않거나, 회원 id와 매칭되는 body_result가 아닌경우)
        return Response({'data': {'message': 'body_result_not_found'}}, status=status.HTTP_404_NOT_FOUND)

    try:
        # 이미지 URL 생성
        created_dt = body_result.created_dt.strftime('%Y%m%dT%H%M%S%f')
        image_front_url = generate_presigned_url(file_keys=['front', created_dt])
        image_side_url = generate_presigned_url(file_keys=['side', created_dt])

        # image_front_url, image_side_url 1시간 접근 가능 URL 업데이트
        body_result.image_front_url = image_front_url
        body_result.image_side_url = image_side_url
        body_result.save()

        # Front data 구성
        front_data = {
            'results': {
                'shoulder_level_angle': body_result.shoulder_level_angle,
                'hip_level_angle': body_result.hip_level_angle,
                'face_level_angle': body_result.face_level_angle,
                'scoliosis_shoulder_ratio': body_result.scoliosis_shoulder_ratio,
                'scoliosis_hip_ratio': body_result.scoliosis_hip_ratio,
                'leg_length_ratio': body_result.leg_length_ratio,
                'left_leg_alignment_angle': body_result.left_leg_alignment_angle,
                'right_leg_alignment_angle': body_result.right_leg_alignment_angle,
            },
            'keypoints': []
        }

        # Side data 구성
        side_data = {
            'results': {
                'forward_head_angle': body_result.forward_head_angle,
                'left_back_knee_angle': body_result.left_back_knee_angle,
                'right_back_knee_angle': body_result.right_back_knee_angle,
            },
            'keypoints': []
        }

        # Keypoints 데이터 처리
        for keypoint in body_result.keypoints.all():  # Keypoint 객체 순회(총 2개)
            keypoint_data = [
                {
                    'x': x,
                    'y': y,
                    'z': z,
                    'visibility': v,
                    'presence': p
                }
                for x, y, z, v, p in zip(
                    keypoint.x,
                    keypoint.y,
                    keypoint.z,
                    keypoint.visibility,
                    keypoint.presence
                )
            ]

            if keypoint.pose_type == 'front':  # pose별 keypoint 데이터 분리
                front_data['keypoints'] = keypoint_data
            else:
                side_data['keypoints'] = keypoint_data

        # 최종 응답 데이터 구성
        response_data = {
            'front_data': front_data,
            'side_data': side_data,
            'image_front': image_front_url,
            'image_side': image_side_url
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'data': {'message': str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        return Response({'message': 'not_receive'}, status=status.HTTP_200_OK)

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
        family_user_id = request.data.get('family_user_id', None)
        req_created_dt = request.data.get('created_dt', None) # 클라이언트 생성(요청) 시간  | 앱 - 서버 간 동기화 작업을 위해서는 동일한 Timestamp를 사용할 필요성이 있음. - Jerry
        height = request.data.get('height', None)
        weight = request.data.get('weight', None)

        # 사용자 정보 확인
        try:
            user_info = UserInfo.objects.get(id=user_id)
        except UserInfo.DoesNotExist:  # 유저가 존재하지 않는 경우
            return Response({'data': {'message': 'user_not_found'}}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            if family_user_id is not None:
                FamilyUserInfo.objects.get(id=family_user_id, user_id=user_id)
        except FamilyUserInfo.DoesNotExist:
            return Response({'data': {'message': 'family_user_not_found'}}, status=status.HTTP_401_UNAUTHORIZED)   
        

        if req_created_dt is not None:
            try:
                # req_created_dt를 datetime 객체로 변환
                created_dt = dt.strptime(req_created_dt, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError as e:
                return Response({'data': {'message': f'Invalid date format: {str(e)}'}}, status=status.HTTP_400_BAD_REQUEST)
        else:
            created_dt = dt.now()

        # results 데이터 병합
        body_data = {
            **front_data.get('results', {}),
            **side_data.get('results', {}),
            'user': user_id,
            'mobile_yn': 'y',
            'family_user': family_user_id if family_user_id is not None else None,
            'created_dt': created_dt,
            'height': height if height else None,
            'weight': weight if weight else None
        }
        
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
            created_dt = body_data['created_dt'].strftime('%Y%m%dT%H%M%S%f')
            # String -> datetime 변환 후 날짜포맷 설정

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



# / *********************************************************************** /
# / ********************  (체형분석앱) - 가족 관련 로직   *********************** /
# / *********************************************************************** /
@swagger_auto_schema(**create_family_user_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_family_user(request) -> Response:
    user_id = request.user.id
    if not user_id:                   # 사용자 ID가 없는 경우
        return Response({'data': {'message': 'token_required'}}, status=status.HTTP_400_BAD_REQUEST)

    if request.user.user_type != 'G': # 일반 유저만 가족 유저 생성 가능
        return Response({'data': {'message': 'user_not_permission'}}, status=status.HTTP_400_BAD_REQUEST)

    if not request.data.get('family_member_name') or not request.data.get('gender') or not request.data.get('relationship'):
        return Response({'data': {'message': 'required_fields_missing'}}, status=status.HTTP_400_BAD_REQUEST)

    req_user_families = FamilyUserInfo.objects.filter(user_id=user_id)

    if len(req_user_families) >= 3: # 가족 유저는 최대 3명까지 생성 가능
        return Response({'data': {'message': 'family_user_limit_exceeded'}}, status=status.HTTP_400_BAD_REQUEST)


    try:
        # 가족 사용자 데이터 준비
        family_data = {
            'user': user_id,
            'family_member_name': request.data.get('family_member_name'),
            'gender': request.data.get('gender'),
            'relationship': request.data.get('relationship'),
            'profile_image': request.data.get('profile_image') is not None  # 이미지가 있는지 확인 (True/False)
        }


        

        #시리얼라이저 생성 및 유효성 검사
        # FamilyUserInfoSerializer가 필요합니다 - 아래는 예시 코드입니다
        serializer = FamilyUserInfoSerializer(data=family_data)
        if not serializer.is_valid():
            return Response({'data': {'message': serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)


        # 트랜잭션으로 DB 작업 처리
        with transaction.atomic():
            # 가족 사용자 저장
            family_user = serializer.save()

            # 프로필 이미지 처리
            profile_image_url = None  # 기본값 설정
            if request.data.get('profile_image'):
                try:
                    profile_image = verify_image(request.data.get('profile_image'))
                    
                    created_dt = dt.strptime(serializer.data['created_dt'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y%m%dT%H%M%S%f')
                    
                    # S3에 이미지 업로드
                    upload_image_to_s3(profile_image, ['profile', created_dt])

                    profile_image_url = generate_presigned_url(file_keys=['profile/profile', created_dt])
                except ValueError as ve:
                    return Response({'data': {'message': f"Invalid image format: {str(ve)}"}}, 
                                   status=status.HTTP_400_BAD_REQUEST)

        
        # 성공 응답 반환
        return Response(
            {'data': {'message': 'family_user_created', 'family_data' :{'id': family_user.id, 'profile_image_url': profile_image_url}}},
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return Response({'data': {'message': str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@swagger_auto_schema(**select_family_user_)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_family_user(request):
    user_id = request.user.id
    if not user_id:
        return Response({'data': {'message': 'token_required'}}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.user_type != 'G':  # 일반 유저만 가족 유저 조회 가능
        return Response({'data': {'message': 'user_not_permission'}}, status=status.HTTP_403_FORBIDDEN)

    family_user_id = request.GET.get('family_user_id', None)

    query_filters = {'user_id': user_id}
    if family_user_id is not None:
        query_filters['id'] = family_user_id

    try:
        family_users = FamilyUserInfo.objects.filter(**query_filters).order_by('-created_dt')
        family_user_responses = FamilyUserResponseSerializer(family_users, many=True).data

        return Response(
            {'data': {'message': 'success', 'family_users': family_user_responses, 'items': len(family_user_responses)}},
            status=status.HTTP_200_OK
        )

    except UserInfo.DoesNotExist:
        return Response({'data': {'message': 'user_not_found'}}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({'data': {'message': str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@swagger_auto_schema(**delete_family_user_)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_family_user(request):
    user_id = request.user.id
    if not user_id:
        return Response({'data': {'message': 'token_required'}}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.user_type != 'G':  # 일반 유저만 가족 유저 삭제 가능
        return Response({'data': {'message': 'user_not_permission'}}, status=status.HTTP_403_FORBIDDEN)
    
    family_user_id = request.query_params.get('family_user_id', None)

    if family_user_id is None:
        return Response({'data': {'message': 'family_user_id_required'}}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        family_user = FamilyUserInfo.objects.get(id=family_user_id, user_id=user_id)
        family_user.delete()

        return Response({'data': {'message': 'family_user_deleted'}}, status=status.HTTP_200_OK)
    
    except FamilyUserInfo.DoesNotExist:
        return Response({'data': {'message': 'family_user_not_found'}}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({'data': {'message': str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_family_user(request):
    user_id = request.user.id
    if not user_id:
        return Response({'data': {'message': 'token_required'}}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user.user_type != 'G':  # 일반 유저만 가족 유저 수정 가능
        return Response({'data': {'message': 'user_not_permission'}}, status=status.HTTP_400_BAD_REQUEST)

    family_user_id = request.data.get('family_user_id', None)
    if family_user_id is None:
        return Response({'data': {'message': 'family_user_id_required'}}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        family_user = FamilyUserInfo.objects.get(id=family_user_id, user_id=user_id)
        
        family_member_name = request.data.get('family_member_name')
        gender = request.data.get('gender')
        relationship = request.data.get('relationship')
        profile_image = request.data.get('profile_image')

        
        # 제공된 값만 업데이트
        if family_member_name:
            family_user.family_member_name = family_member_name
        if gender:
            family_user.gender = gender
        if relationship:
            family_user.relationship = relationship
        
        # 프로필 이미지가 제공된 경우에만 처리
        if profile_image:
            try:
                verified_image = verify_image(profile_image)
                created_dt = family_user.created_dt.strftime('%Y%m%dT%H%M%S%f')
                
                # S3에 이미지 업로드
                upload_image_to_s3(verified_image, ['profile', created_dt])
                family_user.profile_image = True
                
            except ValueError as ve:
                return Response(
                    {'data': {'message': f"Invalid image format: {str(ve)}"}}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        family_user.save()
        
        # 프로필 이미지 URL 생성 (이미지가 있는 경우에만)
        # profile_image_url = None
        # if family_user.profile_image:
        #    created_dt = family_user.created_dt.strftime('%Y%m%dT%H%M%S%f')
        #    profile_image_url = generate_presigned_url(file_keys=['profile', created_dt])
        # 업로드 후 S3에 전파되기까지의 시간이 필요함 현재 업로드 후 바로 URL 생성 시 S3에서 404 에러 발생 
        
        return Response({
            'data': {
                'message': 'family_user_updated',
                'family_data': {
                    'id': family_user.id
                }
            }
        }, status=status.HTTP_200_OK)
        
    except FamilyUserInfo.DoesNotExist:
        return Response(
            {'data': {'message': 'family_user_not_found'}}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        return Response(
            {'data': {'message': str(e)}}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )