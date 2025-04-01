from django.test import SimpleTestCase, TestCase
from django.urls import reverse, resolve
from django.contrib.auth import views as auth_views
from .custom.custom_token import CustomTokenObtainPairView, CustomTokenRefreshView

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.hashers import make_password
from .models import AuthInfo, UserInfo, OrganizationInfo, KioskInfo, SessionInfo
from . import views, views_mobile, views_kiosk, views_aos

base_url = 'http://localhost:8000/'
mobile_uid = 'qwer'
phone_number = '01012345678'
password = '1234'
kiosk_id = 'jifjaeijfieajfi'


keypoints = [{
      "x": 0.45547524094581604,
      "y": 0.2614921033382416,
      "z": -0.3958122134208679,
      "visibility": 0.9988177418708801,
      "presence": 0.9990262985229492
    },
    {
      "x": 0.4740296006202698,
      "y": 0.24843698740005493,
      "z": -0.43741723895072937,
      "visibility": 0.9988846182823181,
      "presence": 0.999110996723175
    },
    {
      "x": 0.4791010320186615,
      "y": 0.24921321868896484,
      "z": -0.4381087124347687,
      "visibility": 0.9989609718322754,
      "presence": 0.99943608045578
    },
    {
      "x": 0.4842189848423004,
      "y": 0.2501499652862549,
      "z": -0.43800732493400574,
      "visibility": 0.9993858337402344,
      "presence": 0.9994809031486511
    },
    {
      "x": 0.4712662100791931,
      "y": 0.24767956137657166,
      "z": -0.3764253854751587,
      "visibility": 0.9987624883651733,
      "presence": 0.9980080723762512
    },
    {
      "x": 0.4743034541606903,
      "y": 0.24759280681610107,
      "z": -0.37713146209716797,
      "visibility": 0.9987375140190125,
      "presence": 0.9982882142066956
    },
    {
      "x": 0.4777162969112396,
      "y": 0.24738499522209167,
      "z": -0.3774909973144531,
      "visibility": 0.9990135431289673,
      "presence": 0.9978784322738647
    },
    {
      "x": 0.5207309126853943,
      "y": 0.26280277967453003,
      "z": -0.5187421441078186,
      "visibility": 0.9996851682662964,
      "presence": 0.9998231530189514
    },
    {
      "x": 0.5146452784538269,
      "y": 0.26117855310440063,
      "z": -0.24147628247737885,
      "visibility": 0.9978771209716797,
      "presence": 0.9984638690948486
    },
    {
      "x": 0.46311885118484497,
      "y": 0.2774588465690613,
      "z": -0.41012394428253174,
      "visibility": 0.9994297623634338,
      "presence": 0.9998718500137329
    },
    {
      "x": 0.4580107629299164,
      "y": 0.2772955000400543,
      "z": -0.3344292938709259,
      "visibility": 0.9989838004112244,
      "presence": 0.999413013458252
    },
    {
      "x": 0.5689696073532104,
      "y": 0.3658641576766968,
      "z": -0.6108775734901428,
      "visibility": 0.9999886751174927,
      "presence": 0.9999971389770508
    },
    {
      "x": 0.49811193346977234,
      "y": 0.35033223032951355,
      "z": 0.01693822629749775,
      "visibility": 0.9991482496261597,
      "presence": 0.9996933937072754
    },
    {
      "x": 0.5588861703872681,
      "y": 0.48897692561149597,
      "z": -0.612106442451477,
      "visibility": 0.9937264919281006,
      "presence": 0.9999678134918213
    },
    {
      "x": 0.488986611366272,
      "y": 0.4637357294559479,
      "z": 0.13065308332443237,
      "visibility": 0.004938873462378979,
      "presence": 0.9993686079978943
    },
    {
      "x": 0.4960425794124603,
      "y": 0.5900753736495972,
      "z": -0.5735718607902527,
      "visibility": 0.9805182218551636,
      "presence": 0.9999845027923584
    },
    {
      "x": 0.4452100694179535,
      "y": 0.5498652458190918,
      "z": 0.03534296900033951,
      "visibility": 0.006259607616811991,
      "presence": 0.9994340538978577
    },
    {
      "x": 0.4919741451740265,
      "y": 0.619450032711029,
      "z": -0.638391375541687,
      "visibility": 0.957688570022583,
      "presence": 0.9999452829360962
    },
    {
      "x": 0.43308424949645996,
      "y": 0.5785096883773804,
      "z": 0.007495216093957424,
      "visibility": 0.00933260191231966,
      "presence": 0.9991573095321655
    },
    {
      "x": 0.4634111225605011,
      "y": 0.6173489689826965,
      "z": -0.6551299095153809,
      "visibility": 0.9582549333572388,
      "presence": 0.9999339580535889
    },
    {
      "x": 0.4262951612472534,
      "y": 0.5780938267707825,
      "z": -0.05809260904788971,
      "visibility": 0.010466008447110653,
      "presence": 0.998981773853302
    },
    {
      "x": 0.4604554772377014,
      "y": 0.6074599623680115,
      "z": -0.5747277140617371,
      "visibility": 0.9202002286911011,
      "presence": 0.9999667406082153
    },
    {
      "x": 0.4276008903980255,
      "y": 0.567387580871582,
      "z": 0.0007659110124222934,
      "visibility": 0.011270111426711082,
      "presence": 0.9993935823440552
    },
    {
      "x": 0.5190989375114441,
      "y": 0.5658106207847595,
      "z": -0.1949155479669571,
      "visibility": 0.9999747276306152,
      "presence": 0.999998927116394
    },
    {
      "x": 0.47399595379829407,
      "y": 0.5552050471305847,
      "z": 0.1949213743209839,
      "visibility": 0.9999082088470459,
      "presence": 0.9999967813491821
    },
    {
      "x": 0.5195010304450989,
      "y": 0.692145824432373,
      "z": 0.16072872281074524,
      "visibility": 0.6931732892990112,
      "presence": 0.9999487400054932
    },
    {
      "x": 0.5059378147125244,
      "y": 0.676961362361908,
      "z": 0.4752119183540344,
      "visibility": 0.04160679876804352,
      "presence": 0.9999196529388428
    },
    {
      "x": 0.5295947194099426,
      "y": 0.8119202852249146,
      "z": 0.5300492644309998,
      "visibility": 0.7780268788337708,
      "presence": 0.9995399713516235
    },
    {
      "x": 0.5193599462509155,
      "y": 0.784217119216919,
      "z": 0.8516308069229126,
      "visibility": 0.11392507702112198,
      "presence": 0.9998090863227844
    },
    {
      "x": 0.5534792542457581,
      "y": 0.8371273875236511,
      "z": 0.5525386929512024,
      "visibility": 0.42359432578086853,
      "presence": 0.9984045624732971
    },
    {
      "x": 0.5436730980873108,
      "y": 0.807289183139801,
      "z": 0.8832737803459167,
      "visibility": 0.16298212110996246,
      "presence": 0.9996564388275146
    },
    {
      "x": 0.4167361855506897,
      "y": 0.8413560390472412,
      "z": 0.3502300977706909,
      "visibility": 0.7512513399124146,
      "presence": 0.9987906813621521
    },
    {
      "x": 0.4196301996707916,
      "y": 0.797217071056366,
      "z": 0.7728996872901917,
      "visibility": 0.26714015007019043,
      "presence": 0.9995280504226685
    }]


