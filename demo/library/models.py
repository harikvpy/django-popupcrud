# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.db import models

from six import python_2_unicode_compatible

# Create your models here.

@python_2_unicode_compatible
class Author(models.Model):
    name = models.CharField("Name", max_length=128)
    penname = models.CharField("Pen Name", max_length=128)
    age = models.SmallIntegerField("Age", null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name

    def double_age(self):
        return self.age*2 if self.age else ''
    double_age.label = "Double Age"


@python_2_unicode_compatible
class Book(models.Model):
    title = models.CharField(_("Title"), max_length=128)
    isbn = models.CharField("ISBN", max_length=12)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        ordering = ('title',)
        verbose_name = "Book"
        verbose_name_plural = "Books"

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class AuthorRating(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    rating = models.CharField("Rating", max_length=1, choices=(
        ('1', '1 Star'),
        ('2', '2 Stars'),
        ('3', '3 Stars'),
        ('4', '4 Stars'),
    ))

    class Meta:
        ordering = ('author',)
        verbose_name = "Author Rating"
        verbose_name = "Author Ratings"

    def __str__(self):
        return "%s - %s" % (self.author.name, self.rating)


@python_2_unicode_compatible
class BookRating(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.CharField("Rating", max_length=1, choices=(
        ('1', '1 Star'),
        ('2', '2 Stars'),
        ('3', '3 Stars'),
        ('4', '4 Stars'),
    ))

    class Meta:
        ordering = ('book',)
        verbose_name = "Book Rating"
        verbose_name = "Book Ratings"

    def __str__(self):
        return "%s - %s" % (self.book.title, self.rating)
