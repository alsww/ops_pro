#coding:utf-8
from django.contrib import admin

# Register your models here.

import auth_admin  #导入自定制的auth_admin

import models

#自定义admin 显示

#admin 表的显示 列详情
class HostAdmin(admin.ModelAdmin):
    list_editable = ('hostname','ip_addr')
    list_display = ('hostname','ip_addr','port','idc','system_type','enabled')
    search_fields = ('hostname','ip_addr')
    list_filter = ('idc','system_type')
class HostUserAdmin(admin.ModelAdmin):
    list_display = ('auth_type','username','password')

class BindHostToUserAdmin(admin.ModelAdmin):
    list_display = ('host','host_user','get_groups')
    filter_horizontal = ('host_groups',)  #管理很多主机的字段添加即可  还可以搜索
admin.site.register(models.UserProfile,auth_admin.UserProfileAdmin)  #
admin.site.register(models.Host,HostAdmin)
admin.site.register(models.HostGroup)
admin.site.register(models.HostUser,HostUserAdmin)
admin.site.register(models.BindHostToUser,BindHostToUserAdmin)
admin.site.register(models.IDC)
#admin后台显示的注册的表详情显示  不加的话不显示该表
admin.site.register(models.TaskLog)
admin.site.register(models.TaskLogDetail)