class UrlsTestCase(SimpleTestCase):

    def test_home_url(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func, views.home)

    def test_login_url(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class, auth_views.LoginView)

    def test_org_register_url(self):
        url = reverse('org_register')
        self.assertEqual(resolve(url).func, views.org_register)

    def test_member_register_url(self):
        url = reverse('member_register')
        self.assertEqual(resolve(url).func, views.member_register)

    def test_report_url(self):
        url = reverse('report')
        self.assertEqual(resolve(url).func, views.report)

    def test_policy_url(self):
        url = reverse('policy')
        self.assertEqual(resolve(url).func, views.policy)

    def test_logout_url(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func.view_class, auth_views.LogoutView)

    def test_password_change_url(self):
        url = reverse('password_change')
        self.assertEqual(resolve(url).func.view_class, views.CustomPasswordChangeView)

    def test_password_change_done_url(self):
        url = reverse('password_change_done')
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordChangeDoneView)

    def test_token_obtain_pair_url(self):
        url = reverse('token_obtain_pair')
        self.assertEqual(resolve(url).func.view_class, CustomTokenObtainPairView)

    def test_token_refresh_url(self):
        url = reverse('token_refresh')
        self.assertEqual(resolve(url).func.view_class, CustomTokenRefreshView)

    def test_request_auth_url(self):
        url = reverse('mobile-auth-request_auth')
        self.assertEqual(resolve(url).func, views_mobile.login_mobile)

    def test_login_kiosk_url(self):
        url = reverse('login_kiosk')
        self.assertEqual(resolve(url).func, views_kiosk.login_kiosk)

    def test_login_kiosk_id_url(self):
        url = reverse('login_kiosk_id')
        self.assertEqual(resolve(url).func, views_kiosk.login_kiosk_id)

    def test_get_userinfo_session_url(self):
        url = reverse('get_userinfo_session')
        self.assertEqual(resolve(url).func, views_kiosk.get_userinfo_session)

    def test_end_session_url(self):
        url = reverse('end_session')
        self.assertEqual(resolve(url).func, views_kiosk.end_session)

class OrgTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Org 생성
        self.org = OrganizationInfo.objects.create(organization_name='test_org')
        
        # 키오스크 <-> Org 매칭
        self.kiosk = KioskInfo.objects.update_or_create(
            kiosk_id=kiosk_id,
            defaults={'organization': self.org, 'active': True}
        )

        # 키오스크 세션 생성
        response = self.client.post('/api/login-kiosk/', {'kiosk_id': kiosk_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session_key = response.data['data']['session_key']

        # 키오스크 회원가입
        response = self.client.post('/api/signup-kiosk/', {'session_key': self.session_key, 'phone_number': '01058581212', 'password': '12345'}, format='json')

        # 응답값의 data안에 "status"의 int값이 0이면 OK 임
        self.assertEqual(response.data['data']['status'], 0)

        user1 = UserInfo.objects.filter(phone_number='01058581212').get()
        self.assertEqual(user1.organization, self.org)

        # 키오스크 로그인
        response = self.client.post('/api/login-kiosk-id/', {'session_key': self.session_key, 'phone_number': '01058581212', 'password': '12345'}, format='json')
        self.assertEqual(response.data['data']['data']['status'], 200)

        # 로그인 한 사용자 정보 조회
        response = self.client.get(f'/api/get-userinfo-session/?session_key={self.session_key}')
        self.assertEqual(response.data['data']['data']['phone_number'], '01058581212')

        

class GaitResultTests(TestCase):
    def setUp(self):
        self.kiosk_client = APIClient()

        # Create the required objects
        self.auth_info = AuthInfo.objects.create(uid=mobile_uid, phone_number=phone_number)
        self.user_info = UserInfo.objects.create(
            username=phone_number,
            phone_number=phone_number,
            password=make_password(password)
        )

        # Authenticate and get access token
        auth_response = self.kiosk_client.post('/api/mobile/login-mobile/', {'mobile_uid': mobile_uid}, format='json')
        auth_data = auth_response.json()['data']
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        self.mobile_client = APIClient()
        self.mobile_client.credentials(HTTP_AUTHORIZATION='Bearer ' + auth_data['jwt_tokens']['access_token'])

        # Login to kiosk and get session key
        response = self.kiosk_client.post('/api/login-kiosk/', {'kiosk_id': kiosk_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session_key = response.data['data']['session_key']

        # Login mobile using QR code
        response = self.mobile_client.post('/api/mobile/login-mobile-qr/', {'session_key': self.session_key},
                                           format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Login kiosk using ID and Password
        response = self.kiosk_client.post('/api/login-kiosk-id/',
                                          {'session_key': self.session_key, 'phone_number': phone_number,
                                           'password': password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Prepare gait data
        self.gait_data = {
            'session_key': self.session_key,
            'gait_data': {
                'velocity': 1.0,
                'cadence': 100,
                'cycle_time_l': 0.5,
                'cycle_time_r': 0.5,
                'stride_len_l': 1.0,
                'stride_len_r': 1.0,
                'supp_base_l': 0.1,
                'supp_base_r': 0.1,
                'swing_perc_l': 0.6,
                'swing_perc_r': 0.6,
                'stance_perc_l': 0.4,
                'stance_perc_r': 0.4,
                'd_supp_perc_l': 0.2,
                'd_supp_perc_r': 0.2,
                'toeinout_l': 5,
                'toeinout_r': 5,
                'stridelen_cv_l': 0.01,
                'stridelen_cv_r': 0.01,
                'stridetm_cv_l': 0.01,
                'stridetm_cv_r': 0.01,
                'score': 85
            }
        }

    def test_get_gait_result_success(self):
        # First, create a gait result
        self.kiosk_client.post(base_url + 'api/analysis/gait/create_result/', self.gait_data, format='json')
        response = self.kiosk_client.post(base_url + 'api/analysis/count/', {"session_key": self.session_key, "type": 3}, format='json') 
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Case 1 : using jwt Tokens (mobile)
        response = self.mobile_client.get(base_url + 'api/analysis/gait/get_result/', {'id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)

        # Case 2 : using session_key (kiosk)
        response = self.kiosk_client.get(base_url + 'api/analysis/gait/get_result/',
                                         {'session_key': self.session_key, 'id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)

    def test_create_gait_result_missing_session_key(self):
        invalid_data = {'gait_data': self.gait_data['gait_data']}  # No session key provided
        response = self.kiosk_client.post(base_url + 'api/analysis/gait/create_result/', invalid_data, format='json')
        self.assertEqual(response.data['data']['message'], 'session_key_required')


class BodyResultTests(TestCase):
    def setUp(self):
        self.kiosk_client = APIClient()

        # Create the required objects
        self.auth_info = AuthInfo.objects.create(uid=mobile_uid, phone_number=phone_number)
        self.user_info = UserInfo.objects.create(
            username=phone_number,
            phone_number=phone_number,
            password=make_password(password)
        )

        # Authenticate and get access token
        auth_response = self.kiosk_client.post('/api/mobile/login-mobile/', {'mobile_uid': mobile_uid}, format='json')
        auth_data = auth_response.json()['data']
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        self.mobile_client = APIClient()
        self.mobile_client.credentials(HTTP_AUTHORIZATION='Bearer ' + auth_data['jwt_tokens']['access_token'])

        # Login to kiosk and get session key
        response = self.kiosk_client.post('/api/login-kiosk/', {'kiosk_id': kiosk_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session_key = response.data['data']['session_key']

        # Login mobile using QR code
        response = self.mobile_client.post('/api/mobile/login-mobile-qr/', {'session_key': self.session_key},
                                           format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Login kiosk using ID and Password
        response = self.kiosk_client.post('/api/login-kiosk-id/',
                                          {'session_key': self.session_key, 'phone_number': phone_number,
                                           'password': password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check session status
        response = self.kiosk_client.get(f'/api/checksession/?session_key={self.session_key}')
        response = response.json()
        self.assertEqual(response['data']['status'], 200)

        # Prepare body data
        self.body_data = {
            'session_key': self.session_key,
            'body_data': {
                'face_level_angle': 1.0,
                'shoulder_level_angle': 2.0,
                'hip_level_angle': 3.0,
                'leg_length_ratio': 1.5,
                'left_leg_alignment_angle': 4.0,
                'right_leg_alignment_angle': 5.0,
                'left_back_knee_angle': 6.0,
                'right_back_knee_angle': 7.0,
                'forward_head_angle': 8.0,
                'scoliosis_shoulder_ratio': 1.1,
                'scoliosis_hip_ratio': 1.2,
            },
            "front_data" : {"keypoints" : keypoints},
            "side_data" : {"keypoints" : keypoints}, 
            'image_front': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAKUlEQVR42u3NMQEAAAgDINc/9IyhBxQgnXYORCwWi8VisVgsFovFf+MF6PxZxcf+kXQAAAAASUVORK5CYII=',
            'image_side': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAKUlEQVR42u3NMQEAAAgDINc/9IyhBxQgnXYORCwWi8VisVgsFovFf+MF6PxZxcf+kXQAAAAASUVORK5CYII='
        }

    def test_get_body_result_success(self):
        # First, create a body result
        response = self.kiosk_client.post(base_url + 'api/analysis/body/create_result/', self.body_data, format='json')
        response2 = self.kiosk_client.post(base_url + 'api/analysis/count/', {"session_key": self.session_key, "type": 4}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Case 1 : using jwt Tokens (mobile)
        response = self.mobile_client.get(base_url + 'api/analysis/body/get_result/', {'id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)

        # Case 2 : using session_key (kiosk)
        response = self.kiosk_client.get(base_url + 'api/analysis/body/get_result/',
                                         {'session_key': self.session_key, 'id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)

    def test_create_body_result_missing_session_key(self):
        invalid_data = {'body_data': self.body_data['body_data']}  # No session key provided
        response = self.kiosk_client.post(base_url + 'api/analysis/body/create_result/', invalid_data, format='json')
        self.assertEqual(response.data['data']['message'], 'session_key_required')


class mobileTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create the required objects
        self.auth_info = AuthInfo.objects.create(uid=mobile_uid, phone_number=phone_number)
        self.user_info = UserInfo.objects.create(
            username=phone_number,
            phone_number=phone_number,
            password=make_password(password)
        )

        # Authenticate and get access token
        auth_response = self.client.post('/api/mobile/login-mobile-id/', {'id': phone_number, 'password': password},
                                         format='json')
        auth_data = auth_response.json()['data']
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK) and self.assertIn('jwt_tokens', auth_data)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + auth_data['jwt_tokens']['access_token'])

    def test_get_user_success(self):
        response = self.client.post(base_url + 'api/mobile/user/get_user/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], dict)

    def test_delete_user_success(self):
        response = self.client.post(base_url + 'api/mobile/user/delete_user/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)




"""
키오스크 로직

1. 기관
- 계정 생성 후 Org 정보 등록
- 우리쪽에서 DB에 키오스크 등록 (KioskInfo에서 Org 정보 등록) - 키오스크 <-> 기관 매칭
- 키오스크 세션 생성
- 키오스크 회원가입 로직 (기관 회원가입)
- 키오스크 로그인
- 키오스크 세션 정보 조회
- 키오스크 세션 종료



"""