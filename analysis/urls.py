from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

from analysis.custom.custom_token import CustomTokenObtainPairView, CustomTokenRefreshView

from analysis.custom.permissions import IsAllowedIP
from django.views.static import serve

from . import views, views_mobile, views_aos, views_kiosk
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.urls import path, re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Swagger API Document of In-and-Out-Body",
        default_version="v1",
        description="In-and-Out-Body API 문서 입니다.",
        terms_of_service="https://www.google.com/policies/terms/",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    # permission_classes=(IsAllowedIP,),  # 허용된 IP주소만 접근 가능
)

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True, next_page='main'), name='login'),
    path('signup/', views.signup, name='signup'),
    # path('register/', views.register, name='register'), 기존 사용자등록 페이지
    path('main/', views.main, name='main'),
    path('org_register/', views.org_register, name='org_register'),
    path('member_register/' , views.member_register, name='member_register'),
    path('report/', views.report, name='report'),
    path('report/protected/', views.report_detail_protected, name='report_detail_protected'),
    path('report/<int:id>/', views.report_detail, name='report_detail'),
    path('report_download/', views.report_download, name='report_download'),

    # 관리자 페이지 보행 관련 대시보드
    path('gait-report/', views.gait_report, name='gait_report'),
    path('api/gait-data/<int:user_id>/', views.get_user_gait_data, name='view_get_gait_data'),
    path('gait-print/<int:id>/', views.gait_print, name='gait_print'),
    path('gait-print-detail/<int:id>/', views.gait_print_kiosk, name='gait_print_detail'),

    path('body-print/<int:id>/', views.body_print, name='body_print'),
    path('body-print-detail/<int:id>/', views.body_print_kiosk, name='body_print_detail'),


    path('no-result/', views.no_result, name='no_result'),
    path('policy/', views.policy, name='policy'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('search_user/', views.search_user, name='search_user'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset-done/', views.password_reset_done, name='password_reset_done'),

    # for JWT token
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),

    # for custom authentication process
    path('api/login-kiosk/', views_kiosk.login_kiosk, name='login_kiosk'),
    path('api/login-kiosk-id/', views_kiosk.login_kiosk_id, name='login_kiosk_id'),
    path('api/get-userinfo-session/', views_kiosk.get_userinfo_session, name='get_userinfo_session'),
    path('api/end-session/', views_kiosk.end_session, name='end_session'),
    path('api/checksession/', views_kiosk.check_session, name='check_session'),
    path('api/signup-kiosk/', views_kiosk.kiosk_signup, name='kiosk_signup'),
    path('api/send-sms/', views_kiosk.kiosk_send_sms, name='send_sms'),
    path('api/check-sms/', views_kiosk.kiosk_check_sms, name='check_sms'),

    path('api/analysis/gait/create_result/', views_kiosk.create_gait_result, name='create_gait_result'),
    path('api/analysis/gait/get_result/', views_kiosk.get_gait_result, name='get_gait_result'),
    path('api/analysis/body/create_result/', views_kiosk.create_body_result, name='create_body_result'),
    path('api/analysis/body/get_result/', views_kiosk.get_body_result, name='get_body_result'),
    path('api/analysis/get_info/', views_kiosk.get_info, name='get_info'),
    path('api/analysis/count/', views_kiosk.kiosk_use_count, name='kiosk_use_count'),

    # 기관 정보 조회 api
    path('api/search-organization/', views.search_organization, name='search_organization'),
    path('api/register-organization/', views.register_organization, name='register_organization'),
    path('api/get-organization-info/', views.get_organization_info, name='get_organization_info'),

    # 서비스 모니터링 (prometheus)
    path('', include('django_prometheus.urls')),

    ## 모바일 전용 API (모바일 이외의 용도로 사용하지 말것)
    path('api/mobile/login-mobile/',            views_mobile.login_mobile,       name='mobile-auth-request_auth'),       # 휴대폰 인증 요청 ( 로그인 )
    path('api/mobile/login-mobile-qr/',         views_mobile.login_mobile_qr,    name='login_mobile_qr'),                # 휴대폰에서 QR 인증 요청,
    path('api/mobile/login-mobile-uuid/',       views_mobile.login_mobile_uuid,  name='mobile-auth-request_auth_uuid'),  # 휴대폰 인증 요청 (UUID를 사용하여 인증-테스트 목적)
    path('api/mobile/user/get_user/',           views_mobile.get_user,           name='mobile-user-get_user'),           # 사용자 정보 가져오기
    path('api/mobile/user/delete_user/',        views_mobile.delete_user,        name='mobile-user-delete_user'),        # 사용자
    path('api/mobile/code/get_code/',           views_mobile.get_code,           name='mobile-code-get_code'),           # 코드 정보 가져오기
    path('api/mobile/gait/get_gait_result/',    views_mobile.get_gait_result,    name='mobile-gait-get_gait_result'),    # 보행 결과 가져오기
    path('api/mobile/body/get_body_result/',    views_mobile.get_body_result,    name='mobile-body-get_body_result'),    # 체형 결과 가져오기
    path('api/mobile/gait/delete_gait_result/', views_mobile.delete_gait_result, name='mobile-body-delete_gait_result'), # 보행 결과 삭제
    path('api/mobile/body/delete_body_result/', views_mobile.delete_body_result, name='mobile-body-delete_body_result'), # 체형 결과 삭제
    # path('api/mobile/gait/sync_gait_result/',   views_mobile.mobile_gait_sync,   name='mobile-gait-mobile_gait_sync'),   # 보행 결과 동기화(gaitresults의 ID값만 반환함)
    path('api/mobile/login-mobile-id/',         views_mobile.login_mobile_id,    name='mobile-auth-request_auth_id'),     # ID 로그인 요청 (ID를 사용하여 로그인)
    path('api/mobile/auth/sms_send/',        views_mobile.mobile_send_auth_sms,              name='mobile-auth-send_sms'),           # SMS 인증 요청
    path('api/mobile/auth/sms_check/',       views_mobile.mobile_check_auth_sms,        name='mobile-auth-check_sms'),          # SMS 인증 확인
    path('api/mobile/auth/signup/',       views_mobile.mobile_signup,            name='mobile-auth-signup'),             # 회원가입



    ## AOS(체형분석앱) 전용 API
    path('api/v2/mobile/login-mobile-register/',  views_aos.login_mobile_register, name='mobile-aos-auth-request_auth_register'), # 휴대폰 인증 요청 (회원가입 / 로그인)
    path('api/v2/mobile/body/create_body_result/', views_aos.create_body_result, name='mobile-aos-body-create_body_result'), # 체형 결과 생성
    path('api/v2/mobile/body/sync_body_result/',   views_aos.mobile_body_sync,   name='mobile-aos-body-mobile_body_sync'),   # 체형 결과 동기화(bodyresults의 ID값만 반환함)
    path('api/v2/mobile/body/get_body_result/',     views_aos.get_body_result_aos, name="mobile-aos-body-get_body_result"), # 체형 결과 가져오기
    path('api/v2/mobile/body/get_body_result/<int:id>/',
                                                views_aos.get_body_result_aos_id, name='mobile-aos-body-get_body_result'),    # 체형 결과 가져오기

    # AOS(체형분석앱) 가족 사용자 API
    path('api/v2/mobile/family/create_family_user/', views_aos.create_family_user, name='mobile-aos-family-create_family_user'), # 가족 사용자 생성
    path('api/v2/mobile/family/get_family_user/',    views_aos.get_family_user,    name='mobile-aos-family-get_family_user'),    # 가족 사용자 정보 가져오기
    path('api/v2/mobile/family/delete_family_user/', views_aos.delete_family_user, name='mobile-aos-family-delete_family_user'), # 가족 사용자 삭제
    path('api/v2/mobile/family/update_family_user/', views_aos.update_family_user, name='mobile-aos-family-update_family_user'), # 가족 사용자 정보 수정


    # 디버그 환경이 아닐 때도 Swagger에 접근이 가능하나 단, 허용된 IP만 접근 가능
    re_path(r'^docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name="schema-json"),
    re_path(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # re_path(r'^static/(?P<path>.*)$', serve, {'document_root':settings.STATIC_ROOT}),   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)

# 디버그 시 실행 부분
# if settings.DEBUG:
#     urlpatterns += [
#         re_path(r'^docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name="schema-json"),
#         re_path(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#         re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),    ]