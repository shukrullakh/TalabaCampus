from django.contrib import admin
from .models import Question,Answer,Reply,Like,Notification,University,CustomUser

admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Reply)
admin.site.register(Like)
admin.site.register(Notification)
admin.site.register(University)