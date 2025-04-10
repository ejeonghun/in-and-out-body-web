from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from analysis.serializers import GaitResponseSerializer, BodyResultSerializer


############################################################################################################
############################################################################################################
##################################               키오스크                 ####################################
############################################################################################################
############################################################################################################


kiosk_create_gait_result_ = dict(
    method='post',
    operation_description="Create a new gait analysis result record",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='Session key for the user'),
            'gait_data': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'velocity': openapi.Schema(type=openapi.TYPE_NUMBER, description='Velocity'),
                    'cadence': openapi.Schema(type=openapi.TYPE_NUMBER, description='Cadence'),
                    'cycle_time_l': openapi.Schema(type=openapi.TYPE_NUMBER, description='Cycle time left'),
                    'cycle_time_r': openapi.Schema(type=openapi.TYPE_NUMBER, description='Cycle time right'),
                    'stride_len_l': openapi.Schema(type=openapi.TYPE_NUMBER, description='Stride length left'),
                    'stride_len_r': openapi.Schema(type=openapi.TYPE_NUMBER, description='Stride length right'),
                    'supp_base_l': openapi.Schema(type=openapi.TYPE_NUMBER, description='Support base left'),
                    'supp_base_r': openapi.Schema(type=openapi.TYPE_NUMBER, description='Support base right'),
                    'swing_perc_l': openapi.Schema(type=openapi.TYPE_NUMBER, description='Swing percentage left'),
                    'swing_perc_r': openapi.Schema(type=openapi.TYPE_NUMBER, description='Swing percentage right'),
                    'stance_perc_l': openapi.Schema(type=openapi.TYPE_NUMBER, description='Stance percentage left'),
                    'stance_perc_r': openapi.Schema(type=openapi.TYPE_NUMBER, description='Stance percentage right'),
                    'd_supp_perc_l': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                    description='Double support percentage left'),
                    'd_supp_perc_r': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                    description='Double support percentage right'),
                    'toeinout_l': openapi.Schema(type=openapi.TYPE_NUMBER, description='Toe-in/out angle left'),
                    'toeinout_r': openapi.Schema(type=openapi.TYPE_NUMBER, description='Toe-in/out angle right'),
                    'stridelen_cv_l': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                     description='Stride length coefficient of variation left'),
                    'stridelen_cv_r': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                     description='Stride length coefficient of variation right'),
                    'stridetm_cv_l': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                    description='Stride time coefficient of variation left'),
                    'stridetm_cv_r': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                    description='Stride time coefficient of variation right'),
                    'score': openapi.Schema(type=openapi.TYPE_NUMBER, description='Gait score'),
                }
            ),
        },
        required=['session_key', 'gait_data'],
    ),
    responses={
        200: 'OK; created_gait_result successfully',
        400: 'Bad Request; (session_key | gait_data) is not provided in the request body',
        401: 'Unauthorized; incorrect user or password',
        403: 'session_expired',
        404: 'Not Found; session_key is not found',
        500: 'Internal Server Error'
    },
    tags=['analysis results']
)





kiosk_get_gait_result_ = dict(
    method='get',
    operation_description="Retrieve latest gait analysis results by session key",
    manual_parameters=[
        openapi.Parameter('session_key', openapi.IN_QUERY, description="Session key for the current user",
                          type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('count', openapi.IN_QUERY, description="The number of items to retrieve from latest results",
                          type=openapi.TYPE_INTEGER, required=False),
        openapi.Parameter('start_date', openapi.IN_QUERY,
                          description="The start date for filtering results (format: YYYY-MM-DD)",
                          type=openapi.TYPE_STRING, required=False),
        openapi.Parameter('end_date', openapi.IN_QUERY,
                          description="The end date for filtering results (format: YYYY-MM-DD)",
                          type=openapi.TYPE_STRING, required=False),
    ],
    responses={
        200: GaitResponseSerializer,
        400: 'Bad Request; session_key is not provided in the request body',
        401: 'Unauthorized; incorrect user or password',
        403: 'session_expired',
        404: 'Not Found; session_key or gait result is not found',
    },
    tags=['analysis results']
)




kiosk_get_info_ = dict(
    method='get',
    operation_description="Get information of gait & body analysis",
    manual_parameters=[
        openapi.Parameter('name', openapi.IN_QUERY, description="Name of analysis (i.e., gait or body)",
                          type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: 'OK',
        400: 'Bad Request; invalid name',
    },
    tags=['analysis results']
)





kiosk_create_body_result_ = dict(
    method='post',
    operation_description="Create a new body result record",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='Session key for the user'),
            'body_data': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'face_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER, description='Face level angle'),
                    'shoulder_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                           description='Shoulder level angle'),
                    'hip_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hip level angle'),
                    'leg_length_ratio': openapi.Schema(type=openapi.TYPE_NUMBER, description='Leg length ratio'),
                    'left_leg_alignment_angle': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                               description='Left leg alignment angle'),
                    'right_leg_alignment_angle': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                                description='Right leg alignment angle'),
                    'left_back_knee_angle': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                           description='Left back knee angle'),
                    'right_back_knee_angle': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                            description='Right back knee angle'),
                    'forward_head_angle': openapi.Schema(type=openapi.TYPE_NUMBER, description='Forward head angle'),
                    'scoliosis_shoulder_ratio': openapi.Schema(type=openapi.TYPE_NUMBER,
                                                               description='Scoliosis shoulder ratio'),
                    'scoliosis_hip_ratio': openapi.Schema(type=openapi.TYPE_NUMBER, description='Scoliosis hip ratio'),
                },
            ),
            'image_front': openapi.Schema(type=openapi.TYPE_STRING,
                                          description='Base64 encoded bytes of the front image'),
            'image_side': openapi.Schema(type=openapi.TYPE_STRING,
                                         description='Base64 encoded bytes of the side image'),
        },
        required=['session_key', 'body_data', 'image_front', 'image_side'],  # Required fields
    ),
    responses={
        200: openapi.Response(
            description='OK; created_body_result successfully',
            examples={
                "application/json": {
                    "message": "created_body_result",
                    "status": 200
                }
            }
        ),
        400: openapi.Response(
            description='Bad Request; session_key or body_data or image is missing, or image format is invalid',
            examples={
                "application/json": {
                    "message": "session_key_required",
                    "status": 400
                }
            }
        ),
        401: openapi.Response(
            description='Unauthorized; user not found',
            examples={
                "application/json": {
                    "message": "user_not_found",
                    "status": 401
                }
            }
        ),
        403: openapi.Response(description='session_expired'),
        404: openapi.Response(
            description='Not Found; session_key is not found',
            examples={
                "application/json": {
                    "message": "session_key_not_found",
                    "status": 404
                }
            }
        ),
        500: openapi.Response(
            description='Internal Server Error; unexpected error occurred',
            examples={
                "application/json": {
                    "message": "An unexpected error occurred.",
                    "status": 500
                }
            }
        ),
    },
    tags=['analysis results']
)





