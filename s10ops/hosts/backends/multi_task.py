#coding:utf-8

#这里其实是触发脚本 来在后台进行， 这里肯定是一个独立的脚本 起一个独立的进程，让操作系统维护，  host app下的新建的backends目录

#由于该脚本在task里面调， 启动一个由操作系统来维护的进程  需要设置环境变量   __file__

import  os,sys
#print os.path.dirname(os.path.abspath(__file__)) #获取目录
BaseDir = "\\".join(os.path.dirname(os.path.abspath(__file__)).split('\\')[:-2])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "s10ops.settings") #这里还得用django的一个方法   s10ops.settings  项目的设置
#加入环境变量
#print(BaseDir)
sys.path.append(BaseDir)

from hosts import models #上面的 加入全局环境变量后  跨文件目录 导入模块


import multiprocessing #多进程 模块

from django.core.exceptions import ObjectDoesNotExist #异常处理模块

import paramiko_handle #多进程 批量处理脚本 文件

import django  #环境变量设置 的时候 提示 模块未导入  就是这个原因
django.setup() #allow outsider scripts invoke django db models  允许外部的脚本 调用 djangodb 模块


def by_paramiko(task_id):
    try:
        task_obj = models.TaskLog.objects.get(id=task_id) #取任务id
        pool = multiprocessing.Pool(processes=5) #进程数量

        res = [] # 取个任务列表
        if task_obj.task_type == 'multi_cmd':
            for h in task_obj.hosts.select_related(): #循环主机的多对多关系查询
                p=pool.apply_async(paramiko_handle.paramiko_ssh,args=(task_id,h,task_obj.cmd))  #告诉它任务id 主机，通过obj 取出命令
                res.append(p) #加入到之前的列表
                print '--multi--38',h
        # 判断文件分发
        elif task_obj.task_type in ('file_send','file_get'):
            for h in task_obj.hosts.select_related():
                p=pool.apply_async(paramiko_handle.paramiko_sftp,args=(task_id,h,task_obj.cmd,task_obj.task_type,task_obj.user.id))
                res.append(p)
        #for r in res:  #循环列表取结果  有问题这种写法 用下面的方法
        #    print r.get()  #很多版本r.get出错

        #相当于循环上面的结果  取出来
        pool.close()
        pool.join()



    except  ObjectDoesNotExist,e:
        sys.exit(e)

def by_ansible(task_id):
    pass

def by_puppet(task_id):
    pass

if __name__ == '__main__':
#Python mult——task。py （参数后面的几个） -taskid + 值 + runtype（saltstack还是puppet）+ 值  ，，算上脚本名共5个
    required_args = ['-task_id','-run_type']  #定义参数类型


    for arg in required_args: #循环参数
        if not arg in sys.argv: #如果传过来的参数不是外部脚本的参数 退出
            sys.exit("arg [%s] is required!"% arg)

    if len(sys.argv) <5: #脚本名和参数长度 小于5 退出
        sys.exit("5 arguments expected but %s given"% len(sys.argv))

    task_id = sys.argv[sys.argv.index("-task_id") + 1 ] #找到id的位置  通过索引反定位
    run_type = sys.argv[sys.argv.index("-run_type") + 1 ]#找到id的位置  通过索引反定位

    if hasattr(__import__(__name__),run_type):  #上面的都听过 。我们反射方法来执行。。  hasattr 是通过其他文件的传过来的变量 到本文件的类中判断该类有没有这个方法，有的话，就执行调用。 而要在本文件中有函数 要匹配执行调用，用__import__(__name__)
        print 'hasattr'
        func = getattr(__import__(__name__),run_type)  #匹配该办法
        print '----taskid----',task_id
        func(task_id) #传进id
    else: #否则 退出
        sys.exit("Invalid run_type, only support [by_paramiko,by_ansible,by_saltstack]")