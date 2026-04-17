from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

def avatar_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'avatars/{instance.id}.{ext}'

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)

    def __str__(self):
        return self.username

class Question(models.Model):
    description = models.TextField()
    tags = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="questions", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description[:50] + "..." if len(self.description) > 50 else self.description

class Answer(models.Model):
    content = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.author.username}"

class Reply(models.Model):
    content = models.TextField()
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.author.username}"

class Like(models.Model):
    VOTE_TYPES = (
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, null=True, blank=True, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, null=True, blank=True, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, null=True, blank=True, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=10, choices=VOTE_TYPES, default='upvote')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('user', 'question'),
            ('user', 'answer'),
            ('user', 'reply'),
        ]

    def __str__(self):
        return f"{self.vote_type} by {self.user.username}"

class Notification(models.Model):
    NOTIFICATIONS_TYPE = (
        ('like', 'Like'),
        ('answer', 'Answer'),
        ('reply', 'Reply'),
        ('follow', 'Follow'),
        ('new_question', 'New Question'),
    )
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATIONS_TYPE)
    question = models.ForeignKey(Question, null=True, blank=True, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, null=True, blank=True, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, null=True, blank=True, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification_type} from {self.sender.username}"


class LoginSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='login_sessions')
    device = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    logged_in_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device}"


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} -> {self.following.username}"


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_sessions')
    device_name = models.CharField(max_length=255, default='Unknown')
    browser = models.CharField(max_length=100, default='Unknown')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    token = models.TextField(unique=True)
    refresh_token = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.device_name} - {self.browser}"
