from django.urls import path, include, converters, register_converter
from . import views
from rest_framework.routers import DefaultRouter
from fcm_django.api.rest_framework import FCMDeviceViewSet

from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    TokenRefreshView,
    # TokenVerifyView,
)

class NegativeIntConverter(converters.IntConverter):
    regex = r'-?\d+'
register_converter(NegativeIntConverter, 'negint')    

urlpatterns = [
    path("bag/", views.BagView.as_view()),
    path("gears/", views.GearView.as_view({"get": "list", "post": "create"})),
    path("gears/<negint:token_id>", views.GearView.as_view({"get": "retrieve"})),
    path("things/", views.ThingView.as_view()),
    path("recommend/", views.RecommendationView.as_view()),
    
    path("exercises/", views.ExerciseView.as_view({"get": "list", "post": "create"})),
]

urlpatterns += [
    path("token/refresh/", TokenRefreshView.as_view()),
]
urlpatterns += [
    path("history/<int:year>/<int:month>/", views.ExerciseMonthView.as_view()),
    path("history/<int:year>/<int:month>/<int:day>/", views.ExerciseDayView.as_view()),
    path("history/<negint:token_id>/", views.ExerciseNFTView.as_view()),
]

urlpatterns += [
    path("task/", views.ExerciseWeekView.as_view()),
    path("gacha/", views.GachaAPIView.as_view()),
    path("target/<int:token_id>", views.WearView.as_view({"put": "_update"})),
    path(
        "dress/<negint:token_id>",
        views.WearView.as_view({"put": "update", "delete": "destroy"}),
    ),
    path(
        "coupon/<negint:token_id>",
        views.couponView.as_view({"put": "update", "delete": "destroy"}),
    ),
    path(
        "coupon/",
        views.couponView.as_view({"get": "list"}),
    ),
]

urlpatterns += [
    path("read/", views.readView.as_view()),  # test only
    # path("mint/", views.mintView.as_view()),
]
# .list(), .retrieve(), .create(), .update(), .partial_update(), .destroy()

router = DefaultRouter()
router.register('devices', FCMDeviceViewSet)

urlpatterns += [
    path("msg/test/", views.MSGView.as_view()),
]

urlpatterns += router.urls

router = DefaultRouter()
router.register('devices', FCMDeviceViewSet)