kiosk_get_body_result_ = dict(
    method='get',
    operation_description="Retrieve latest body analysis results by session key",
    manual_parameters=[
        openapi.Parameter('session_key', openapi.IN_QUERY, description="Session key for the current user",
                          type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('count', openapi.IN_QUERY, description="The number of items to retrieve from latest results",
                          type=openapi.TYPE_INTEGER, required=False),
        openapi.Parameter('start_date', openapi.IN_QUERY,
                          description="The start date for filtering results (format: YYYY-MM-DD)",
                          type=openapi.TYPE_STRING, required=False),
        openapi.Parameter('end_date', openapi.IN_QUERY,
                          description="The end date for filtering results (format: YYYY-MM-DD)",
                          type=openapi.TYPE_STRING, required=False),
    ],
    responses={
        200: BodyResultSerializer(many=True),
        400: 'Bad Request; session_key is not provided in the request body',
        401: 'Unauthorized; incorrect user or password',
        403: 'session_expired',
        404: 'Not Found; session_key is not found',
        500: 'Internal Server Error'
    },
    tags=['analysis results']
)





kiosk_login_kiosk_ = dict(
    method='post',
    operation_summary="키오스크 세션 생성 및 키오스크 버전 체크",
    operation_description="Login to the kiosk using kiosk_id and kiosk version check logic, returning session key",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'kiosk_id': openapi.Schema(type=openapi.TYPE_STRING, description='Kiosk identifier'),
        },
        required=['kiosk_id'],
    ),
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'data':
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='Generated session key'),
                    }),
            })),
        400: 'Bad Request; kiosk_id is not provided in the request body',
        401: 'kiosk_update_required or kiosk_inactive',
    },
    tags=['kiosk']
)






kiosk_login_kiosk_id = dict(
    method='post',
    operation_description="Login to the kiosk using session key, phone number, and password",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='Session key'),
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
        },
        required=['session_key', 'phone_number', 'password'],
    ),
    responses={
        200: 'Login Success',
        400: 'Bad Request; (session_key | phone_number | password) is not provided in the request body',
        401: 'Unauthorized; incorrect user or password',
        403: 'session_expired',
        404: 'Not Found; session_key is not found',
    },
    tags=['kiosk']
)




kiosk_get_userinfo_session_ = dict(
    method='get',
    operation_description="Retrieve user information by session key",
    manual_parameters=[
        openapi.Parameter('session_key', openapi.IN_QUERY, description="Session key", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_info': openapi.Schema(type=openapi.TYPE_OBJECT, description='User information'),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status Code'),
                    }
                )})),
        400: 'Bad Request; session_key is not provided in the request body',
        401: 'Unauthorized; incorrect user or password',
        403: 'session_expried',
        404: 'Not Found; session_key is not found',
    },
    tags=['kiosk']
)



kiosk_end_session_ = dict(
    method='post',
    operation_description="End the session using session key",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='Session key'),
        },
        required=['session_key'],
    ),
    responses={
        200: 'Success',
        400: 'Bad Request; (session_key | phone_number | password) is not provided in the request body',
        404: 'Not Found; session_key is not found',
    },
    tags=['kiosk']
)





