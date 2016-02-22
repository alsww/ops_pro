#coding:utf-8

import time
import paramiko,json #
from hosts import models
from django.utils import timezone #导入django的时间 下面的时间存取 按照django项目配置来的  django是带时区的默认是格林威治时间
from s10ops import settings  #导入配置

def paramiko_sftp(task_id,host_obj,task_content,task_type,user_id):
    bind_host = host_obj
    try:
        t = paramiko.Transport((bind_host.host.ip_addr,int(bind_host.host.port) ))
        if bind_host.host_user.auth_type == 'ssh-password':

            t.connect(username=bind_host.host_user.username,password=bind_host.host_user.password)
        else:
            pass

            #key = paramiko.RSAKey.from_private_key_file(settings.RSA_PRIVATE_KEY_FILE)
            #t.connect(username=bind_host.host_user.username,pkey=key)

        sftp = paramiko.SFTPClient.from_transport(t)
        #字典jsonxuliehua
        task_dic = json.loads(task_content)
        #不管是send 还是get 我都要把存到数据库的记录的路径取出来
        if task_type == 'file_send':
            upload_files = task_dic['upload_files']
            for file_path in upload_files:
                file_abs_path = "%s/%s/%s" %(settings.FileUploadDir,user_id,file_path)  #组合的绝对路径
                print file_abs_path
                remote_filename = file_path.split("/")[-1]
                print '---\033[32;1m sending [%s] to [%s]\033[0m'% (remote_filename,task_dic['remote_path'])
                sftp.put(file_abs_path,"%s/%s" %(task_dic['remote_path'],remote_filename))
            cmd_result = "successfully send files %s to remote path [%s]" %(upload_files,task_dic['remote_path'])
            result = 'success'
        else:
            pass
    except Exception,e:
        print e
        cmd_result = e
        result = 'failed'

    #写到数据库  不然前端等着不知道传没传完
    log_obj= models.TaskLogDetail.objects.get(child_of_task_id=task_id,bind_host_id=bind_host.id)
    log_obj.event_log = cmd_result
    log_obj.date = timezone.now()
    log_obj.result = result
#
    log_obj.save()
def paramiko_ssh(task_id,host_obj,task_content):  # multi task 脚本调用该方法。
    #time.sleep(2)
    print 'going to run:',host_obj,task_content #测试打印
    #如下拷贝 paramiko
    bind_host = host_obj
    s = paramiko.SSHClient()
    s.load_system_host_keys()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if bind_host.host_user.auth_type == 'ssh-password':
            s.connect(bind_host.host.ip_addr,
                      int(bind_host.host.port),
                      bind_host.host_user.username,
                      bind_host.host_user.password,
                      timeout=5)
        else:#rsa_key
            pass
            '''
            key = paramiko.RSAKey.from_private_key_file(settings.RSA_PRIVATE_KEY_FILE)
            s.connect(bind_host.host.ip_addr,
                      int(bind_host.host.port),
                      bind_host.host_user.username,
                      pkey=key,
                      timeout=5)
            '''
        stdin,stdout,stderr = s.exec_command(task_content) #cmd 命令  看如下注释实例
        result = stdout.read(),stderr.read()
        cmd_result = filter(lambda x:len(x)>0,result)[0]   #filter只返回正确的
        print cmd_result
        #>>> correct = ('df','')
        #>>> err = ('','err')
        #>>> print filter(lambda x:len(x)>0,err)[0]
        #err
        #>>> print filter(lambda x:len(x)>0,correct)[0]
        #df
        #不管是错误指令 还是正确 只要执行都会按照成功创建任务来看。
        result = 'success'
    except Exception,e:
        print("\033[31;1m%s\033[0m" % e)
        #会返回两个值， 错误或者输出  直接锅炉
        cmd_result = e
        result = 'failed'

    for line in cmd_result:
        print line


    #下面的是将调用脚本执行的输出写入的数据库的表中  我们在task中调用脚本
    #我们是要修改已经创建的任务修改event——log 不是插入新纪录。所有我们要更改而不是新建 不然循环取会取出两个结果
    #log_obj = models.TaskLogDetail(
    ##   child_of_task_id = task_id,
    #   bind_host_id = bind_host.id,
    #   date= timezone.now(),
    #   event_log = cmd_result,
    #   result = result
    #)

    log_obj= models.TaskLogDetail.objects.get(child_of_task_id=task_id,bind_host_id=bind_host.id)
    log_obj.event_log = cmd_result
    log_obj.date = timezone.now()  #django的setting时间是格林尼治时区。所以我们要调整
    log_obj.result = result

    log_obj.save()