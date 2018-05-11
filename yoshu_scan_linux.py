#!/usr/bin/env python
# -*- coding: utf8 -*-
import os,subprocess,socket,time,sys,json,urllib2,redis,requests
from socket import gethostname
from sys import argv

#钉钉机器人webhook变量
WebHook="https://oapi.dingtalk.com/robot/send?access_token=517267414dd5acbee6cc972d841d55436ef49333956613735015fcdc4772aeb1"

#处理消息
def do_message(context):
        message = {
                "msgtype":"text",
                "text":{
                        "content":context
                }
        }
        return message
#调用发送消息
def send_reques(text):
        #context = get_message()
        message = do_message(text)
        json_dump = json.dumps(message)
        req_con = urllib2.Request(WebHook,json_dump)
        req_con.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req_con)

#读有数的site文档
def yoshu():
    ip_names = {}
    with open("yoshu_site.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            obj = line.split(",")
            ip_names[obj[1].split("\r\n")[0]]=obj[0]
    return ip_names

#redis连接
def get_serverinfo():
    r = redis.StrictRedis(host='r-uf6e0da4fcd9b7f4.redis.rds.aliyuncs.com', port = 6379, password ='FGmtS5XFaSouBOzV', db = 12)
    redis_key = r.mget("reSer")
    job_key=json.loads(redis_key[0])
    server_list=job_key['Value'].values()
    iplist=yoshu()
   
    new_server_list = []
    for v in server_list:
         redis_name = (v['ServiceName'])
         company_name=redis_name.split("_")[0]
         v['Ip']=iplist[company_name]
         redis_ip = (v['Ip'])
         redis_port = (v['Port'] + 100)
         new_server_list.append({"RedisName":redis_name,"RedisIp":redis_ip,"RedisPort":redis_port})
         with open("redis_ip.txt", 'w') as f:
             f.write(str(new_server_list).encode("utf-8") + '\r\n')
    return new_server_list
def get_servers():
    serverInfo = get_serverinfo()
    serverLinks=[]
    servers=[]
    for info in serverInfo:
        server={}
        server["_each_port"] = info["RedisPort"]
        server["_each_ip"] = info["RedisIp"]
        server["_each_name"] = info["RedisName"]
        link = "http://%s:%s" % (server["_each_ip"], server["_each_port"])
        server["_link"]=link
        if(link  not in  serverLinks):
            serverLinks.append(link)
            servers.append(server)
    return servers

#端口检测
def check_port():
    for info in get_servers():
        _each_port = info["_each_port"]
        _each_ip = info["_each_ip"]
        _each_name = info["_each_name"]
        link = info["_link"]
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            r = requests.get(link, timeout=1, allow_redirects=False)
            r.raise_for_status() # 如果响应状态码不是 200，就主动抛出异常
            r.close()            
            tt = "check port success!"
            logfile = "yoshu_success.log"
            f = open(logfile,'a+')
            f.write(now + " " + str(_each_ip) + " " + str(_each_port) + " " + tt + "\n")
            f.close()
        except Exception as e:
            message = "ServiceName: %s \n Ip: %s \n Port: %s \n Error:%s \n Time: %s"   % (_each_name, _each_ip, _each_port,e.message, now)
            send_reques(message)

if __name__ == '__main__':
    while True:       
        check_port()
        time.sleep(3600) 