kiosk_check_session_ = dict(
    method='get',
    operation_description="Check if the session key is valid",
    manual_parameters=[
        openapi.Parameter('session_key', openapi.IN_QUERY, description="Session key", type=openapi.TYPE_STRING),
    ],
    responses={
        200: 'Success',
        400: 'Bad Request; session_key is not provided in the request body',
        404: 'Not Found; session_key is not found',
        403: 'Forbidden; session is expired',
    },
    tags=['kiosk']
)


kiosk_use_count_ = {
    'method': 'post',
    'operation_description': '키오스크 사용 횟수를 기록합니다.',
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['session_key', 'type'],
        properties={
            'session_key': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='세션 키'
            ),
            'type': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='카운트 유형 (1: 회원 보행, 2: 회원 체형, 3: 비회원 보행, 4: 비회원 체형)'
            )
        }
    ),
    'responses': {
        200: 'Success',
        400: 'Bad Request; session_key is not provided in the request body',
        404: 'Not Found; session_key is not found'
    },
    'tags': ['kiosk']
}



kiosk_signup_ = {
    'method': 'post',
    'operation_summary': '키오스크 회원가입',
    'operation_description': '키오스크에서 회원가입을 진행합니다.',
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['session_key','phone_number', 'password'],
        properties={
            'session_key': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='세션키'
            ),
            'phone_number': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='사용자 전화번호 (010으로 시작하는 11자리)',
                pattern='^010[0-9]{8}$'
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='사용자 비밀번호'
            ),
            'dob': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description='사용자 생년월일 (YYYY)',
            ),
            'gender': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='사용자 성별 (0 : M, 1 : F)',
                enum=['0', '1']
            ),
            'auth_code': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='SMS 인증 코드'
            ),
        }
    ),
    'responses': {
        200: openapi.Response(
            description='회원가입 성공',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='성공 메시지'),
                    'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='상태 코드')
                }
            )
        ),
        400: openapi.Response(
            description='잘못된 요청',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='오류 메시지 (phone_number_already_exists, phone_number_and_password_required, 또는 invalid_phone_number_format)'
                    ),
                    'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='상태 코드', example="0: 성공, 1: 세션키 없음, 2:전화번호, 성별, 생년월일 형식 확인, 3:이미 가입됨, 4:필수 파라미터 누락, 5: 세션키에 키오스크를 정보가 없음")
                }
            )
        )
    },
    'tags': ['kiosk']
}


kiosk_send_sms_ = dict(
    method='POST',
    operation_summary= '회원가입 시 인증번호 발송 API',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호 (010으로 시작하는 11자리)'),
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='세션 키')
        },
        required=['phone_number', 'session_key']
    ),
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                'status': openapi.Schema(type=openapi.TYPE_INTEGER, example="0: 성공 , 1: 전화번호 형식 검사 실패, 2: 이미 가입된 전화번호, 3:전화번호나 세션키가 요청 파라미터에 없음, 500: 발송실패 , ")
            }
        )),
    },
    tags= ['kiosk']
)


kiosk_check_sms_ = dict(
    method='POST',
    operation_summary= '회원가입 시 인증번호 검증 API',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호 (010으로 시작하는 11자리)'),
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='세션 키'),
            'auth_code': openapi.Schema(type=openapi.TYPE_STRING, description='인증 코드')
        },
        required=['phone_number', 'session_key', 'auth_code']
    ),
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                'status': openapi.Schema(type=openapi.TYPE_INTEGER, example=200)
            }
        )),
        400: openapi.Response('Bad Request', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )),
    },
    tags= ['kiosk']
)

############################################################################################################
############################################################################################################
##################################               모바일 공용               ####################################
############################################################################################################
############################################################################################################





############################################################################################################
# 사용위치 : views_mobile.py  - mobile-login
# 적용범위 : Flutter
############################################################################################################
login_mobile_ = {
    'method': 'post',
    'operation_summary': "모바일 로그인(토큰 발급) - mobile_uid",
    'operation_description': "mobile_uid를 사용하여 모바일 기기 인증(로그인 만) - Dave님 쪽 Logic ",
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_uid': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='SMS 인증번호'
            ),
        },
        required=['mobile_uid'],
    ),
    'responses': {
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_info': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='사용자 정보'),
                        'jwt_tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access_token': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Access token'),
                                'refresh_token': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Refresh token'),
                            }
                        ),
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='success'
                        ),
                        'status': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=200
                        )
                    }
                )
            }
        )),
        400: openapi.Response(
            description="Bad Request; 예시: mobile_uid_required",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example='mobile_uid_required'
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=400
                            )
                        }
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Not Found; 예시: Not received",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example='Not received'
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=404
                            )
                        }
                    )
                }
            )
        ),
        403: openapi.Response(
            description="Forbidden; 예시: unregistered user",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example='unregistered user'
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=403
                            )
                        }
                    )
                }
            )
        ),
    }
}


