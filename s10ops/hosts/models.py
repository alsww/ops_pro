#coding:utf-8
from django.db import models

# Create your models here.


from myauth import  UserProfile

class Host(models.Model):  #主机表
    hostname = models.CharField(max_length=64)  #主机名 可以重名
    ip_addr = models.GenericIPAddressField(unique=True) #ip地址  不可以重名
    port = models.IntegerField(default=22)  #端口 可以重
    idc = models.ForeignKey('IDC')  #机房 是外键管理
    system_type_choices= (  #机器类型
        ('linux','Linux'),
        ('windows','Windows'),
    )
    system_type = models.CharField(choices=system_type_choices,max_length=32,default='linux') #默认要选择， 默认是linxu
    enabled = models.BooleanField(default=True)  # 是否可用 布尔类型
    memo = models.TextField(blank=True,null=True)  # 说明  blank 是 admin 可以为空  null 为true是 数据库为空二者缺一不可
    date = models.DateTimeField(auto_now_add=True)  #创建日期

    def __unicode__(self):
        return  "%s(%s)" %(self.hostname,self.ip_addr)
    class Meta:  #为了在admin中显示中文给表写的别名
        verbose_name = u'主机列表'   #复数形式 取消 不然后台admin都有s
        verbose_name_plural = u"主机列表"
class IDC(models.Model):
    name = models.CharField(unique=True,max_length=64)
    memo = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return  self.name

class HostUser(models.Model):
    auth_type_choices = (
        ('ssh-password', 'SSH/PASSWORD'),
        ('ssh-key', 'SSH/KEY'),
    )  #认证方式选择
    auth_type = models.CharField(choices=auth_type_choices,max_length=32,default='ssh-password')
    username = models.CharField(max_length=64)  #用户名可以重名
    password = models.CharField(max_length=128,blank=True,null=True) #要保证唯一性， 用户名 密码 类型必须三者是唯一的

    def __unicode__(self):
        return "(%s)%s" %(self.auth_type,self.username)

    class Meta:  #要保证唯一性， 用户名 密码 类型必须三者是唯一的
        unique_together = ('auth_type','username','password')
        verbose_name = u'远程主机用户'  #去复数
        verbose_name_plural = u"远程主机用户" #去复数
class HostGroup(models.Model):
    name = models.CharField(unique=True,max_length=64)  #
    memo = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return  self.name
    class Meta:
        verbose_name = u'主机组'
        verbose_name_plural = u"主机组"
class BindHostToUser(models.Model):  #主机绑定关系
    host = models.ForeignKey("Host")
    host_user= models.ForeignKey("HostUser")
    #host_user= models.ManyToManyField("HostUser")
    host_groups = models.ManyToManyField("HostGroup")

    class Meta:
        unique_together = ('host','host_user')
        verbose_name = u'主机与用户绑定关系'
        verbose_name_plural = u"主机与用户绑定关系"
    def __unicode__(self):
        return  '%s:%s' %(self.host.hostname, self.host_user.username)

    # 如果想显示多对多 在admin内 写如下函数即可
    def get_groups(self):
        #循环一遍这个表里面的内容     可以把每个组名拿出来显示成一行
        return ','.join([g.name for g in self.host_groups.select_related()])  #以逗号分割，将循环出来的g，取g.name   用法则在admin内写上get_groups

class TaskLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)  #开始时间
    end_time = models.DateTimeField(null=True,blank=True)  #结束时间
    task_type_choices = (('multi_cmd',"CMD"),('file_send',"批量发送文件"),('file_get',"批量下载文件")) #任务类型选择
    task_type = models.CharField(choices=task_type_choices,max_length=50)#任务类型
    user = models.ForeignKey('UserProfile') #执行用户
    hosts = models.ManyToManyField('BindHostToUser')#主机
    cmd = models.TextField() #命令字段
    expire_time = models.IntegerField(default=30)#过期时间
    task_pid = models.IntegerField(default=0) #任务的Python后端借口的程序的pid  例如我shudown100台主机，可能关机过程需要2三分钟，你后台最大并发是10台进行，这样你在刚关机，第一波进程执行时候你可以制止，所以你要杀掉pid 即可
    note = models.CharField(max_length=100,blank=True,null=True) # 备注
    def __unicode__(self):
        '''object. __unicode__ ( self )
            Called to implement unicode() built-in; should return a Unicode object. When this method is not defined, string conversion is attempted, and the result of string conversion is converted to Unicode using the system default encoding.

            【译文】实现unicode()内嵌函数；应该返回Unicode对象。当没有定义这个方法时，取而代之的是string转换，转换的结果是用系统默认编码转化为Unicode。'''
        return "taskid:%s cmd:%s" %(self.id,self.cmd)
    class Meta:
        verbose_name = u'批量任务'
        verbose_name_plural = u'批量任务'

class TaskLogDetail(models.Model):  #这个是存取任务返回的结果
    child_of_task = models.ForeignKey('TaskLog') #外键记录跟子任务的关系
    bind_host  = models.ForeignKey('BindHostToUser') #绑定主机
    date = models.DateTimeField(auto_now_add=True) #finished date
    event_log = models.TextField() #输出log记录
    result_choices= (('success','Success'),('failed','Failed'),('unknown','Unknown'))  #结果返回的状态
    result = models.CharField(choices=result_choices,max_length=30,default='unknown')#返回的结果，可能有两种状态，执行了，可能成功可能失败，  没有执行即失败
    note = models.CharField(max_length=100,blank=True)

    def __unicode__(self):
        return "child of:%s result:%s" %(self.child_of_task.id, self.result)
    class Meta:
        verbose_name = u'批量任务日志'
        verbose_name_plural = u'批量任务日志'

        # 建完表 执行 Python manage.py makemigrations    Python manage.py migrate   python managy.py syncdb