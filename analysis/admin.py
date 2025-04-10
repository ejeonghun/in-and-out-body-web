from django.contrib import admin
from .models import UserInfo, GaitResult, BodyResult, SessionInfo, SchoolInfo, UserHist, KioskInfo, OrganizationInfo, KioskCount
from django.contrib.auth.hashers import make_password
from django.forms import ModelForm


@admin.register(BodyResult)
class BodyResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'formatted_created_dt')

    @staticmethod
    def user_id(user):
        return user.id

    @staticmethod
    def formatted_created_dt(obj):
        return obj.created_dt.strftime('%Y-%m-%d %H:%M:%S')  # 한국 형식으로 포맷팅

class UserInfoForm(ModelForm): # 비밀번호를 암호화해서 저장하도록 하는 커스텀 폼 
    class Meta:
        model = UserInfo
        fields = '__all__'  # 모든 필드 포함

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            return make_password(password)  # 비밀번호를 암호화하여 저장
        return self.instance.password  # 기존 비밀번호 유지

@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    form = UserInfoForm
    list_display = ('username', 'phone_number', 'formatted_created_dt')

    @staticmethod
    def formatted_created_dt(obj):
        return obj.created_dt.strftime('%Y-%m-%d %H:%M:%S')  # 한국 형식으로 포맷팅
    

@admin.register(KioskCount)
class KioskCountAdmin(admin.ModelAdmin):
    list_display = ('formatted_kiosk','formatted_created_dt')

    @staticmethod
    def formatted_kiosk(obj):
        kiosk = KioskInfo.objects.filter(id=obj.kiosk_id)
        print(kiosk.get().kiosk_id)
        print(kiosk.get().Org)
        if kiosk.get().Org != None:
            return f"{kiosk.get().Org} - {kiosk.get().kiosk_id} (회원 보행/체형 : {obj.type1}회, {obj.type2}회 /// 비회원 보행/체형 : {obj.type3}회, {obj.type4}회)"
        else:
            return f"기관/학교 정보 없음 - {kiosk.get().kiosk_id} (회원 보행/체형 : {obj.type1}회, {obj.type2}회 /// 비회원 보행/체형 : {obj.type3}회, {obj.type4}회)"
    
    @staticmethod
    def formatted_created_dt(obj):
        return obj.created_dt.strftime('%Y-%m-%d %H:%M:%S')  # 한국 형식으로 포맷팅

admin.site.register([GaitResult, SessionInfo, SchoolInfo, UserHist, KioskInfo, OrganizationInfo])
