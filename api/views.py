# from django.shortcuts import render
from datetime import datetime, timedelta
import os
import numpy as np
import random
from collections import defaultdict
from firebase_admin.messaging import Message, Notification

from accounts.models import User
from api.utils.ethereum import mint_test, read_test, w3
from .models import Coupon, Thing, Gear, Exercise, Wear, WeekTask
from accounts.permissions import IsOwnerOrAdmin, IsUserOrAdmin
from django.db import transaction
from django.db.models import Sum, Value, F, IntegerField,ExpressionWrapper, Count, Avg, Min
from fcm_django.models import FCMDevice
from django.http import Http404
from django.db.models.functions import Coalesce, TruncDate
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveUpdateDestroyAPIView


from .serializers import (
    CouponSerializers,
    GearSerializers,
    MintSerializers,
    ThingSerializers,
    ExerciseSerializers,
    WearSerializers,
    WearUpdateSerializers,
)


class BagView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        things = user.thing_set.all().exclude(amount=0).order_by("type")
        gears = user.gear_set.all().order_by("type", "level")
        thing_serializer = ThingSerializers(things, many=True)
        gear_serializer = GearSerializers(gears, many=True)
        return Response(
            {"gears": gear_serializer.data, "things": thing_serializer.data}
        )


class ThingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        things = user.thing_set.all().exclude(amount=0).order_by("type")
        serializer = ThingSerializers(things, many=True)
        return Response(serializer.data)


class GearView(ModelViewSet):
    permission_classes = [IsOwnerOrAdmin]
    serializer_class = MintSerializers
    lookup_field = "token_id"

    def get_queryset(self):
        if self.action == "list":
            return Gear.objects.filter(user=self.request.user)
        else:
            return Gear.objects.all()

    def create(self, request, *args, **kwargs):
        address = request.user.address
        serializer = MintSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lucky = self.generate_lucky(data.get("lucky"))
        logs = {"type": data.get("type"), "level": data.get("level"), "lucky": lucky}
        hex_logs = w3.to_hex(text=str(logs))
        decode_logs = w3.to_text(hex_logs)
        print(f"hex_logs: {hex_logs}", f"decode_logs: {decode_logs}", sep="\n")

        try:
            res = mint_test(address, hex_logs)
        except Exception as err:
            print("error:", err)
            return Response({"error": type(err).__name__}, status=401)

        status = res.pop("status", None)
        token_id = res.pop("token_id")

        if not status:
            return Response({"error": "mint error"}, status=400)

        gear = serializer.save(user=request.user, token_id=token_id, lucky=lucky)

        return Response(
            {"tx": res, "uri": gear.uri, "gear": {**serializer.data}}, status=200
        )

    def generate_lucky(self, type):
        lucky_choices = [type, "epic"]
        lucky_weights = [1 - Gear.PROB_EPIC[type], Gear.PROB_EPIC[type]]
        _type = random.choices(lucky_choices, weights=lucky_weights)[0]
        _range = Gear.LUCKY_RANGE[_type]
        lucky = random.randint(_range[0] * 100, _range[1] * 100) / 100
        # return math.floor(random.uniform(lower, upper) * 100) / 100  # exclusive
        return lucky

    # def retrieve(self, request, *args, **kwargs):
    #     try:
    #         instance = self.get_object()
    #         serializer = self.get_serializer(instance)
    #         return Response(serializer.data, status=200)
    #     except Exception as err:
    #         print(err)
    #         raise NotFound("Object not found.")

    # def list(self, request, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data, status=200)

    # def get(self, request, pk=None):
    #     user = request.user
    #     if pk == None:
    #         gears = user.gear_set.all().order_by("type", "level")
    #         serializer = GearSerializers(gears, many=True)
    #         return Response(serializer.data)
    #     else:
    #         try:
    #             gear = user.gear_set.get(pk=pk)
    #             serializer = GearSerializers(gear)
    #             return Response(serializer.data, status=200)
    #         except Gear.DoesNotExist:
    #             return Response({'message': 'Gear not found'}, status=404)

    # class GearView(ModelViewSet):
    #     queryset = Gear.objects.all()
    #     serializer_class = GearSerializers
    #     permission_classes = [IsAuthenticated]

    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)

