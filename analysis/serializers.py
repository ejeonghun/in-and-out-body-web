from rest_framework import serializers

from analysis.models import UserInfo, UserHist, SessionInfo, SchoolInfo, GaitResult, BodyResult, CodeInfo, Keypoint, FamilyUserInfo

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from datetime import datetime as dt
from analysis.helpers import generate_presigned_url

class CodeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeInfo
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']

class SessionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionInfo
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']

class SchoolInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolInfo
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']

class UserHistSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHist
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']

class GaitResultSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    student_name = serializers.CharField(source='user.student_name', read_only=True)
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = GaitResult
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']


class BodyResultSerializer(serializers.ModelSerializer):
    family_user_id = serializers.IntegerField(required=False)  # 가족 ID 관련

    class Meta:
        model = BodyResult
        fields = '__all__'
        read_only_fields = ['id']


class KioskInfoSerializer(serializers.Serializer):
    class Meta:
        model = BodyResult
        fields = '__all__'
        read_only_fields = ['id']



class GaitResponseSerializer(serializers.Serializer):
    data = GaitResultSerializer(many=True)
    message = serializers.CharField(default="OK")
    status = serializers.IntegerField(default=200)

class BodyResponseSerializer(serializers.Serializer):
    data = BodyResultSerializer(many=True)
    message = serializers.CharField(default="OK")
    status = serializers.IntegerField(default=200)

class KeypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keypoint
        fields = ['body_result', 'pose_type', 'x', 'y', 'z', 'visibility', 'presence']


class FamilyUserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyUserInfo
        fields = '__all__'
        read_only_fields = ['id', 'created_dt']


class FamilyUserResponseSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = FamilyUserInfo
        fields = ['id', 'family_member_name', 'gender', 'relationship', 'profile_image_url']

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            print(type(obj.created_dt))
            created_dt = obj.created_dt.strftime('%Y%m%dT%H%M%S%f')
            return generate_presigned_url(file_keys=['profile/profile', created_dt])
        return None  # 이미지가 없을 경우 None 반환