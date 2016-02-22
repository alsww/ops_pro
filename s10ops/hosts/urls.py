#coding:utf-8
from django.conf.urls import include, url
import views

urlpatterns = [
    url("^$", views.hosts_index, name="hosts"),    #主页
    url("^host_mgr/$", views.host_mgr, name="host_mgr"),  #主机监控
    url("^multi_cmd/$", views.multi_cmd, name="multi_cmd"), #多命令

    url("^submit_task/$", views.submit_task, name="submit_task"),
    url("^gettaskresult/$", views.gettaskresult, name="gettaskresult"),
    url("^multi_file_transfer/$", views.multi_file_transfer, name="multi_file_transfer"),
    url("^file_upload/$", views.file_upload, name="file_upload"),
]