############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter
############################################################################################################
login_mobile_id_pw_ = {
    'method':'post',
    'operation_summary':"모바일 로그인 ID/PW 로그인(토큰 발급) - ID, PW",
    'operation_description':"Authenticate mobile device using ID and password to issue JWT tokens.",
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='User ID (phone number)'
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='User password'
            ),
        },
        required=['id', 'password'],
    ),
    'responses':{
        200: openapi.Response(
            description='Success or User Not Found',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description='Response data for successful authentication.',
                        properties={
                            'user_info': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='User information object, structure depends on implementation.'
                            ),
                            'jwt_tokens': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='JWT tokens issued upon successful authentication.',
                                properties={
                                    'access_token': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Access token for authenticated requests.'
                                    ),
                                    'refresh_token': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Refresh token for obtaining a new access token.'
                                    ),
                                }
                            ),
                            'is_default_password': openapi.Schema(
                                type=openapi.TYPE_BOOLEAN,
                                description='Indicates whether the user is using the default password.'
                            ),
                        }
                    ),
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="'user_not_found' if authentication fails."
                    )
                }
            )
        ),
        400: openapi.Response(
            description='Bad Request',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="'id_password_required' if ID or password is missing."
                    )
                }
            )
        ),
    }
}



############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter
############################################################################################################
login_mobile_uuid_ = {
    'method':'post',
    'operation_summary':"UUID 로그인",
    'operation_description':"Authenticate mobile device using uuid",
    'request_body':openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'uuid': openapi.Schema(type=openapi.TYPE_STRING,
                                   description='Unique identifier for the mobile device'),
        },
        required=['uuid'],
    ),
    'responses':{
        200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_OBJECT,
                                                        properties={
                                                            'data':
                                                                openapi.Schema(
                                                                    type=openapi.TYPE_OBJECT,
                                                                    properties={
                                                                        'user_info': openapi.Schema(
                                                                            type=openapi.TYPE_OBJECT,
                                                                            description='User information'),
                                                                        'jwt_tokens': openapi.Schema(
                                                                            type=openapi.TYPE_OBJECT,
                                                                            properties={
                                                                                'access_token': openapi.Schema(
                                                                                    type=openapi.TYPE_STRING,
                                                                                    description='Access token'),
                                                                                'refresh_token': openapi.Schema(
                                                                                    type=openapi.TYPE_STRING,
                                                                                    description='Refresh token'),
                                                                            }
                                                                        ),
                                                                    }
                                                                ),
                                                        })),
        400: 'Bad Request; uuid is not provided in the request body',
    }
}


############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
delete_user_ = {
    'method':'post',
    'operation_summary':"회원 탈퇴",
    'operation_description':"Delete user information",
    'responses':{
        200: openapi.Response('Success',
                              openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                  'data':
                                      openapi.Schema(
                                          type=openapi.TYPE_OBJECT,
                                          properties={
                                              'message': openapi.Schema(type=openapi.TYPE_STRING,
                                                                        description='Success message'),
                                          }
                                      )}),
                              ),
        404: 'Not Found; user_not_found',
    },
    'tags':['mobile']
}




############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter
############################################################################################################
login_mobile_qr_ = {
    'method':'post',
    'operation_summary':"모바일 -> 키오스크 로그인",
    'operation_description':"Login using session-key-generated QR code in mobile app",
    'request_body':openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'session_key': openapi.Schema(type=openapi.TYPE_STRING, description='Session key from QR code'),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID (i.e., index)')
        },
        required=['session_key'],
    ),
    'responses':{
        200: openapi.Response('Login Success',
                              openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                  'data':
                                      openapi.Schema(
                                          type=openapi.TYPE_OBJECT,
                                          properties={
                                              'session_key': openapi.Schema(type=openapi.TYPE_STRING,
                                                                            description='Session key'),
                                              'message': openapi.Schema(type=openapi.TYPE_STRING,
                                                                        description='Success message'),
                                          }
                                      )})),
        400: 'Bad Request; session_key is not provided in the request body',
        404: 'Not Found; session_key is not found',
    }
}


############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter
############################################################################################################
get_user_ = {
    'method':'post',
    'operation_summary':"사용자 정보 조회",
    'operation_description':"Get user information using access token",
    'responses':{
        200: openapi.Response('Success',
                              openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                  'data':
                                      openapi.Schema(
                                          type=openapi.TYPE_OBJECT,
                                          properties={
                                              'user_info': openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                          description='User information'),
                                              'message': openapi.Schema(type=openapi.TYPE_STRING,
                                                                        description='Success message'),
                                          }
                                      )}),
                              ),
        404: 'Not Found; user_not_found',
    },
    'tags':['mobile']
}


############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
get_code_ = {
    'method':'get',
    'operation_summary':"체형 계산 코드 정보 조회",
    'operation_description':"""select code info list
                            - group_id_list: list of group_id
                            ex) 01, 02
                            """,
    'manual_parameters':[
        openapi.Parameter('group_id_list', openapi.IN_QUERY, description="group_id list", type=openapi.TYPE_INTEGER),
    ],
    'responses':{
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "data": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "group_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "code_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "code_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "min_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "max_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "normal_min_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "normal_max_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "caution_min_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "caution_max_value": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "outline": openapi.Schema(type=openapi.TYPE_STRING),
                                "risk": openapi.Schema(type=openapi.TYPE_STRING),
                                "improve": openapi.Schema(type=openapi.TYPE_STRING),
                                "recommended": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                              items=openapi.Schema(type=openapi.TYPE_STRING), ),
                                "title": openapi.Schema(type=openapi.TYPE_STRING),
                                "title_outline": openapi.Schema(type=openapi.TYPE_STRING),
                                "title_risk": openapi.Schema(type=openapi.TYPE_STRING),
                                "title_improve": openapi.Schema(type=openapi.TYPE_STRING),
                                "title_recommended": openapi.Schema(type=openapi.TYPE_STRING),
                                "unit_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "seq_no": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "display_ticks": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                items=openapi.Schema(type=openapi.TYPE_STRING)),
                                "direction": openapi.Schema(type=openapi.TYPE_STRING),
                                "created_dt": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                            }
                        )
                    ),
                },
            )
        ),
        400: 'Bad Request; group_id_list_required',
        404: 'Not Found; code_not_found',
    },
    'tags':['mobile']
}



