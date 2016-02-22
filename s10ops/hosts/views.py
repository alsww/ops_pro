#coding:utf-8_

from django.shortcuts import render
from django.shortcuts import HttpResponse,HttpResponseRedirect

from django.contrib.auth import authenticate,login,logout #用户登录信息验证

from django.views.decorators.csrf import csrf_exempt # 制定函数豁免 csrf  也就是个免除csrf的装饰圈

from django.contrib.auth.decorators import login_required  #登录装饰器验证 未验证用户则跳转到登录界面
import models,task,json #序列化到前端字典
import utils #  在 view中dump  get--result时候调用了utils函数判断时间。如果穿的对象 obj 是一个 isoformat  也就是日期格式。 我就转换成字符串 如下 返回

# Create your views here.
@login_required  #登录装饰器，如果未登录就会跳转到登录界面
def index(request):
    return render(request,'index.html')
@login_required #登录装饰器，如果未登录就会跳转到登录界面
def hosts_index(request):
    return render(request,'hosts/dashboard.html')

@login_required #登录装饰器，如果未登录就会跳转到登录界面
def assets_index(request):
    return render(request,'assets/dashboard.html')

@login_required##登录装饰器，如果未登录就会跳转到登录界面
def monitor_index(request):
    return render(request,'monitor/dashboard.html')


@login_required#登录装饰器，如果未登录就会跳转到登录界面
def acc_logout(request):
    logout(request)
    return  HttpResponseRedirect("/")

def acc_login(request):  #登录装饰器，如果未登录就会跳转到登录界面
    login_err = ''  #赋值前端登录错提示的空字典

    if request.method == 'POST':  #判断前端是否是post提交
        username= request.POST.get('email')  #获取前端post提交的input的name值 并赋值
        password= request.POST.get('password') #获取前端post提交的input的name值 并赋值
        user = authenticate(username=username,password=password)  #调用django的authenticate方法来验证用户的正确与否

        if user is not None:  #如果上面的验证变量不为空 该用户正确
            login(request,user)  #登录该用户

            return HttpResponseRedirect('/') #跳转到主页

        else:
            login_err = "Wrong username or password!" #赋值错误提示
    return  render(request,'login.html', {'login_err':login_err}) #前端返回内容

@login_required
def host_mgr(request):
    selected_gid = request.GET.get('selected_gid')  #三级右侧内容不用ajax 用 selectgid 局部刷新   这里赋值变量
    if selected_gid:  #如果存在
        host_list = models.BindHostToUser.objects.filter(host_groups__id =selected_gid)   # 过滤 通过bindhosttouser这个表 查host_groups的id
    else: #否则
       host_list = request.user.bind_hosts.select_related() #查询
    return render(request,"hosts/host_mgr.html",{'host_list':host_list}) #返回


@login_required
def multi_cmd(request):
    return render(request,"hosts/multi_cmd.html")

@login_required
def submit_task(request):
    print request.POST #打印测试
    tas_obj = task.Task(request)# 传给request到函数  下周讲django起并发任务
    res = tas_obj.handle()  #task中处理多命令数据是一个字典返回的return的
    #上面返回了一个字典 返回到前端需要 json序列化一下
    return HttpResponse(json.dumps(res))#json序列化一下


@login_required
def gettaskresult(request):

    task_obj = task.Task(request)  #传过来的request

    res = task_obj.get_task_result() # 调用 taks脚本Task类的get。。 方法

    print '--res--task--',res  #打印 测试
    print 'aaaaaaaaaaaa'
    #return HttpResponse('task_obj')
    return HttpResponse(json.dumps(res,default=utils.json_date_handler)) #  在 view中dump  get——result时候调用了utils函数判断时间。如果穿的对象 obj 是一个 isoformat  也就是日期格式。 我就转换成字符串 如下 返回

@login_required
def multi_file_transfer(request):
    return render(request,"hosts/multi_file_transfer.html")


@csrf_exempt  # 豁免csrf的装饰圈   django的全局注入，这是提交文件 时候跨站禁止，   可以全局加入csrf  但是提交文件不知道如何post。
@login_required
def file_upload(request):
    filename = request.FILES['filename']  #传文件从files取
    print '-->',request.POST
    file_path =utils.handle_upload_file(request,filename)

    return HttpResponse(json.dumps({'uploaded_file_path':file_path}))  #将这个字典传到后端，作为前端的全局变量先存储下来