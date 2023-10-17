from django.urls import path, include
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


# authentication
urlpatterns = [
    # path("login/", views.LoginView.as_view()),
    path("user/logout/", views.LogoutView.as_view()),
    path("user/signup/", views.UserView.as_view({"post": "create"})),
    path("user/signin/", views.SignInView.as_view()),
    path("user/nonce/", views.fetchNonce.as_view()),
]

# development only !
urlpatterns += [
    path("users/", views.UserView.as_view({"get": "list"})),
    path("user/<int:pk>/detail/", views.UserView.as_view({"get": "retrieve"})),
]

# GET, PATCH, PUT, Delete user profile
urlpatterns += [
    path("user/<str:address>/", views.ProfileView.as_view()),
]

urlpatterns += [
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    #  path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("api/token/refresh/", TokenRefreshView.as_view()),
]
