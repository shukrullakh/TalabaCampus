from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (QuestionViewSet, ReplyViewSet, AnswerViewSet,
    NotificationViewSet, LikeView, ProfileView, ChangePasswordView, ChangeUsernameView,
    LoginSessionsView, FollowView, UserDetailView, SuggestedUsersView, AIProxyView,
    UserSessionListView, UserSessionDeleteView, UserSessionLogoutAllView)

router = DefaultRouter()
router.register(r'questions', QuestionViewSet)
router.register(r'answers', AnswerViewSet)
router.register(r'replies', ReplyViewSet)
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = router.urls + [
    path('like/', LikeView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('change-username/', ChangeUsernameView.as_view()),
    path('login-sessions/', LoginSessionsView.as_view()),
    path('users/<int:user_id>/', UserDetailView.as_view()),
    path('users/<int:user_id>/follow/', FollowView.as_view()),
    path('users/suggested/', SuggestedUsersView.as_view()),
    path('ai/chat/', AIProxyView.as_view()),
    path('sessions/', UserSessionListView.as_view()),
    path('sessions/<int:session_id>/delete/', UserSessionDeleteView.as_view()),
    path('sessions/logout-all/', UserSessionLogoutAllView.as_view()),
    path('login-sessions/<int:session_id>/delete/', LoginSessionsView.as_view()),
]