class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):  # 抓取特定user以及當前月份完成運動的紀錄
        user = request.user

        gear = user.gear_set.filter(finish_date__isnull=False).order_by("finish_date").last()
        e = user.exercise_set.filter(max=True).order_by("timestamp").last()
        
        if not e:
            return Response({"message":"trial..."})
        gear=e.gear
        
        exercises = user.exercise_set.filter(gear=gear)
        time_range = exercises.values_list('timestamp__date', flat=True).order_by('timestamp__date').distinct()
        diff = [(time_range[x]-time_range[x-1]).days for x in range(1, len(time_range))]
  
        arr = self.remove_outliers(diff)
        avg_diff = arr.mean()
        
        e = exercises.values('timestamp__date').annotate(
            date=F('timestamp__date'),
            total_count=Sum('count'),
            total_valid_count=Sum(F('count') * F('accuracy')),
            mean_count=Avg('count'),
            mean_valid_count=Avg(F('count') * F('accuracy')),
            num_of_record=Count('id')
        ).order_by("timestamp__date")
        avg_daily_valid_count = e.aggregate(mean_vaild_count=Avg("total_valid_count"))["mean_vaild_count"]
        
        orientation = "workout" if avg_diff >= 2.5 else "health"
        if avg_daily_valid_count < 30:
            level = 0
        elif avg_daily_valid_count < 60:
            level = 1
        else:
            level = 2
        return Response({"orientation":orientation, "level":level, "avg_daily_valid_count": avg_daily_valid_count, "avg_diff":avg_diff})
    
    def remove_outliers(self, arr, threshold=1.5):
        mean = np.mean(arr)
        std = np.std(arr)
        z_scores = (arr - mean) / std
        outliers = np.where(np.abs(z_scores) > threshold)[0]
        filtered_arr = np.delete(arr, outliers)
        return filtered_arr
    
