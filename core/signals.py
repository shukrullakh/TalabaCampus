from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Answer, Reply, Like, Notification, Follow, Question

@receiver(post_save, sender=Answer)
def create_answer_notification(sender, instance, created, **kwargs):
    if created:
        question_author = instance.question.author
        if instance.author != question_author:
            Notification.objects.create(
                recipient=question_author,
                sender=instance.author,
                notification_type='answer',
                question=instance.question,
            )

@receiver(post_save, sender=Reply)
def create_reply_notification(sender, instance, created, **kwargs):
    if created:
        answer_author = instance.answer.author
        if instance.author != answer_author:
            Notification.objects.create(
                recipient=answer_author,
                sender=instance.author,
                notification_type='reply',
                question=instance.answer.question,
                reply=instance,
            )

@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        target_user = None
        question = None
        if instance.question:
            target_user = instance.question.author
            question = instance.question
        elif instance.answer:
            target_user = instance.answer.author
            question = instance.answer.question
        elif instance.reply:
            target_user = instance.reply.author
            question = instance.reply.answer.question

        if target_user and instance.user != target_user:
            Notification.objects.get_or_create(
                recipient=target_user,
                sender=instance.user,
                notification_type='like',
                question=question,
            )

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='follow',
        )

@receiver(post_save, sender=Question)
def create_question_notification(sender, instance, created, **kwargs):
    if created:
        # Barcha followerlariga xabar yuboramiz
        followers = Follow.objects.filter(following=instance.author)
        notifications = [
            Notification(
                recipient=follow.follower,
                sender=instance.author,
                notification_type='new_question',
                question=instance,
            )
            for follow in followers
            if follow.follower != instance.author
        ]
        Notification.objects.bulk_create(notifications)
