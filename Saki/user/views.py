from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from .authentications import CustomAuthentication, create_token
from .serializers import UserSerializer
from .models import User, Otp
from random import randint
import requests


class Register(APIView):
    '''
    Required fields {"username": "<your username>, "phone": "<your phone number>", "country_code": "<your country code>"}
    Note: phone number is a 9 digit without '0' at the beginning .ex (504XXXXXX).
          Enter country code with '+' .ex(+966), default is (+966).
    '''
    def post(self, request):
        user = UserSerializer(data=request.data)
        if user.is_valid(raise_exception=True):
            user.save()
            return Response(data="User created", status=status.HTTP_201_CREATED)
        else:
            raise APIException(detail=user.errors)


class Login(APIView):
    '''
    Take the phone number and send an otp code to the user.
    phone number is a 9 digit without '0' at the beginning .ex (504XXXXXX).
    '''
    def post(self, request):
        phone = request.data.get('phone')
        try:
            user = User.objects.get(phone=phone)
        except:
            raise APIException(detail='Phone number not found!')
        
        code = user.country_code.lstrip('+')
        phone = code+phone
        otp = randint(1000, 9999)
        
        # url = 'https://el.cloud.unifonic.com/rest/SMS/messages'
        # param = {
        #     "AppSid": "hQAqafSG6BAbBpmSp6Yj4f93MNS0KL",
        #     "Recipient": phone,
        #     "Body": f"Your login code {otp}",
        # }
        
        otp_duration = timezone.now()+timezone.timedelta(minutes=5)

        Otp.objects.create(
            user=user,
            code=otp,
            expirey=otp_duration,
            utilized=False
        )
        
        # otp_response = requests.post(url=url, data=param)
        # if otp_response.status_code != 200:
        #     return otp_response
        return Response(data='OTP code sent')
    

class Verify_Otp(APIView):
    '''
    Verify the entered otp code to the generated code.
    '''
    def post(self, request):
        try:
            otp_code = request.data.get('code')
            otp_data = Otp.objects.get(code=otp_code)
            user = User.objects.get(username=otp_data.user)
        except:
            raise APIException(detail='Wrong code')
        
        if otp_data.utilized == False:
            if timezone.now() < otp_data.expirey:
                token = create_token(id=user.id, username=user.username, phone=user.phone)
                responce = Response(data="Login successfull", status=status.HTTP_200_OK)
                responce.set_cookie(key="jwt", value=token, httponly=True)
                otp_data.utilized = True
                otp_data.save()
                return responce
            else:
                return Response(data='Expired OTP code')
        else:
            return Response(data='OTP code been used before')
        
    # def post(self, request):
    #     try:
    #         email = request.data.get("email")
    #         email = email.lower()
    #         user = User.objects.get(email=email)
    #     except:
    #         raise APIException(detail="Wrong credentials")

    #     try:
    #         password = request.data.get("password")
    #         check_password(password=password, encoded=user.password)
    #     except:
    #         raise APIException(detail="Wrong credentials")

    #     token = create_token(id=user.id, username=user.username, email=user.email)
    #     responce = Response(data="Login successfull", status=status.HTTP_200_OK)
    #     responce.set_cookie(key="jwt", value=token, httponly=True)
    #     return responce


class UserProfile(APIView):
    authentication_classes = [
        CustomAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        user = User.objects.get(id=request.user.id)
        data = request.data
        serializer = UserSerializer(instance=user, data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(data="Successfully updated", status=status.HTTP_200_OK)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = User.objects.get(id=request.user.id)
        user.delete()
        response = Response(data="User deleted", status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("jwt")
        return response


class Logout(APIView):
    authentication_classes = [
        CustomAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        responce = Response(data="Logout Successfull", status=status.HTTP_200_OK)
        responce.delete_cookie("jwt")
        return responce
