#coding:utf-8

import os,random
from  s10ops import settings   #调用设置的 文件上传目录

def json_date_handler(obj):
    if hasattr(obj, 'isoformat'):  #  �� view函数中数据dump  get����resultʱ������˸ú����ж�ʱ�䡣������Ķ��� obj 中有没有 isoformat  Ҳ�������ڸ�ʽ�� �Ҿ�ת�����ַ��� ���� ����
        return obj.strftime("%Y-%m-%d %H:%M:%S")


def handle_upload_file(request,file_obj):
    random_dir = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba1234567890',10))#创建随机目录。

    upload_dir = '%s/%s' %(settings.FileUploadDir,request.user.id)
    upload_dir2 = '%s/%s' %(upload_dir,random_dir)
    if not os.path.isdir(upload_dir): #如果路径不存在。创建文件  windows是md 输入命令“md c:\text”创建文件夹
        os.mkdir(upload_dir)
    if not os.path.isdir(upload_dir2):
        os.mkdir(upload_dir2)
    #for循环会一个文件一个目录

    with open('%s/%s' %(upload_dir2,file_obj.name),'wb') as destination :
    #with open('%s/%s' %(upload_dir,file_obj.name),'wb') as destination :
        for chunk in file_obj.chunks():
            destination.write(chunk)

    return  "%s/%s" %(random_dir,file_obj.name) #此处返回目录 跟文件名