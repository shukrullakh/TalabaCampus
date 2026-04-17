from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from .models import UserSession, Question, Answer, Reply, Notification, Like, LoginSession
from .serializers import QuestionSerializer, AnswerSerializer, ReplySerializer, NotificationSerializer, RegisterSerializer, LoginSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

def get_device_name(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'iphone' in ua: return 'iPhone'
    if 'ipad' in ua: return 'iPad'
    if 'android' in ua and 'mobile' in ua: return 'Android telefon'
    if 'android' in ua: return 'Android planshet'
    if 'macintosh' in ua or 'mac os' in ua: return 'Mac kompyuter'
    if 'windows' in ua: return 'Windows kompyuter'
    if 'linux' in ua: return 'Linux kompyuter'
    return "Noma'lum qurilma"

def get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            email_or_username = request.data.get('email_or_username')
            user = User.objects.filter(email=email_or_username).first()
            if not user:
                user = User.objects.filter(username=email_or_username).first()
            if user:
                device = get_device_name(request)
                ip = get_ip(request)
                LoginSession.objects.create(user=user, device=device, ip_address=ip)
                # UserSession (yangi)
                ua_string = request.META.get('HTTP_USER_AGENT', '')
                device_name, browser = parse_user_agent(ua_string)
                access_token = data.get('access', '')
                refresh_token = data.get('refresh', '')
                UserSession.objects.create(
                    user=user,
                    device_name=device_name,
                    browser=browser,
                    ip_address=ip or None,
                    user_agent=ua_string[:500],
                    token=access_token,
                    refresh_token=refresh_token,
                )
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_vote_count(type_, id_, vote_type):
    if type_ == 'question':
        return Like.objects.filter(question_id=id_, vote_type=vote_type, answer_id__isnull=True, reply_id__isnull=True).count()
    elif type_ == 'answer':
        return Like.objects.filter(answer_id=id_, vote_type=vote_type, question_id__isnull=True, reply_id__isnull=True).count()
    elif type_ == 'reply':
        return Like.objects.filter(reply_id=id_, vote_type=vote_type, question_id__isnull=True, answer_id__isnull=True).count()
    return 0


class LikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        type_ = request.data.get('type')
        id_ = request.data.get('id')
        vote_type = request.data.get('vote_type', 'upvote')

        if not type_ or not id_:
            return Response({'error': 'type va id kerak'}, status=400)

        filters = {'user': user}
        if type_ == 'question':
            filters['question_id'] = id_
        elif type_ == 'answer':
            filters['answer_id'] = id_
        elif type_ == 'reply':
            filters['reply_id'] = id_
        else:
            return Response({'error': "type noto'g'ri"}, status=400)

        existing = Like.objects.filter(**filters).first()
        if existing:
            existing.delete()
            voted = None
        else:
            Like.objects.create(**filters, vote_type='upvote')
            voted = "upvote"

        return Response({
            "voted": voted,
            "upvotes": get_vote_count(type_, id_, 'upvote'),
        })

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
        })

    def patch(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
        })

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current = request.data.get('current_password')
        new_pass = request.data.get('new_password')
        if not request.user.check_password(current):
            return Response({'error': "Joriy parol noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_pass) < 8:
            return Response({'error': "Yangi parol kamida 8 ta belgi bo'lishi kerak"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(new_pass)
        request.user.save()
        return Response({'message': 'Parol muvaffaqiyatli yangilandi'})

class ChangeUsernameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        new_username = request.data.get('new_username')
        if not new_username:
            return Response({'error': "Yangi foydalanuvchi nomi kerak"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=new_username).exists():
            return Response({'error': "Bu foydalanuvchi nomi allaqachon mavjud"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.username = new_username
        request.user.save()
        return Response({'message': 'Foydalanuvchi nomi muvaffaqiyatli yangilandi'})

class LoginSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if session_id:
            sessions = LoginSession.objects.filter(user=request.user, id=session_id)
        else:
            sessions = LoginSession.objects.filter(user=request.user).order_by('-logged_in_at')[:1]
        return Response([{
            'id': s.id,
            'device': s.device,
            'ip_address': s.ip_address,
            'logged_in_at': s.logged_in_at,
        } for s in sessions])

    def delete(self, request, session_id=None):
        if session_id:
            LoginSession.objects.filter(id=session_id, user=request.user).delete()
            return Response({'message': 'Session tugatildi'})
        # Barcha sessionlarni o'chirish (joriyidan tashqari)
        latest = LoginSession.objects.filter(user=request.user).order_by('-logged_in_at').first()
        if latest:
            LoginSession.objects.filter(user=request.user).exclude(id=latest.id).delete()
        return Response({'message': 'Barcha sessionlar tugatildi'})

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('-created_at')
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all().order_by('-created_at')
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

class ReplyViewSet(viewsets.ModelViewSet):
    queryset = Reply.objects.all().order_by('-created_at')
    serializer_class = ReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_read = request.data.get('is_read', instance.is_read)
        instance.save()
        return Response(self.get_serializer(instance).data)


class UserProfileView(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=404)
        
        questions_count = user.questions.count()
        answers_count = user.answers.count()
        
        return Response({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
            'questions_count': questions_count,
            'answers_count': answers_count,
            'date_joined': user.date_joined,
        })


from .models import UserSession, Follow

class FollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=404)

        if target == request.user:
            return Response({'error': 'O\'zingizni follow qila olmaysiz'}, status=400)

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target
        )

        if not created:
            follow.delete()
            return Response({'following': False, 'followers_count': target.followers.count()})

        return Response({'following': True, 'followers_count': target.followers.count()})

    def get(self, request, user_id):
        is_following = Follow.objects.filter(
            follower=request.user,
            following_id=user_id
        ).exists()
        return Response({'following': is_following})


class UserDetailView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=404)

        followers_count = user.followers.count()
        following_count = user.following.count()
        questions_count = user.questions.count()
        answers_count = user.answers.count()

        is_following = False
        if request.user.is_authenticated:
            is_following = Follow.objects.filter(follower=request.user, following=user).exists()

        avatar_url = None
        if user.avatar:
            avatar_url = request.build_absolute_uri(user.avatar.url)

        return Response({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'avatar': avatar_url,
            'followers_count': followers_count,
            'following_count': following_count,
            'questions_count': questions_count,
            'answers_count': answers_count,
            'is_following': is_following,
        })


class SuggestedUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Allaqachon follow qilinganlar
        already_following = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        # O'zini ham chiqarib tashlaymiz
        exclude_ids = list(already_following) + [request.user.id]

        # Eng faol foydalanuvchilar (ko'p savol/javob berganlar)
        from django.db.models import Count
        suggested = User.objects.exclude(id__in=exclude_ids).annotate(
            activity=Count('questions') + Count('answers')
        ).order_by('-activity')[:10]

        data = []
        for user in suggested:
            avatar_url = None
            if user.avatar:
                avatar_url = request.build_absolute_uri(user.avatar.url)
            data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar': avatar_url,
                'questions_count': user.questions.count(),
                'answers_count': user.answers.count(),
                'followers_count': user.followers.count(),
            })
        return Response(data)


import requests as req_lib

class AIProxyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        messages = request.data.get('messages', [])
        try:
            res = req_lib.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": "Bearer REMOVED_API_KEY",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sen TalabaCampus platformasining AI yordamchisissan. Talabalar o'qish, dasturlash, fanlar bo'yicha savol berishadi. Javoblarni qisqa, aniq va foydali qil. O'zbek tilida so'rashsa o'zbek tilida, rus tilida so'rashsa rus tilida, ingliz tilida so'rashsa ingliz tilida javob ber."
                        },
                        *messages
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
                timeout=30
            )
            return Response(res.json())
        except Exception as e:
            return Response({"error": str(e)}, status=500)