############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
get_gait_result_ = dict(
    method='get',
    operation_summary="게이트 결과 리스트 조회",
    operation_description="""select gait result list
    - page: page number. default 1
    - page_size: page size. default 10
    """,
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="page number.", type=openapi.TYPE_INTEGER, default=1),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="page size(items)", type=openapi.TYPE_INTEGER,
                          default=10),
    ],
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "data": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT, description="Result object")
                    ),
                    "total_pages": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of pages."),
                    "current_page": openapi.Schema(type=openapi.TYPE_INTEGER, description="Current page number."),
                    "total_items": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of items."),
                    "items": openapi.Schema(type=openapi.TYPE_INTEGER,
                                            description="Number of items in the current page."),
                },
            )
        ),
        400: 'Bad Request; page number out of range',
    },
    tags=['mobile']
)




############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
get_body_result_ = dict(
    method='get',
    operation_summary="체형 결과 리스트 조회",
    operation_description="""select body result list
    - page: page number. default 1
    - page_size: page size. default 10
    - mobile: y: mobile, n: kiosk. default 'n'
    """,
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="page number.", type=openapi.TYPE_INTEGER, default=1),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="page size(items)", type=openapi.TYPE_INTEGER,
                          default=10),
        openapi.Parameter('mobile', openapi.IN_QUERY, description="'y': mobile, 'n': kiosk, default: 'n'",
                          type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "data": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "student_grade": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "student_class": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "student_number": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "face_level_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "shoulder_level_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "hip_level_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "leg_length_ratio": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "left_leg_alignment_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "right_leg_alignment_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "left_back_knee_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "right_back_knee_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "forward_head_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "scoliosis_shoulder_ratio": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "scoliosis_hip_ratio": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "image_front_url": openapi.Schema(type=openapi.TYPE_STRING),
                                "image_side_url": openapi.Schema(type=openapi.TYPE_STRING),
                                "mobile_yn": openapi.Schema(type=openapi.TYPE_STRING, description="y: mobile, n: kiosk",
                                                            default="n"),
                                "created_dt": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                "height": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "weight": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "user": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "school": openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    ),
                    "total_pages": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of pages."),
                    "current_page": openapi.Schema(type=openapi.TYPE_INTEGER, description="Current page number."),
                    "total_items": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of items."),
                    "items": openapi.Schema(type=openapi.TYPE_INTEGER,
                                            description="Number of items in the current page."),
                },
            )
        ),
        400: 'Bad Request; page number out of range',
    },
    tags=['mobile']
)





############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
delete_gait_result_ = dict(
    method='post',
    operation_summary="게이트 결과 삭제",
    operation_description="Delete gait result using gait_id",
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, description="gait id", type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: 'Success',
        400: 'Bad Request; gait_id is not provided in the request body',
    },
    tags=['mobile']
)




############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
delete_body_result_ = dict(
    method='post',
    operation_summary="체형 결과 삭제",
    operation_description="Delete body result using body_id",
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, description="body id", type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: 'Success',
        400: 'Bad Request; body_id is not provided in the request body',
    },
    tags=['mobile']
)


############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################

mobile_send_auth_sms_ = dict(
    method='POST',
    operation_summary='회원가입 시 인증번호 발송 API',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호 (010으로 시작하는 11자리)', example='01012345678'),
            'type': openapi.Schema(type=openapi.TYPE_STRING, example='password', description='password: 비밀번호 변경, None: 회원가입\n 회원가입 시에는 type을 생략 \n 회원가입인 경우에는 이미 가입된 회원이면 인증번호 발송 X'),
        },
        required=['phone_number']
    ),
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
            }
        )),
        400: openapi.Response('Bad Request', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='phone_number_required')
            }
        )),
        429: openapi.Response('Too Many Requests', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='too_many_requests')
            }
        )),
        500: openapi.Response('Internal Server Error', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='transmission failed')
            }
        )),
    },
    tags=['mobile']
)

mobile_check_auth_sms_ = dict(
    method='POST',
    operation_summary='인증번호 확인 API',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호', example='01012345678'),
            'auth_code': openapi.Schema(type=openapi.TYPE_STRING, description='인증번호', example='123456'),
        },
        required=['phone_number', 'auth_code']
    ),
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
            }
        )),
        400: openapi.Response('Bad Request', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='phone_number_or_auth_code_required'),
            }
        )),
        500: openapi.Response('Internal Server Error', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='transmission failed'),
            }
        )),
    },
    tags=['mobile']
)