class ExerciseView(ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializers
    permission_classes = [IsAuthenticated] #記得更新

    def gacha(self, user):
         # 設定各等級小物的機率值
        probabilities = Thing.probabilities
        # 根據機率隨機獲取一個等級
        choices = [*probabilities.keys()]
        values = [*probabilities.values()]
        level = random.choices(choices, weights=values)[0]

        # 檢查是否已經有同一等級的thing存在
        existing_thing = Thing.objects.filter(user=user, type=level).first()

        if existing_thing:
            # 如果已存在，將amount加一
            existing_thing.amount += 1
            existing_thing.save()
            new_thing = existing_thing
        else:
            # 否則創建新的thing
            new_thing = Thing.objects.create(user=user, type=level)
            new_thing.amount = 1
            new_thing.save()

        # 返回結果
        return {
            "message": "You got a new thing x 1",
            "type": new_thing.type,
            "amount": new_thing.amount,
        }
    def workout_task(self, task):
        today = datetime.now().date()
        exercises = task.user.exercise_set.order_by("-timestamp__date")
        last_complete = exercises.first().timestamp.date() if exercises.exists() else None  
        
        if task.count == 0 or not last_complete or (today - last_complete).days > 3 or task.count == 7 and today > last_complete:
            task.week_start = today
            task.count = 1
            return "DAILY_COMPLETE", None
        
        task.count += 1
        if task.count < 7:
            return "DAILY_COMPLETE", None
            
        return "WEEKLY_COMPLETE", self.gacha(task.user)
    
    def healthy_task(self, task):
        if task.delta > timedelta(days=task.count) or task.delta >= timedelta(days=7):
            task.count = 0
            
        today = datetime.now().date()

        gacha = None    
        if task.delta == timedelta(days=task.count) and task.count != 0:  # 連續
            task.count += 1
            if task.count >= 7:
                # message = "完成每周任務"
                status = "WEEKLY_COMPLETE"
                gacha = self.gacha(task.user)
            else:
                # message = "完成本日任務"
                status = "DAILY_COMPLETE"
        else:  # delta > timedelta(days=task.count)
            task.week_start = today
            task.count = 1
            # message = "完成首日任務"
            status = "DAILY_COMPLETE"
        return status, gacha
    
    def handle_task(self, exercise, user):
        if exercise.exists():
            return None
        
        task = user.task
        orientation = user.wear.target.orientation
        if orientation != "workout":
            status, gacha = self.healthy_task(task)
        else:
            status, gacha = self.workout_task(task)
            
        task.save()  # 保存更新後的 WeekTask
        res = {"status": status, "count": task.count}
   
        return {**res, "thing":gacha} if gacha else res

    def handle_thing(self, request, data, valid_count, lucky):  # type 轉成string, 待改
        thing_level = data.get("thing")
        if thing_level == None:
            return None

        thing = Thing.objects.filter(user=request.user, type=thing_level).first()
        if not thing or thing.amount == 0:
            raise PermissionDenied("You don't have any thing of given type")

        thing.amount -= 1
        thing.save()

        bonus = Thing.weights.get(thing_level, 1)
        res = ThingSerializers(thing).data
        res["bonus"] = round(valid_count * bonus * lucky, 2)
        return res

    @transaction.atomic  # # transaction.set_rollback(True)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # gear = data.get("gear")
        count = data.get("count")
        accuracy = data.get("accuracy")
        # validated_data['accuracy'] = 
        valid_count = round(count * accuracy)
        
        today = datetime.now().date()

        # if gear.user != request.user:
        #     raise PermissionDenied("You are not allowed to modify this gear.")
        # user = request.user if request.user.is_authenticated else User.objects.get(username="root") #測試完移除
        user = request.user
        
        gear = user.wear.target
        
        if gear is None:
            raise PermissionDenied("You haven't set the target gear !")
        
        if gear.isMax:
            raise PermissionDenied("This gear has already reached Max Level")
                    
        if valid_count < gear.work_min:
            return Response({"status":"WORKMIN_FAILED", "message":"workmin isn't reached !", "workmin": gear.work_min, "valid_count":valid_count})

        daily_exercise = Exercise.objects.filter(
            timestamp__date=today, user=user
        )

        current_count = (
            daily_exercise.filter(
                user=user,
            ).aggregate(total=Coalesce( Sum(ExpressionWrapper(F("count") * F("accuracy"), output_field=IntegerField())), Value(0)))
        )["total"]
    
        
        if current_count >= gear.work_max:
            raise PermissionDenied(
                "You have already reached the maximum exp for this gear today"
            )

        left_count = gear.work_max - current_count
        daily_max_flag = False
        
        _valid_count = valid_count
        if  valid_count >= left_count:
            _valid_count = left_count
            daily_max_flag = True
   
        thing = self.handle_thing(request, data, valid_count, gear.lucky)
        bonus = thing.get("bonus", 0) if thing else 0
        task = self.handle_task(daily_exercise, gear.user)
        
        exp = round(_valid_count * gear.lucky + bonus, 2)
        delta = gear.goal_exp - gear.exp
        gear.exp = min(round(gear.exp + exp, 2), gear.goal_exp)
        
        if gear.isMax:
            exp = delta
            gear.finish_date = today
            data["max"] = True
            
        gear.save()
        serializer.save(user=user, gear=gear, exp=exp)

        return Response(
            {
                "exp": exp,
                "gear_exp": gear.exp,
                "valid_count":valid_count,
                "daily_valid_count": current_count + valid_count,
                "daily_max_flag": daily_max_flag,
                "gear_max_flag": gear.isMax, 
                "task": task,
                "thing": thing,
            },
            status=200,
        )

    # def perform_create(self, serializer):  #
    #     data = serializer.validated_data
    #     gear = data.get("gear")
    #     accuracy = data.get("accuracy")  # or from server
    #     count = data.get("count")

    #     if gear.user != self.request.user:
    #         raise PermissionDenied("You are not allowed to modify this gear.")

    #     gear.exp += accuracy  # calculate exp with exercise...
    #     gear.save()

    #     serializer.save()


class ExerciseDayView(APIView):  # 使用者每日運動種類與次數 目前是直接加總
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month, day):
        query = Exercise.objects.filter(
                user=request.user,
                timestamp__year=year,
                timestamp__month=month,
                timestamp__day=day,
            )

        exercises = (
            query
            .values("type")
            .annotate(
                exp=Sum('exp'), 
                valid_count=Sum(ExpressionWrapper(F("count") * F("accuracy"), output_field=IntegerField())),
                count=Sum('count'), 
            )
            # .annotate(total_count=Sum("count"))
        )
        
        things = (query.values("thing").filter(thing__isnull=False)
        .annotate(type=F("thing"), count=Count('thing', output_field=IntegerField()))
        .values("type", "count"))
        

        total_things = things.aggregate(total_thing=Coalesce(Sum("count"), Value(0)))
        total_count = exercises.aggregate(total_count=Sum("count"))
        total_daily_exp = exercises.aggregate(total_daily_exp=Sum("exp"))
        total_valid_count = exercises.aggregate(total_vaild_count=Sum("valid_count"))
        
        result_data = {
            item["type"]: {**item} for item in exercises
        }
        things = {
            item["type"]: {**item} for item in things
        }

        things = [ things.get(type[0]) if things.get(type[0],None) else {"type":type[0], "count":0} for type in Thing.Type.choices]

        empty = {k:0 for k in ["exp","valid_count","count"]}
        result = [ result_data.get(type[0]) if result_data.get(type[0],None) else {"type":type[0], **empty} for type in Exercise.Type.choices]
        
        res = {**total_count, **total_daily_exp, **total_valid_count, **total_things, "exercise":ExerciseSerializers(query, many=True).data}
        return Response(res if len(exercises)>0 else [])


class ExerciseMonthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month):  # 抓取特定user以及當前月份完成運動的紀錄
        exercises = (
            Exercise.objects.filter(
                user=request.user,
                timestamp__year=year,
                timestamp__month=month,
            ).dates(
                "timestamp",
                "day",
            )
            # .values_list("timestamp__day", flat=True)
        )

        print(exercises)

        return Response(list(exercises))

class ExerciseNFTView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, token_id):  # 抓取特定user以及當前月份完成運動的紀錄
        e = Exercise.objects.filter(
            user=request.user,
            gear__token_id=token_id,
        )
        if not e:
            raise PermissionDenied("You don't have this gear")
        time_range = e.values_list('timestamp__date', flat=True).distinct()
        start_date = time_range[0] if len(time_range) <= 30 else time_range[len(time_range)-30]
        
        exercises = e.filter(
            timestamp__date__gte=start_date
        ).values('timestamp__date', 'type').annotate(
            date=F('timestamp__date'),
            total_count=Sum('count'),
            total_valid_count=Sum(F('count') * F('accuracy')),
            total_exp=Sum('exp'),
            mean_count=Avg('count'),
            mean_valid_count=Avg(F('count') * F('accuracy')),
            mean_exp=Avg('exp'),
            mean_accuracy=Sum(F('count') * F('accuracy')) / Sum('count'),
            num_of_record=Count('id')
        ).order_by("timestamp__date")
        types = exercises.values_list("type", flat=True)
        exercises = exercises.values("total_count","total_valid_count", "total_exp", "mean_count","mean_valid_count", "mean_exp", "mean_accuracy","num_of_record","date")
        res = defaultdict(list)
        for _type, exercise in zip(types, exercises):
            res[_type].append(exercise)
        return Response(res)
    
