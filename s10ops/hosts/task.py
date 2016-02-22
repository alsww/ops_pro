#coding:utf-8

import models
from django.db import transaction # 总任务已提交，但是下面执行的是循环，突然断电， 导致已执行的不能回滚，所以我们需要django的 tranaction方法来做到 前面的表格都创建和后面的表格都创建 统一commit。

from s10ops import  settings #导入setting 的脚本路径主要是
import subprocess #python 调用shell命令  和 command system类似
import os
import json

#example
'''
import subprocess
 subprocess.check_output(['df','-h'])
 subprocess.Popen(['df','-h']).read()
'''


class Task(object):
    def __init__(self,request):
        self.request= request #将request 传过来
        self.task_type = self.request.POST.get("task_type") #获取任务类型

    def handle(self):  #反射函数调用各种办法
        if self.task_type:
            func = getattr(self,self.task_type)
            return func()

    # 总任务已提交，但是下面执行的是循环，突然断电， 导致已执行的不能回滚，所以我们需要django的 tranaction方法来做到 前面的表格都创建和后面的表格都创建 统一commit。
    @transaction.atomic
    def multi_cmd(self):
        print '---going to run cmd----'
        print '---',self.request.POST #测试打印  字典
        selected_hosts = set(self.request.POST.getlist("selected_hosts[]"))  #赋值主机列表  取列表用getlist
        cmd = self.request.POST.get("cmd")
        #create task info 数据库tasklog表数据创建  如果直接用object.create 的方法不会返回创建成功。 如果先赋值变量，再save可以看到返回创建成功与否
        task_obj = models.TaskLog(
            task_type = self.task_type,
            user_id = self.request.user.id,
            #manyto many 必须 在创建完纪录后再添加
            cmd = cmd,
        )
        task_obj.save()  #写入到数据库 相当于 create
        #多对多关系不能在创建记录的时候添加，如上的（） 需要再创建记录有再添加。  必须在创建完纪录后再添加
        task_obj.hosts.add(*selected_hosts) #添加m2m关系  manytomany方式添加列表 用add（*列表）  添加字典是两个* add（**字典）
        #测试打印  添加列表  用*号代替如下添加方式。 添加 manytomany
        #task_obj.hosts.add([1,2,3])

        #================================任务详情表创建信息 #create task detail record for all the hosts will be executed later
        for bind_host_id in selected_hosts:
            obj =models.TaskLogDetail(
            child_of_task_id = task_obj.id,  #总任务的id
            bind_host_id = bind_host_id, #绑定主机的id
            event_log = "N/A", #现在先把详情 写空
                #剩下的是default 在表里面
        )
            obj.save()  # from django.db import transaction 这里又一个点，如果我有几千台主机这样的话我创建一个任务就会 save相当于 在数据库里面 commit  创建一次任务就有好几千次 commit 压力可想而知；第二点 像上面的任务 执行成功提交，总任务已提交，但是下面执行的是循环，突然断电， 导致已执行的不能回滚，所以我们需要django的 tranaction方法来做到 前面的表格都创建和后面的表格都创建 统一commit。



        #================================任务详情表创建信息



        #这里其实是触发脚本 来在后台进行， 这里肯定是一个独立的脚本 起一个独立的进程，让操作系统维护，  host app下的新建的backends目录

        #调用 paramiko的脚本   脚本路径我们统一在setting中配置  下面添加 脚本的参数

        p = subprocess.Popen([
            'python',
            settings.MultiTaskScript,
            '-task_id',str(task_obj.id),
            '-run_type',settings.MultiTaskRunType, #在setting中配置
        ])#,preexec_fn=os.setsid)
        print '----->pid:',p.pid

        return {'task_id':task_obj.id}

        #我们在view中response 的话就要序列化一个字典
    def multi_file_transfer(self):
        print '----going to handle file uploading/download'


        selected_hosts = set(self.request.POST.getlist("selected_hosts[]"))
        transfer_type = self.request.POST.get("file_transfer_type")
        remote_path = self.request.POST.get("remote_path")
        upload_files = self.request.POST.getlist("upload_files[]")
        #create task info
        data_dic = {
            'remote_path':remote_path,
            'upload_files':upload_files,
        }
        task_obj = models.TaskLog(
            task_type = transfer_type,
            user_id = self.request.user.id,
            #manyto many 必须 在创建完纪录后再添加
            cmd = json.dumps(data_dic), #没有单独的存放文件路径 跟文件名的字段 我把信息存在cmd字段内  但是不能存字典 要序列化成字符串
        )
        task_obj.save()
        task_obj.hosts.add(*selected_hosts) #添加m2m关系
        #task_obj.hosts.add([1,2,3])

        #create task detail record for all the hosts will be executed later
        for bind_host_id in selected_hosts:
            obj =models.TaskLogDetail(
                child_of_task_id = task_obj.id,
                bind_host_id = bind_host_id,
                event_log = "N/A",
            )
            obj.save()

        #invoke backend multitask script
        p = subprocess.Popen([
            'python',
            settings.MultiTaskScript,
            '-task_id',str(task_obj.id),
            '-run_type',settings.MultiTaskRunType,
        ])#,preexec_fn=os.setsid)
        print '----->pid:',p.pid


        return {'task_id': task_obj.id}

    def get_task_result(self):
        task_id = self.request.GET.get('task_id') #获取的任务id 去数据库取命令输出表取出命令输出详情
        print task_id

        if task_id:
            res_list = models.TaskLogDetail.objects.filter(child_of_task_id=task_id)  #赋值过滤 id  此时是一个Python的数据对象，jsondump都不成功  必须点valule一下 （res_list.values） 变成一个列表包着的字典。 还是一个类，我们 将其变成一个字典 list一下 list（res_list.values）
            # 如上有下面的格式解释   list（res_list.values）  列表包着的字典  可以在内容再获取 字段。。。 注意了。。。
            #如下有时间 错误
            #json.dump(res,default=)  在view视图内的返回的时候加个时间判断    return HttpResponse(json.dumps(res,default=utils.json_date_handler))

            return list(res_list.values('id',
                                        'bind_host__host__hostname',
                                        'bind_host__host__ip_addr',
                                        'bind_host__host_user__username',
                                        'date',
                                        'event_log',
                                        'result',
                                        ))