mobile_signup_ = dict(
    method='POST',
    operation_summary='회원가입 API',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호 (010으로 시작하는 11자리)', example='01012345678'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호', example='your_password'),
            'dob': openapi.Schema(type=openapi.TYPE_STRING, description='생년 (YYYY 형식)', example='1990'),
            'gender': openapi.Schema(type=openapi.TYPE_STRING, description='성별 (0: 남성, 1: 여성)', example='0'),
        },
        required=['phone_number', 'password']
    ),
    responses={
        200: openapi.Response('Success', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
            }
        )),
        400: openapi.Response('Bad Request', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='invalid_phone_number_format'),
            }
        )),
    },
    tags=['mobile']
)



mobile_password_change_ = dict(
    method='POST',
    operation_summary='비밀번호 변경',
    tags=['mobile'],
    description='Allows a user to change their password using their phone number and an authentication code.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password for the user'),
            'auth_code': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication code sent to the user'),
        },
        required=['phone_number', 'new_password', 'auth_code'],
    ),
    responses={
        200: openapi.Response(
            description='Password changed successfully',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                },
            ),
        ),
        400: openapi.Response(
            description='Bad Request',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        404: openapi.Response(
            description='User not found',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        500: openapi.Response(
            description='Internal Server Error',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
    },
)


mobile_is_default_password_ = dict(
    method='post',
    operation_summary='초기 비밀번호 확인',
    tags=['mobile'],
    description='Checks if the user\'s password is the default password using their phone number.',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
        },
        required=['phone_number'],
    ),
    responses={
        200: openapi.Response(
            description='Password check successful',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'is_default_password': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                },
            ),
        ),
        400: openapi.Response(
            description='Bad Request',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        404: openapi.Response(
            description='User not found',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        500: openapi.Response(
            description='Internal Server Error',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
    },
)


############################################################################################################
############################################################################################################
##################################               체형분석앱                ####################################
############################################################################################################
############################################################################################################




############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
login_mobile_register_ = {
    'method': 'post',
    'operation_summary' : "모바일 로그인(토큰 발급) - mobile_uid",
    'operation_description': "mobile_uid를 사용하여 모바일 기기 인증 후 로그인 또는 회원가입 진행 - Jerry 님 Logic",
    'tags': ['체형분석앱'],
    'request_body' : openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mobile_uid': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='SMS 인증번호'
            ),
        },
        required=['mobile_uid'],
    ),
    'responses'  : {
        200: openapi.Response(
            'Success',
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'user_info': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='사용자 정보',
                                nullable=True
                            ),
                            'jwt_tokens': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'access_token': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Access token'
                                    ),
                                    'refresh_token': openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description='Refresh token'
                                    ),
                                }
                            ),
                            'message': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example='success'
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=200
                            )
                        }
                    )
                }
            )
        ),
        400: openapi.Response(
            description="Bad Request; mobile_uid가 제공되지 않음",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example='mobile_uid_required'
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=400
                            )
                        }
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Not Found; mobile_uid로 인증 정보 없음",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example='user_not_found'
                    ),
                    'status': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        example=200
                    )
                }
            )
        ),
        403: openapi.Response(
            description="Forbidden; 등록되지 않은 사용자",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example='unregistered user'
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=403
                            )
                        }
                    )
                }
            )
        ),
    }
}



