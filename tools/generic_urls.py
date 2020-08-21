from django.urls import path
import sys
import inspect


def add_url_from_generic_views(app_name):
    inspect.getmembers(__import__(app_name))
    urls = []
    for name, obj in inspect.getmembers(sys.modules[app_name]):
        if inspect.isclass(obj) and app_name in str(obj):
            model_name = obj.model._meta.model_name
            if "CreateView" in name:
                urls.append(path('%s/add/' % model_name, obj.as_view(), name="%s_add" % model_name))
            elif "DeleteView" in name:
                urls.append(path('%s/<int:pk>/delete' % model_name, obj.as_view(), name="%s_delete" % model_name))
            elif "DetailView" in name:
                urls.append(path('%s/<int:pk>/' % model_name, obj.as_view(), name="%s_detail" % model_name))
            elif "ListView" in name:
                urls.append(path('%s/' % model_name, obj.as_view(), name="%s_list" % model_name))
            elif "UpdateView" in name:
                urls.append(path('%s/<int:pk>/change/' % model_name, obj.as_view(), name="%s_change" % model_name))
    return urls
