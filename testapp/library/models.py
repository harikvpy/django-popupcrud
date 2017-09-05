# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.encoding import python_2_unicode_compatible

from django.db import models

# Create your models here.

@python_2_unicode_compatible
class Author(models.Model):
    name = models.CharField(max_length=128)
    penname = models.CharField(max_length=128)
    age = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Book(models.Model):
    title = models.CharField(max_length=128)
    author = models.ForeignKey(Author)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title
