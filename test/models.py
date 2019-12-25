import uuid

from six import python_2_unicode_compatible

from django.db import models

# Create your models here.

@python_2_unicode_compatible
class Author(models.Model):
    name = models.CharField("Name", max_length=128)
    age = models.SmallIntegerField("Age", null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name

    def double_age(self):
        return self.age*2
    double_age.short_description = "Double Age"


@python_2_unicode_compatible
class Book(models.Model):
    title = models.CharField("Title", max_length=128)
    author = models.ForeignKey(Author)
    uuid = models.UUIDField(default=uuid.uuid4)

    class Meta:
        ordering = ('title',)
        verbose_name = "Book"
        verbose_name_plural = "Books"

    def __str__(self):
        return self.title
