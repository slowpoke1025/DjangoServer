from accounts.tokens import create_jwt
from api.models import Wear, WeekTask, Gear
from .models import User
from .permissions import IsUserOrAdmin
from .serializers import ProfileSerializers, UserSerializers
from api.serializers import MintSerializers
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.db.models import Min
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from siwe import SiweMessage, generate_nonce


class fetchNonce(APIView):
    def get(self, request):
        try:
            address = request.GET.get("address", None)
            user = User.objects.get(address=address)
            return Response({"nonce": user.nonce}, status=200)

        except User.DoesNotExist:
            return Response(
                {
                    "nonce": generate_nonce(),
                    "error": "UserDoesNotExist",
                    "redirect": "/signup",
                },
                status=200,
            )
        except Exception as err:
            print("error:", type(err).__name__)
            return Response({"error": type(err).__name__}, status=401)


def siweVerify(request):
    message = request.data.get("message")
    signature = request.data.get("signature")
    siweMessage = SiweMessage(message=message)
    address = siweMessage.address
    user = User.objects.filter(address=address).first()
    nonce = user.nonce if user else siweMessage.nonce
    siweMessage.verify(signature, nonce=nonce)
    print("verify")
    if user:
        user.nonce = generate_nonce()
        user.save()

    return user, address


class jwtForever(APIView):
    def get(self, request):
        user = request.user
        serializer = ProfileSerializers(user)
        data = serializer.data
        tokens = create_jwt(user, data)
        return Response(tokens)

class SignInView(APIView):
    def post(self, request):
        try:
            if request.user.is_authenticated:
                return Response({"error": "Login Already, Logout first"}, status=403)

            user, address = siweVerify(request)

            if not user:
                raise User.DoesNotExist

            serializer = ProfileSerializers(user)
            data = serializer.data
            tokens = create_jwt(user, data)

            # login(request, user)

            return Response(
                {"message": f"Signin as {address}", "user": data, "tokens": tokens},
                status=200,
            )

        except User.DoesNotExist:
            return Response(
                {
                    "message": "User does not exist",
                    "error": "UserDoesNotExist",
                    "redirect": "/signup",
                },
                status=404,
            )

        except Exception as err:
            print("error:", type(err).__name__)
            return Response({"error": type(err).__name__}, status=401)


class UserView(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializers

    # def perform_create(self, serializer):
    #     password = make_password(serializer.validated_data["password"])
    #     serializer.save(password=password)

    def get_permissions(self):
        if self.action == "post":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsUserOrAdmin]
        return [permission() for permission in permission_classes]

    def trial_gear(self, user):
        min_id = Gear.objects.aggregate(Min("token_id"))['token_id__min']
        _type = Gear.TRIAL_TYPE[0] if user.gender == "Male" else Gear.TRIAL_TYPE[1]
        return Gear.objects.create(user=user, token_id=min_id-1, level=3, lucky=1, type=_type)
    
    def create(self, request, *args, **kwargs):
        try:
            _, address = siweVerify(request)
        except Exception as err:
            print("error:", type(err).__name__)
            return Response({"error": type(err).__name__}, status=401)
        
        serializer = self.get_serializer(data=request.data.get("user"))
        serializer.is_valid(raise_exception=True)
        user = serializer.save(address=address)
        res = ProfileSerializers(user)
        WeekTask.objects.create(user=user)
        Wear.objects.create(user=user)
        gear = self.trial_gear(user)
        user.wear.target = gear
        user.wear.hair = gear
        user.wear.save()
        data = res.data
        tokens = create_jwt(user, data)

        return Response(
            {"message": f"Signup as {address}", "user": data, "tokens": tokens},
            status=201,
        )


class ProfileView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializers
    permission_classes = [IsUserOrAdmin]
    lookup_field = "address"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "User deleted successfully"}, status=200)

    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     return Response({'message': 'Book updated successfully'}, status=200)

    # def partial_update(self, request, *args, **kwargs):
    #     kwargs['partial'] = True
    #     return self.update(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        logout(request)
        request.session.clear()
        return Response(
            {
                "message": f"{user.username}: Logout successfully",
            },
            status=200,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        # password = request.data.get("password")
        # user = authenticate(username=username, password=password)
        user = authenticate(request, username=username)

        # if request.user.is_authenticated:
        #     return Response({"message": request.user.username}, status=200)
        if user:
            login(request, user)
            return Response({"message": "Login successfully"}, status=200)
        else:
            return Response({"message": "Invalid credentials"}, status=401)