class ExerciseWeekView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):  # 抓取特定user以及當前月份完成運動的紀錄
        user = request.user
        task = user.task
        orientation = user.wear.target.orientation
        res = self.workout(user, task) if orientation == "workout" else self.healthy(task)
        
        return Response(res)
    
    def healthy(self, task):
        today = datetime.now().date()

        if task.delta > timedelta(days=task.count) or task.delta >= timedelta(days=7):
            task.week_start = today
            task.count = 0
            task.save()
        # exercise_days = Exercise.objects.filter(timestamp__range=(start, end))
        days = [
            {"date": task.week_start + timedelta(i), "done": i < task.count}
            for i in range(7)
        ]

        return {"dates": days, "count": task.count}   
         
    def workout(self, user, task):
        today = datetime.now().date()
        exercises = user.exercise_set.order_by("-timestamp__date")
        last_complete = exercises.first().timestamp.date() if exercises.exists() else None
        
        

        if task.count == 0 or not last_complete or (today - last_complete).days > 3 or task.count == 7 and today > last_complete:
            task.week_start = today
            task.count = 0
            task.save()
            days = [
              {"date": today + timedelta(3*i), "done": False} for i in range(7)
            ]
            return {"dates": days, "count": 0}   

        days = exercises.values_list("timestamp__date", flat=True).distinct()[:task.count:-1]
        d = 7 - task.count
        while d > 0:
            days.append(days[-1] + timedelta(days=3))
            d -= 1
        days = [
            {"date": day, "done": i < task.count}
            for i, day in enumerate(days)
        ]
        return {"dates": days, "count": task.count}   


class GachaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 設定各等級小物的機率值
        probabilities = Thing.probabilities
        # 根據機率隨機獲取一個等級
        choices = [*probabilities.keys()]
        values = [*probabilities.values()]
        level = random.choices(choices, weights=values)[0]

        # 檢查是否已經有同一等級的thing存在
        existing_thing = Thing.objects.filter(user=request.user, type=level).first()

        if existing_thing:
            # 如果已存在，將amount加一
            existing_thing.amount += 1
            existing_thing.save()
            new_thing = existing_thing
        else:
            # 否則創建新的thing
            new_thing = Thing.objects.create(user=request.user, type=level)
            new_thing.amount = 1
            new_thing.save()

        # 返回結果
        response_data = {
            "message": "You got a new thing x 1",
            "type": new_thing.type,
            "amount": new_thing.amount,
        }
        return Response(response_data)


class WearView(ModelViewSet):
    permission_classes = [IsAuthenticated]

    serializer_class = WearUpdateSerializers
    lookup_field = "token_id"

    def get_queryset(self):
        return self.request.user.gear_set

    # def get_object(self):
    #     token_id = self.kwargs.get("token_id")
    #     if self.request.method == "PUT":
    #         serializer = self.get_serializer(data=self.request.data)
    #         serializer.is_valid(raise_exception=True)
    #         token_id = serializer.data.get("token_id")

    #     gear = self.get_queryset().filter(token_id=token_id).first()
    #     if gear is None:
    #         raise PermissionDenied(
    #             f"You are not allowed to modify this gear ({token_id})"
    #         )
    #     return gear
    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {"detail": "You are not allowed to modify this gear"}, status=403
            )

        return super().handle_exception(exc)

    def update(self, request, *args, **kwargs):
        gear = self.get_object()
        wear = request.user.wear

        if getattr(wear, gear.pos) == gear:
            raise PermissionDenied("This gear is already dressed")

        setattr(wear, gear.pos, gear)
        wear.save()
        return Response(
            {"message": f"Update successfully", "dress": wear.dress}, status=200
        )

    def _update(self, request, *args, **kwargs):
        gear = self.get_object()
        wear = request.user.wear
        if wear.target == gear:
            raise PermissionDenied("This gear is already targeted")
        if gear.isMax:
            raise PermissionDenied("This gear has already reached Max Level")
            
        wear.target = gear
        wear.save()
        return Response(
            {"message": f"Update target successfully", "target": wear._target},
            status=200,
        )

    def destroy(self, request, *args, **kwargs):
        gear = self.get_object()
        wear = request.user.wear

        if getattr(wear, gear.pos) != gear:
            raise PermissionDenied("This gear isn't dressed.")

        setattr(wear, gear.pos, None)
        wear.save()
        return Response(
            {"message": f"Undress successfully", "dress": wear.dress}, status=200
        )

    # def perform_update(self, serializer):
    #     # Ensure the wear object belongs to the authenticated user
    #     instance = serializer.instance
    #     if instance.user != self.request.user:
    #         return Response({"error": "You are not allowed to update this wear object."},
    #                         status=403)