############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
mobile_create_body_result_ = dict(
    method='post',
    operation_summary="모바일 체형 결과 생성(체형분석앱)",
    operation_description=""" 해당 API는 각 포즈별 체형 분석 값과 keypoints들과 이미지, 가족 ID(선택)을 받아서 저장시킴.
    Create a new body result record
    - mobile only
    - AI server result --> image base64 add --> API request --> DB save
    - header: Bearer token required
    - front_data: Front pose results and keypoints (33 keypoints required)
    - side_data: Side pose results and keypoints (33 keypoints required)
    - keypoints idx : https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md#pose-landmark-model-blazepose-ghum-3d
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'front_data': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'results': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'shoulder_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'hip_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'face_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'scoliosis_shoulder_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'scoliosis_hip_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'leg_length_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'left_leg_alignment_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'right_leg_alignment_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                        }
                    ),
                    'keypoints': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'x': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'y': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'z': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'visibility': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'presence': openapi.Schema(type=openapi.TYPE_NUMBER),
                            }
                        )
                    )
                }
            ),
            'side_data': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'results': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'forward_head_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'left_back_knee_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'right_back_knee_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                        }
                    ),
                    'keypoints': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'x': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'y': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'z': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'visibility': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'presence': openapi.Schema(type=openapi.TYPE_NUMBER),
                            }
                        )
                    )
                }
            ),
            'image_front': openapi.Schema(type=openapi.TYPE_STRING),
            'image_side': openapi.Schema(type=openapi.TYPE_STRING),
            'family_user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='가족 사용자 ID', nullable=True),
            "created_dt": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
            "height": openapi.Schema(type=openapi.TYPE_NUMBER),
            "weight": openapi.Schema(type=openapi.TYPE_NUMBER),
        },
        required=['front_data', 'side_data', 'image_front', 'image_side']
    ),
    responses={
        200: openapi.Response(
            description='Success',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING),
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                }
            )
        ),
        400: 'Bad Request',
        401: 'Unauthorized',
        500: 'Internal Server Error',
    },
    tags=['체형분석앱']
)


############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
mobile_body_sync_ = dict(
    method='get',
    operation_summary="체형 결과 ID값 리스트 조회",
    operation_description="""select body result id list
    - mobile created data only(mobile_yn = 'y')
    - JWT Token required    
    """,
    # 응답값 정의
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "message": openapi.Schema(type=openapi.TYPE_STRING, description="Success message"),
                            "body_results": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                           items=openapi.Schema(type=openapi.TYPE_INTEGER),
                                                           description="Body result ID list"),
                            "items": openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of items")
                        }
                    )
                }
            )
        ),
        401: 'Unauthorized; user_not_found',
    },
    tags=['체형분석앱']
)

############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
create_family_user_ = {
    'method': 'post',
    'operation_summary': "가족 사용자 생성",
    'operation_description': "사용자의 가족 사용자 정보를 생성합니다.",
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'family_member_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='가족 구성원의 이름',
            ),
            'gender': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='성별 (예: M, F)',
            ),
            'relationship': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='가족 관계 (예: 부모, 형제, 자매 등)',
            ),
            'profile_image': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='가족 구성원의 프로필 이미지 (Base64)',
            ),
        },
        required=['family_member_name', 'gender', 'relationship'],  # 필수 필드
    ),
    'responses': {
        201: openapi.Response(
            description='가족 사용자 생성 성공',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='family_user_created'),
                            'family_data': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='가족 사용자 ID'),
                                    'profile_image_url': openapi.Schema(type=openapi.TYPE_STRING, description='프로필 이미지 URL'),
                                }
                            )
                        }
                    )
                }
            )
        ),
        400: openapi.Response(
            description='잘못된 요청; 필수 필드가 누락되었거나 유효하지 않음',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='required_fields_missing'),
                        }
                    )
                }
            )
        ),
        403: openapi.Response(
            description='권한 없음; 일반 유저만 가족 사용자 생성 가능',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='user_not_permission'),
                        }
                    )
                }
            )
        ),
        404: openapi.Response(
            description='가족 ID 없음;',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='token_required'),
                        }
                    )
                }
            )
        ),
        500: openapi.Response(
            description='서버 오류; 예기치 않은 오류 발생',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='Internal Server Error'),
                        }
                    )
                }
            )
        ),
    },
    'tags': ['체형분석앱 - 가족 관리']
}

############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
select_family_user_ = {
    'method': 'get',
    'operation_summary': "가족 사용자 조회",
    'operation_description': "사용자의 가족 사용자 정보를 조회합니다.\n 가족 사용자 ID를 제공하면 해당 사용자의 정보를 조회합니다.",
    'manual_parameters':[
        openapi.Parameter('family_user_id', openapi.IN_QUERY, description="family_user_id", type=openapi.TYPE_INTEGER, required=False),
    ],
    'responses': {
        200: openapi.Response(
            description='가족 사용자 조회 성공',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                            'family_users': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='가족 사용자 ID'),
                                        'family_member_name': openapi.Schema(type=openapi.TYPE_STRING, description='가족 구성원의 이름'),
                                        'gender': openapi.Schema(type=openapi.TYPE_STRING, description='성별 (예: M, F)'),
                                        'relationship': openapi.Schema(type=openapi.TYPE_STRING, description='가족 관계 (예: 아빠, 엄마 등)'),
                                        'profile_image_url': openapi.Schema(type=openapi.TYPE_STRING, description='프로필 이미지 URL', nullable=True),
                                    }
                                )
                            ),
                            'items': openapi.Schema(type=openapi.TYPE_INTEGER, description='가족 사용자 수'),
                        }
                    )
                }
            )
        ),
        400: openapi.Response(
            description='잘못된 요청; 사용자 ID가 제공되지 않음',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='token_required'),
                        }
                    )
                }
            )
        ),
        401: openapi.Response(
            description='Unauthorized; 사용자 권한 없음',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='user_not_permission'),
                        }
                    )
                }
            )
        ),
        404: openapi.Response(
            description='Not Found; 사용자 정보 없음',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='user_not_found'),
                        }
                    )
                }
            )
        ),
        500: openapi.Response(
            description='서버 오류; 예기치 않은 오류 발생',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='Internal Server Error'),
                        }
                    )
                }
            )
        ),
    },
    'tags': ['체형분석앱 - 가족 관리']
}


############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
get_body_result_aos_ = dict(
    method='get',
    operation_summary="체형 결과 리스트 조회 - 체형분석앱 전용",
    operation_description="""select body result list
    - page: page number. default 1
    - page_size: page size. default 10
    - mobile: y: mobile, n: kiosk. default 'n'
    - family_user_id: family user ID
    """,
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="page number.", type=openapi.TYPE_INTEGER, default=1),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="page size(items)", type=openapi.TYPE_INTEGER,
                          default=10),
        openapi.Parameter('mobile', openapi.IN_QUERY, description="'y': mobile, 'n': kiosk, default: 'n'",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('family_user_id', openapi.IN_QUERY, description="family_user_id", type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "data": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "student_grade": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "student_class": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "student_number": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "face_level_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "shoulder_level_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "hip_level_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "leg_length_ratio": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "left_leg_alignment_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "right_leg_alignment_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "left_back_knee_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "right_back_knee_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "forward_head_angle": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "scoliosis_shoulder_ratio": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "scoliosis_hip_ratio": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "image_front_url": openapi.Schema(type=openapi.TYPE_STRING),
                                "image_side_url": openapi.Schema(type=openapi.TYPE_STRING),
                                "mobile_yn": openapi.Schema(type=openapi.TYPE_STRING, description="y: mobile, n: kiosk",
                                                            default="n"),
                                "created_dt": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                "height": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "weight": openapi.Schema(type=openapi.TYPE_NUMBER),
                                "user": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "school": openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    ),
                    "total_pages": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of pages."),
                    "current_page": openapi.Schema(type=openapi.TYPE_INTEGER, description="Current page number."),
                    "total_items": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of items."),
                    "items": openapi.Schema(type=openapi.TYPE_INTEGER,
                                            description="Number of items in the current page."),
                },
            )
        ),
        400: 'Bad Request; page number out of range',
    },
    tags=['체형분석앱']
)



############################################################################################################
# 사용위치 : views_mobile.py
# 적용범위 : Flutter, AOS
############################################################################################################
get_body_result_aos_id_ = dict(
    method='get',
    operation_summary="체형 결과 단건 조회",
    operation_description="""Get body result by ID
    - mobile only
    - header: Bearer token required
    - returns front and side data with keypoints
    """,
    responses={
        200: openapi.Response(
            description='Success',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'front_data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'results': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'shoulder_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'hip_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'face_level_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'scoliosis_shoulder_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'scoliosis_hip_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'leg_length_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'left_leg_alignment_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'right_leg_alignment_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                            ),
                            'keypoints': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'x': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'y': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'z': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'visibility': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'presence': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    }
                                )
                            )
                        }
                    ),
                    'side_data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'results': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'forward_head_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'left_back_knee_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'right_back_knee_angle': openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                            ),
                            'keypoints': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'x': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'y': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'z': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'visibility': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        'presence': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    }
                                )
                            )
                        }
                    ),
                    'image_front': openapi.Schema(type=openapi.TYPE_STRING),
                    'image_side': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Bad Request; body_id_required',
        401: 'Unauthorized',
        404: 'Not Found; body_result_not_found',
        500: 'Internal Server Error',
    },
    tags=['체형분석앱']
)

############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################
delete_family_user_ = {
    'method': 'post',
    'operation_summary': "가족 사용자 삭제",
    'operation_description': "가족 사용자 정보를 삭제합니다. 사용자는 일반 유저여야 하며, 삭제할 가족 사용자 ID를 제공해야 합니다.",
    'manual_parameters':[
        openapi.Parameter('family_user_id', openapi.IN_QUERY, description="family_user_id", type=openapi.TYPE_INTEGER),
    ],
    'responses': {
        200: openapi.Response(
            description='Success',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                }
            )
        ),
        400: 'Bad Request; family_user_id is not provided in the request body',
        401: 'Unauthorized',
        404: 'Not Found; family_user_not_found',
        500: 'Internal Server Error',
    },
    'tags': ['체형분석앱 - 가족 관리']
}

############################################################################################################
# 사용위치 : views_aos.py
# 적용범위 : AOS
############################################################################################################

# analysis/swagger.py
update_family_user_ = {
    'method': 'post',
    'operation_summary': "가족 사용자 수정",
    'operation_description': "사용자의 가족 사용자 정보를 수정합니다.",
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'family_user_id': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description='가족 사용자 ID',
            ),
            'family_member_name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='가족 구성원의 이름',
            ),
            'gender': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='성별 (예: M, F)',
            ),
            'relationship': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='가족 관계 (예: 부모, 형제, 자매 등)',
            ),
            'profile_image': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='가족 구성원의 프로필 이미지 (Base64)',
            ),
        },
        required=['family_user_id'],  # 필수 필드
    ),
    'responses': {
        200: openapi.Response(
            description='가족 사용자 수정 성공',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='family_user_updated'),
                            'family_data': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='가족 사용자 ID'),
                                }
                            )
                        }
                    )
                }
            )
        ),
        400: openapi.Response(
            description='잘못된 요청; 필수 필드가 누락되었거나 유효하지 않음',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='required_fields_missing'),
                        }
                    )
                }
            )
        ),
        403: openapi.Response(
            description='권한 없음; 일반 유저만 가족 사용자 수정 가능',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='user_not_permission'),
                        }
                    )
                }
            )
        ),
        404: openapi.Response(
            description='가족 사용자 ID 없음;',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='family_user_not_found'),
                        }
                    )
                }
            )
        ),
        500: openapi.Response(
            description='서버 오류; 예기치 않은 오류 발생',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'message': openapi.Schema(type=openapi.TYPE_STRING, example='Internal Server Error'),
                        }
                    )
                }
            )
        ),
    },
    'tags': ['체형분석앱 - 가족 관리']
}