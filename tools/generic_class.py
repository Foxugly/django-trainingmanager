from urllib.parse import urljoin

from django.conf import settings
from django.db import models
from django.urls import reverse


class GenericClass(models.Model):
    class Meta:
        abstract = True

    app_label = None
    app_name = None
    model_name = None
    change_url = None
    add_url = None
    detail_url = None
    list_url = None

    def __init__(self, *args, **kwargs):
        self.app_name = self._meta.app_label
        self.model_name = self._meta.model_name
        self.change_url = '%s:%s_change' % (self.app_name, self.model_name)
        self.add_url = '%s:%s_add' % (self.app_name, self.model_name)
        self.detail_url = '%s:%s_detail' % (self.app_name, self.model_name)
        self.delete_url = '%s:%s_delete' % (self.app_name, self.model_name)
        self.list_url = '%s:%s_list' % (self.app_name, self.model_name)
        super(GenericClass, self).__init__(*args, **kwargs)

    def get_edit_url(self):
        return reverse(self.change_url, kwargs={'pk': self.pk})

    def get_change_url(self):
        return reverse(self.change_url, kwargs={'pk': self.pk})

    def get_add_url(self):
        return reverse(self.add_url)

    def get_absolute_url(self):
        return reverse(self.detail_url, kwargs={'pk': self.pk})

    def get_full_url(self):
        return urljoin(settings.WEBSITE, self.get_absolute_url())

    def get_detail_url(self):
        return reverse(self.detail_url, kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse(self.delete_url, kwargs={'pk': self.pk})

    def get_list_url(self):
        return reverse(self.list_url)