def parse_user_agent(ua_string):
    ua = ua_string.lower()
    # Device
    if 'iphone' in ua:
        device = 'iPhone'
    elif 'ipad' in ua:
        device = 'iPad'
    elif 'android' in ua and 'mobile' in ua:
        device = 'Android Telefon'
    elif 'android' in ua:
        device = 'Android Planshet'
    elif 'macintosh' in ua or 'mac os' in ua:
        device = 'Mac'
    elif 'windows' in ua:
        device = 'Windows PC'
    elif 'linux' in ua:
        device = 'Linux'
    else:
        device = 'Noma\'lam qurilma'

    # Browser
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Edge'
    elif 'chrome' in ua and 'safari' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'opera' in ua or 'opr/' in ua:
        browser = 'Opera'
    else:
        browser = 'Noma\'lam brauzer'

    return device, browser


class UserSessionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user, is_active=True)
        current_token = str(request.auth)
        data = []
        for s in sessions:
            data.append({
                'id': s.id,
                'device_name': s.device_name,
                'browser': s.browser,
                'ip_address': s.ip_address,
                'created_at': s.created_at,
                'last_activity': s.last_activity,
                'is_current': s.token == current_token,
            })
        return Response(data)


class UserSessionDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, session_id):
        try:
            session = UserSession.objects.get(id=session_id, user=request.user)
            session.is_active = False
            session.save()
            # Refresh tokenni blacklist ga qo'shamiz
            try:
                if session.refresh_token:
                    token = RefreshToken(session.refresh_token)
                    token.blacklist()
            except Exception as e:
                print("Blacklist error:", e)
            return Response({'message': 'Session tugatildi'})
        except UserSession.DoesNotExist:
            return Response({'error': 'Session topilmadi'}, status=404)


class UserSessionLogoutAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_token = str(request.auth)
        sessions = UserSession.objects.filter(
            user=request.user, is_active=True
        ).exclude(token=current_token)
        for session in sessions:
            try:
                if session.refresh_token:
                    token = RefreshToken(session.refresh_token)
                    token.blacklist()
            except Exception as e:
                print("Blacklist error:", e)
        sessions.update(is_active=False)
        return Response({'message': 'Barcha sessionlar tugatildi'})
