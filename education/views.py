from django.shortcuts import render
from rest_framework import viewsets, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from education.models import Course, Lesson, Payment, Subscription
from education.serializers import CourseSerializer, LessonSerializer, PaymentSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from education.permissions import CustomPermission
from education.paginators import CoursePagination
from education.tasks import send_update_course


class MixinQueryset:
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(owner=self.request.user.pk)
        return queryset


'''COURSE ViewSets'''
# ----------------------------------------------------------------


class CourseViewSet(MixinQueryset, viewsets.ModelViewSet):
    '''ViewSet Course'''
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [CustomPermission]
    pagination_class = CoursePagination

    def perform_create(self, serializer):
        new_course = serializer.save(owner=self.request.user)
        new_course.owner = self.request.user
        new_course.save()
        if new_course:
            send_update_course.delay(new_course.course.id)


'''LESSON generics'''
# ----------------------------------------------------------------


class LessonCreateAPIView(generics.CreateAPIView):
    '''CREATE Lesson'''
    serializer_class = LessonSerializer
    permission_classes = [CustomPermission]

    def perform_create(self, serializer):
        new_lesson = serializer.save(owner=self.request.user)
        new_lesson.owner = self.request.user
        new_lesson.save()
        if new_lesson:
            send_update_course.delay(new_lesson.course.id)


class LessonListAPIView(MixinQueryset, generics.ListAPIView):
    '''READ ALL Lesson'''
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    pagination_class = CoursePagination


class LessonRetrieveAPIView(MixinQueryset, generics.RetrieveAPIView):
    '''READ ONE Lesson'''
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()


class LessonUpdateAPIView(MixinQueryset, generics.UpdateAPIView):
    '''UPDATE PUT AND PATCH Lesson'''
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()

    def perform_update(self, serializer):
        new_lesson = serializer.save(owner=self.request.user)
        new_lesson.owner = self.request.user
        new_lesson.save()
        if new_lesson:
            send_update_course.delay(new_lesson.course.id)


class LessonDestroyAPIView(generics.DestroyAPIView):
    '''DELETE Lesson'''
    queryset = Lesson.objects.all()
    permission_classes = [CustomPermission]


'''PAYMENT generics'''
# ----------------------------------------------------------------


class PaymentListAPIView(generics.ListAPIView):
    '''READ ALL Payments, Добавлена фильтрация'''
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['course', 'lesson', 'payment_method']
    ordering_fields = ['payment_date']
    permission_classes = [IsAuthenticated]


'''SUBSCRIPTION viewset '''
# ----------------------------------------------------------------


class SubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()

    def perform_create(self, serializer):
        new_subscription = serializer.save()
        new_subscription.user = self.request.user
        new_subscription.save()