#    def update(self, request, *args, **kwargs):
#         partial = kwargs.pop("partial", False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response(
#             {"message": "updated successfully", "data": serializer.data}, status=200
#         )

#     def partial_update(self, request, *args, **kwargs):
#         kwargs["partial"] = True
#         return self.update(request, *args, **kwargs)


class couponView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CouponSerializers
    lookup_field = "token_id"

    def get_queryset(self):
        return self.request.user.gear_set

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {"detail": "You are not allowed to modify this gear"}, status=403
            )

        return super().handle_exception(exc)

    def destroy(self, request, *args, **kwargs):
        gear = self.get_object()
        if gear.coupon is None:
            raise PermissionDenied("This gear has not been exchanged")
        gear.coupon = None
        gear.save()
        return Response({"message": f"Delete successfully", "coupon": None}, status=200)

    def list(self, request, *args, **kwargs):
        coupons = self.get_queryset().filter(coupon__isnull=False).order_by("level")
        serializer = CouponSerializers(coupons, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        gear = self.get_object()
        if gear.coupon is not None:
            raise PermissionDenied("This gear is already exchanged")

        if not gear.is_exchangeable:
            raise PermissionDenied("This gear is not exchangeable")

        serializer = self.get_serializer(gear, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(coupon_date=datetime.now().date())

        return Response(
            {"message": f"Exchange successfully", "coupon": serializer.data}, status=200
        )


class readView(APIView):
    def get(self, request):
        try:
            res = read_test(request.user.address)
            return Response(res, status=200)
        except Exception as err:
            print(err)
            return Response({"error": str(err)}, status=400)


class FCMView(APIView):
    authentication_classes = []

    def get(self, request):
        try:
            return render(request, 'index.html')
        except Exception as err:
            return Response({"error": str(err)}, status=400)

    def post(self, request):
        try:
            user = request.user
            return Response({"USER:": user}, status=400)
        except Exception as err:
            return Response({"error": str(err)}, status=400)


class MSGView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            devices = FCMDevice.objects.all()
            devices.send_message(
                Message(
                    notification=Notification(
                        title="From DREAM", body="It's time to workout!")
                ),
            )
            return Response("message sent")
        except Exception as err:
            return Response({"error": str(err)}, status=400)

# class mintView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         address = request.user.address
#         serializer = MintSerializers(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         res = mint_test(address)

#         if res["tx"].get("status"):
#             lucky_probabilities = {0: 0.4, 1: 0.3, 2: 0.2, 3: 0.1}
#             lucky_choices = list(lucky_probabilities.keys())
#             lucky_weights = list(lucky_probabilities.values())
#             lucky = random.choices(lucky_choices, weights=lucky_weights)[0]
#             gear = serializer.save(
#                 user=request.user, token_id=res["token_id"], lucky=lucky
#             )

#             return Response({"tx": res["tx"], "gear": serializer.data}, status=200)

#         return Response({"error": "mint error"}, status=400)
