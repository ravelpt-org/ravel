from django.contrib.auth.models import User, Group
from django.db import models


# Create your models here.

class Post(models.Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    post_time = models.DateTimeField(auto_now=True)
    comments = models.ManyToManyField("Comment")


class Comment(models.Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    post_time = models.DateTimeField(auto_now=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
