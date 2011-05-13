#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Robot for happyfarm
    Util for renren.com
    Copyright (C) 2009, bin.c.chen@gmail.com

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""

__author__ = "alex (bin.c.chen@gmail.com)"
__version__ = "Revision: 1.02.247"
__date__ = "$Date: 2009/08/07 14:50:59 $"
__copyright__ = "Copyright (c) 2009 Alex"
__license__ = "Python"


import sys, traceback
from sgmllib import SGMLParser
# from BaseHTMLProcessor import BaseHTMLProcessor

import urllib,urllib2,cookielib,time
import StringIO,sys,hashlib
import gzip
import json
from pprint import pprint
from getpass import getpass

import logging
import logging.config

import ConfigParser
import AdvancedConfigParser
import string, os, types
import datetime
import random
import re

from conf import *

# cf = ConfigParser.ConfigParser()
cf = AdvancedConfigParser.AdvancedRawConfigParser()
cf.read(config.conf_file)

logging.config.fileConfig(config.logging_file)
#create logger
logger = logging.getLogger("MSG")

debug_file = open("debug.txt", "a")
DEBUG = True
MSG_HDR_LEN = 30
SCREEN_LEN = 79

false = 0
true = 1

# init params
always_steal    = cf.getint('actions', 'alwaysSteal')
auto_water      = cf.getint('actions', 'auto_water')
auto_clear_weed = cf.getint('actions', 'auto_clear_weed')
auto_spraying   = cf.getint('actions', 'auto_spraying')
auto_planting   = cf.getint('actions', 'auto_planting')
auto_fertilize  = cf.getint('actions', 'auto_fertilize')
show_friends_list   = cf.getint('actions', 'show_friends_list')


max_delay_time = cf.getint('params', 'max_delay_time')
random_lower = cf.getint('params', 'random_lower')
random_upper = cf.getint('params', 'random_upper')
fertilize_lower_time = cf.getint('params', 'fertilize_lower_time')
fertilize_upper_time = cf.getint('params', 'fertilize_upper_time')
seed_CID             = cf.getint('params', 'seed_CID')

md5_seed             = cf.get("params", "pm_md5_seed")

class HFLoginURL(SGMLParser):

    def reset(self):
        SGMLParser.reset(self)
        self.url = ''

    def start_iframe(self, attrs):
        # pprint(attrs)
        if attrs[0][1] == "iframe_canvas":
            for item in attrs:
                if item[0] == 'src':
                    self.url = item[1]
                    # print self.url
                    break

class UpdateInfo(SGMLParser):

    def reset(self):
        SGMLParser.reset(self)
        self.latesturl = ''
        self.latestVer = []

    def start_a(self, attrs):
        if attrs[0][0] == 'href':
            url = attrs[0][1].strip()
            if url[-3:] == 'zip':
                # "http://cid-9aba854c0d65d608.skydrive.live.com/self.aspx/.Public/HF^_ROBOT/HF^_ROBOT^_0.71^_Setup.zip"
                self.latesturl = url

                verReStr = "\^_(?P<latestVer>[\d\.]+)\^_"
                obj = re.compile(verReStr).search(self.latesturl)
                if obj:
       		        self.latestVer = obj.group("latestVer").split('.')
       		        # print self.latestVer

class BestSeed(object):
    def __init__(self):
        self.validMaxrateCID = 517
        self.earningMostmoneyCID = 518
        self.earningMostExpCID = 519

    def is_spec_cid(self,cId):
        if cId == self.validMaxrateCID or \
           cId == self.earningMostmoneyCID or \
           cId == self.earningMostExpCID:
               return True

        return False



class FriendLister(SGMLParser):

    def reset(self):
        SGMLParser.reset(self)
        self.fri = []

    def handle_comment(self, text):
        patten = 'var friends='
        n = text.find(patten)
        if n != -1:
            vars_in_text = text.split(';')
            for var in vars_in_text:
                s = var.find(patten)
                if s != -1:

                    friends = eval( var[s+len(patten):] )

                    for f in friends:
                        self.fri.append({'userId':str(f['id']),'userName':eval('u"""'+f['name']+'"""').encode('UTF-8')})
                    break


class HappyFarm(object):

    def __init__(self):
        self.header = {'User-Agent':'Mozilla/5.0 ','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'zh-cn,zh;q=0.5','Accept-Encoding':'gzip,deflate','Accept-Charset':'utf-8,gb2312;q=0.7,*;q=0.7','Keep-Alive':'300','Connection':'keep-alive'}

        self.login_timeout = { 'retry':int(cf.get('params','pm_login_retry')), 'pm':int(cf.get('params','pm_login_timeout')), 'txt':cf.get('info','txt_login_timeout') % ( cf.get('params','pm_login_timeout') ) }
        self.getweb_timeout = { 'pm':int(cf.get('params','pm_getweb_timeout')), 'txt':cf.get('info','txt_getweb_timeout') % ( cf.get('params','pm_getweb_timeout') ) }

        self.farmlandStatus = []

        self.host = {}
        self.friends = []
        self.person_hav_farm = []

        self.farm_url = ''
        self.parcel = {}
        self.ferts = {}

        self.cid = '6'
        self.ccid = []
        self.tid = '1'

        self.difftime = 0
        self.type = sys.getfilesystemencoding()

        # self.timezone = time.timezone

        self.harvest_wait_list = []
        self.seedinfo = {}
        self.sorted_seed_info = [] # cId, cLevel, exp/h, price/h

        self.dog = {}

        cookies = cookielib.CookieJar()

        if int(cf.get('httpproxy','proxy_enable')):
            # set proxy
            proxyserver = cf.get('httpproxy','proxy_host')+':'+cf.get('httpproxy','proxy_port')
            proxy = 'http://%s' % (proxyserver)
            opener = urllib2.build_opener( urllib2.ProxyHandler({'http':proxy}), urllib2.HTTPCookieProcessor(cookies) )
        else:
            opener = urllib2.build_opener( urllib2.HTTPCookieProcessor(cookies) )

        urllib2.install_opener(opener)
        # print opener.handlers

        self.releaseVer = []
        verReStr = "Revision: (?P<ver1>\d+)\.(?P<ver2>\d+)\.(?P<ver3>\d+)"
        obj = re.compile(verReStr).search(__version__)
        if obj:
            self.releaseVer = [ obj.group("ver1"), obj.group("ver2") ]
            # print self.releaseVer

    def farm_init(self):

        self.friends = []
        self.person_hav_farm = []

        ok = True
        is_ok= True
        i=0
#login
        while ok:
            if is_ok:
                auto_login = cf.getint('login', 'auto')
                if auto_login:
                    email = cf.get("login", "email")
                    password = cf.get("login", "password")
                else:
                    email = raw_input('请输入校内登录帐号 > '.decode('UTF-8').encode(self.type))
                    email = email.decode(self.type).encode('UTF-8')
                    password = getpass('password > ')
                    password = password.decode(self.type).encode('UTF-8')

                self.host['password'] = {'email' : email, 'password' : password}
                is_ok = False

            i+=1
            if i > self.login_timeout['retry'] :
                self.print_str(self.getweb_timeout['txt'])
                time.sleep(self.getweb_timeout['pm'])
                i = 0

            self.print_str( self.host['password']['email']+" 校内人人网登录中..." )
            url = 'http://passport.renren.com/PLogin.do?domain=renren.com'
            try:
                results = self.req(url, urllib.urlencode(self.host['password']))
            except:
                self.print_str(self.login_timeout['txt'])
                time.sleep(self.login_timeout['pm'])
                continue
            else:
                reID = re.compile(r'\"id\" : (?P<UID>\d+)')
                IDObj = reID.search(results)
                if IDObj:
                    UID = int(IDObj.group('UID'))
                    # s = "Usr ID is %d" %UID
                    # self.print_str(s)
                    if UID > 0:
                       self.print_str( "成功登录!" )
                    else:
                        self.print_str(self.login_timeout['txt'])
                        time.sleep(self.login_timeout['pm'])
                        continue
                else:
                    self.print_str(self.login_timeout['txt'])
                    time.sleep(self.login_timeout['pm'])
                    continue

                if not auto_login:
                   auto_login = 1
                   cf.set("login", "auto", auto_login)
                   cf.set("login", "email", email)
                   cf.set("login", "password", password)
                   cf.write(open(config.conf_file, "w"))
                   self.print_str( "成功设置为自动登录，详情请看:" )
                   self.print_str( config.conf_file )


#get self.farm_url
            url = 'http://apps.renren.com/happyfarm'
            try:
                results = self.req(url)
            except:
                self.print_str(self.login_timeout['txt'])
                time.sleep(self.login_timeout['pm'])
                continue

            parser = HFLoginURL()
            parser.feed(results)
            parser.close()

            # parser.url = "http://xn.hf.fminutes.com?xn_sig_in_iframe=1&amp;xn_sig_method=get&amp;xn_sig_time=1251418201650&amp;xn_sig_user=251389112&amp;xn_sig_expires=1251424800&amp;xn_sig_session_key=2.5e5db48cef04590accc7591da1a40bb6.3600.1251424800-251389112&amp;xn_sig_added=1&amp;xn_sig_api_key=540b23c85c5f474f91b0196a9cfea621&amp;xn_sig_app_id=23163"
            if not parser.url:
                self.print_str( '开心农场登录有误,请重新登录:' )
                is_ok = True
                continue

            if parser.url.find('com?xn')!=-1:
                parser.url = parser.url.replace('com?xn','com/?xn')
            self.farm_url = parser.url

#get self.friends
            url = 'http://friend.renren.com/myfriendlistx.do'
            try:
                results = self.req(url)
            except:
                self.print_str(self.login_timeout['txt'])
                time.sleep(self.login_timeout['pm'])
                continue

            parser = FriendLister()
            parser.feed(results)
            parser.close()
            if not parser.fri:
                self.print_str( '你没有好友或校内获取好友出错...' )

            else:
                self.friends = parser.fri # get friends


            ret = self.get_info(self.farm_url)
            if not ret:
                self.print_str(self.login_timeout['txt'])
                time.sleep(self.login_timeout['pm'])
                continue

            ok = False
            time.sleep(1)

#get self.header, self.difftime
    def get_info(self, url):

        try:
            r = urllib2.Request(url, None, self.header)
            result = urllib2.urlopen(r)

            self.print_obj(result.read(), "result.read()")
            # print url, result.info()

            self.header['Cookie'] = result.info().getheader('Set-Cookie').replace('path=/, ','').replace(' path=/','')

            farm_time = result.info().getheader('Date')  # Mon, 27 Jul 2009 03:08:31 GMT
            #print 'farm   time: \t', farm_time

            result.close()

            #print 'time   zone: \tGMT', -time.timezone/3600
            server_time = datetime.datetime( *time.strptime(farm_time, '%a, %d %b %Y %H:%M:%S GMT')[0:7] )
            #print 'server time: \t', server_time

            host_time = datetime.datetime( *time.localtime()[0:7] )
            #print 'host   time: \t', host_time

            delay = server_time - host_time
            # adjust to local time from Greenwich mean time
            self.difftime = delay.days*24*3600 + delay.seconds + delay.microseconds/1000000.0 - time.timezone
            # print 'delay: \t', delay
        except:
            return False


        return True

# get self.farmlandStatus by friends number, self.dog and add myself into friends list

    def farm_data(self,friNo=None, showNameList=False):
        """
        friNo: Field Number
        {u'a': 18,                        # seed index = cId
 u'b': 4,                                 # cropStatus
 u'f': 1,                         # number of grass
 u'g': 0,                         # number of pest
 u'h': 1,                         # 0 means thirsty, need water
 u'i': [1251008173],              # healthy
 u'j': 1,                         # plant season 2+1 = 3
 u'k': 0,                         # yield
 u'l': 0,                         # LSL for leavings
 u'm': 0,                         # leavings
 u'n': 2,                         # 0: stealed but cought by dog, 1: stealed, 2: not stealed yet
 u'o': 0,                         # fertilize
 u'p': {u'1251006913': [7],       # {u'1248862423': [1, 3] ...}, 1 mean pest, 2 mean grass, 3 mean thirsty
        u'1251007981': [2],
        u'1251008168': [6],
        u'1251011830': [2]},
 u'q': 1250781857,                # last ripe time
 u'r': 1251006913,                # ...?
 u's': 1,                         # big pest remaining blood
 u't': 1,                         # ...
 u'u': u'5'}],                    # big pest total blood


        """
        self.farmlandStatus = [] # init
        data = self.send_request(mod='user', friNo=friNo)

        if data.has_key('farmlandStatus'):
            self.farmlandStatus = data[u'farmlandStatus']

        if not friNo:
            self.host['uId'] = str(data['user']['uId'])
            self.host['userName'] = data['user']['userName'].encode('UTF-8')
            self.host['FB'] = int(data['user']['FB'])
            self.host['exp'] = int(data['user']['exp'])
            self.host['headPic'] = data['user']['headPic']
            self.host['money'] = int(data['user']['money'])
            self.host['rate'] = int(self.get_rate(self.host['exp']))
            self.print_obj(self.host, 'self.host')

            me = {'userId':self.host['uId'],'userName':self.host['userName']}

            if me not in self.friends:
                # add self.host to friends list
                self.friends.insert(0, me)
                now_exp = self.host['exp'] - self.host['rate']*(self.host['rate']+1)*100
                next_exp = (self.host['rate']+1) * 200

                global seed_CID
                if self.bestCID.is_spec_cid(seed_CID):
                    seed_CID = self.select_best_seed(seed_CID)
                self.plant_cId_list = [seed_CID, \
                                    self.select_best_seed(self.bestCID.validMaxrateCID), \
                                    self.select_best_seed(self.bestCID.earningMostmoneyCID), \
                                    self.select_best_seed(self.bestCID.earningMostExpCID)]

                print '-'*SCREEN_LEN

                s = '等级： %d    经验： %d/%d    现金： %d    F币： %d' \
                    %( self.host['rate'], now_exp, next_exp, self.host['money'], self.host['FB'] )
                self.print_str( s )

                s = '用户自定义种子：【%s】 | 可用最大等级种子：【%s】' \
                    %(self.seedinfo[self.plant_cId_list[0]]['cName'], self.seedinfo[self.plant_cId_list[1]]['cName'])
                self.print_str( s )

                s = '最赚现金的种子：【%s】 | 最赚经验的种子：  【%s】' \
                    %(self.seedinfo[self.plant_cId_list[2]]['cName'], self.seedinfo[self.plant_cId_list[3]]['cName'])
                self.print_str( s )

                print '-'*SCREEN_LEN

                if auto_planting:
                    s = '%s 再次提醒：您当前选择的自动种植的种子为【%s】 %s' \
                        %('*'*3, self.seedinfo[self.plant_cId_list[0]]['cName'], '*'*3)
                    self.print_str( s )

                    print '-'*SCREEN_LEN

        self.dog = {}
        if data.has_key('dog'):
            self.dog = data['dog']

        f = {}
        for i in self.friends:
            if i['userId'] == friNo:
                f = i
                break

        # init person_hav_farm
        if f:
            if self.farmlandStatus:
                if f not in self.person_hav_farm:
                    self.person_hav_farm.append(f)
                    if showNameList:
                        s = '[%03d] %12d' %(len(self.person_hav_farm), int(f['userId']) )
                        self.print_str( s + ': ' + f['userName'] )
            else:
                if f in self.person_hav_farm:
                    s = '×× %12d: %s 无开心农场，从巡视名单中删除。 ××' %(int(f['userId']), f['userName'])
                    self.print_str( s )
                    self.person_hav_farm.remove(f)



    def send_request(self, mod='', act='', whoNo='', place=0, tId='', cId=0, num=0, rtype=3, friNo=None):

        i = 0
        data = []

        while True:
            i+=1
            if i > self.login_timeout['retry'] :
                self.print_str(self.getweb_timeout['txt'])
                time.sleep(self.getweb_timeout['pm'])
                i = 0
            md5 = hashlib.md5()
            farmTime = str(int(time.time())+self.difftime)
            md5.update(farmTime+md5_seed)
            farmKey = md5.hexdigest()

            if mod:
                url = 'http://xn.hf.fminutes.com/api.php?mod='+mod
                url = url + '&act='+act+'&farmKey='+farmKey+'&farmTime='+farmTime+'&inuId='
                if mod == 'farmlandstatus':
                    # harvest, scounge, water, clear_weed, spraying, scarify, fertilize, planting
                    if act in ['planting']:
                        url = url + '&cId='+str(cId)
                        url = url + '&ownerId='+whoNo
                        url = url + '&place='+str(place)
                    else:
                        url = url + '&ownerId='+whoNo
                        url = url + '&place='+str(place)
                        url = url + '&tId='+tId

                elif mod == 'shop':

                    if act in ['buy']:
                        if rtype == 1:
                           url = url + '&id=' + str(cId) + '&number=' + str(num) + '&type=' + str(rtype)
                        elif rtype == 3:
                           url = url + '&id=' + tId + '&number=' + str(num) + '&type=' + str(rtype)
                        else:
                            self.print_str('url 不支持！' )

                    else:
                        # get_decoration_info, get_tool_info, get_dog_info, get_seed_info
                        url = url + '&type=' + str(rtype)

                elif mod == 'Package':
                    # get_package_info
                    pass

                elif mod == 'user':
                    # farm_data
                    if friNo:
                        url = 'http://xn.hf.fminutes.com/api.php?mod=user&act=run&flag=1&farmKey='+farmKey+'&farmTime='+farmTime+'&inuId='+'&ownerId='+friNo
                    else:
                        url = 'http://xn.hf.fminutes.com/api.php?mod=user&act=run&farmKey='+farmKey+'&farmTime='+farmTime+'&inuId='

                elif mod == 'repertory':
                    # getUserSeed, get_user_crop, sale_all
                    pass

                else:
                    self.print_str('url 出错!' )
            else:
                self.print_str('url 出错!' )

            try:
                data = self.req(url)
            except:
                self.print_str(self.login_timeout['txt'])
#                result.close
                time.sleep(self.login_timeout['pm'])
                continue

            if type(data) == types.DictType:
                if not data.has_key('direction'):
                    data['direction'] = u''
                data['direction'] = data['direction'].encode('UTF-8')

            # if type(data) == types.DictType and data.has_key('direction') and data['direction'] == u'你们已经不是好友了。'.encode('UTF-8'):
            #     self.print_str( '.'*MSG_HDR_LEN + '确认是否仍为好友，重启ROBOT... ' )
            #     HappyFarm().robot()
            if type(data) == types.DictType and data.has_key('errorContent') and data['errorContent'] != u'': # and data['errorContent'] == u'请重新登录(code 101)'
                self.print_str( '.'*MSG_HDR_LEN + '出错，重启ROBOT... ' )
                HappyFarm().robot()

            return data

    def req(self, url, data=None):

        r = urllib2.Request(url, data, self.header)

        u = urllib2.urlopen(r)
        results = u.read()
        # print url, ': \n', u.info()
        u.close()
        try:
            results = gzip.GzipFile(fileobj=StringIO.StringIO(results)).read()
        except:
            results = results

        try:
            results = json.loads(results)
        except:
            results = results

        self.print_obj(results, url)

        return results

    def harvest(self,x,place):
        '''
        {u'code': 1,
         u'direction': u'',
         u'exp': u'37',
         u'farmlandIndex': 6,
         u'harvest': 31,
         u'levelUp': False,
         u'poptype': 4,
         u'status': {u'action': [],
                     u'cId': 10,
                     u'cropStatus': 4,
                     u'fertilize': 0,
                     u'harvestTimes': 1,
                     u'health': 100,
                     u'humidity': 1,
                     u'leavings': 0,
                     u'min': 0,
                     u'mph': 0,
                     u'nph': 0,
                     u'oldhumidity': 1,
                     u'oldpest': 0,
                     u'oldweed': 0,
                     u'output': 0,
                     u'pId': 0,
                     u'pest': 0,
                     u'plantTime': 1248905623,
                     u'thief': [],
                     u'updateTime': 1249002823,
                     u'weed': 0}}
        '''
        s = '到 %s 的第 %02d 块地【收】第 %02d 季菜: %s ...  ' \
            %(x['userName'], place+1, x['j']+1, self.seedinfo[x[u'a']]['cName'])
        self.print_str( s )
        whoNo = x['userId']
        data = self.send_request(mod='farmlandstatus', act='harvest', whoNo=whoNo, place=place)
        if data['code']:
            # {"farmlandIndex":1,"code":1,"poptype":4,"direction":"","harvest":1,"status":{"cId":6,"cropStatus":6,"oldweed":0,"oldpest":0,"oldhumidity":1,"weed":0,"pest":0,"humidity":1,"health":100,"harvestTimes":0,"output":41,"min":24,"leavings":40,"thief":{"251389112":1},"fertilize":0,"action":[],"plantTime":1248830404,"updateTime":1248939064,"pId":0,"nph":0,"mph":0}}'
            if data['direction']:
                self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
            else:
                s = '收获 %02s 个！' %(data['harvest'])
                self.print_str( '.'*MSG_HDR_LEN + s )

            if auto_planting and ( x['j']+1 == int(self.seedinfo[x['a']]['maturingTime']) ):
               self.planting(x, place, seed_CID)
        else:
            # '{"farmlandIndex":1,"code":0,"poptype":1,"direction":"\u8fd9\u5757\u5730\u6ca1\u4e1c\u897f\u53ef\u6536\u83b7\uff01","harvest":0}'
            if data['direction']:
                self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
            else:
                self.print_str( '.'*MSG_HDR_LEN + '摘果失败！' )


    def scrounge(self,x,place):

        s = '到 %s 的第 %02d 块地【偷】第 %02d 季菜: %s ...  ' \
            %(x['userName'], place+1, x['j']+1, self.seedinfo[x[u'a']]['cName'])
        self.print_str( s )
        whoNo = x['userId']

        retry = 0
        while True:
            data = self.send_request(mod='farmlandstatus', act='scrounge', whoNo=whoNo, place=place)
            retry += 1
            if retry > 3 or data['direction'] != u'这块地没东西可采摘的！'.encode('UTF-8'):
                break
            else:
                time.sleep(1)

        if data['code']:
            # {"farmlandIndex":1,"code":1,"poptype":4,"direction":"","harvest":1,"status":{"cId":6,"cropStatus":6,"oldweed":0,"oldpest":0,"oldhumidity":1,"weed":0,"pest":0,"humidity":1,"health":100,"harvestTimes":0,"output":41,"min":24,"leavings":40,"thief":{"251389112":1},"fertilize":0,"action":[],"plantTime":1248830404,"updateTime":1248939064,"pId":0,"nph":0,"mph":0}}'
            if data['direction']:
                self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
            else:
                s = '偷到 %02s 个！' %(data['harvest'])
                self.print_str( '.'*MSG_HDR_LEN + s )
        else:
            # '{"farmlandIndex":1,"code":0,"poptype":1,"direction":"\u8fd9\u5757\u5730\u6ca1\u4e1c\u897f\u53ef\u6536\u83b7\uff01","harvest":0}'
            if data['direction']:
                self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
            else:
                self.print_str( '.'*MSG_HDR_LEN + '偷取失败！' )


    def water(self,x,place):
        '''
        {u'code': 1,
         u'direction': u'\u8c22\u8c22\u5e2e\u5fd9\uff0c\u4f60\u771f\u662f\u4e2a\u597d\u4eba\uff01',
         u'exp': 2,
         u'farmlandIndex': 4,
         u'humidity': 1,
         u'levelUp': False,
         u'money': 1,
         u'mph': 0,
         u'nph': 0,
         u'pId': 0,
         u'pest': 0,
         u'poptype': 1,
         u'tId': 0,
         u'weed': 1}
        '''

        s = '到 %s 的第 %02d 块地【浇水】...  ' \
            %(x['userName'], place+1, )
        self.print_str( s )
        whoNo = x['userId']
        data = self.send_request(mod='farmlandstatus', act='water', whoNo=whoNo, place=place)
        if data['code']:
            if data['direction']:
                self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
            else:
                self.print_str( '.'*MSG_HDR_LEN + '浇水成功！' )
        else:
            if data['direction']:
                self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
            else:
                self.print_str( '.'*MSG_HDR_LEN + '浇水失败！' )

    def clear_weed(self,x,place):
        '''
        {u'code': 1,
         u'direction': u'\u8c22\u8c22\u4f60\uff0c\u6742\u8349\u6e05\u9664\u5e72\u51c0\u4e86\uff01',
         u'exp': 2,
         u'farmlandIndex': 1,
         u'humidity': 1,
         u'levelUp': False,
         u'money': 1,
         u'mph': 0,
         u'nph': 0,
         u'pId': 0,
         u'pest': 0,
         u'poptype': 1,
         u'tId': 0,
         u'weed': 0}
        '''

        s = '到 %s 的第 %02d 块地【除草】...  ' \
            %(x['userName'], place+1, )
        self.print_str( s )
        whoNo = x['userId']
        while True:
            data = self.send_request(mod='farmlandstatus', act='clearWeed', whoNo=whoNo, place=place)
            if data['code']:
                if data['weed'] == 0:
                    if data['direction']:
                        self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                    else:
                        self.print_str( '.'*MSG_HDR_LEN + '除草成功！' )
                    break
            else:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '除草失败！' )
                break


    def spraying(self,x,place, tId='0'):
        '''
        {u'code': 0,
         u'direction': u'\u8fd9\u4e2a\u9053\u5177\u6bcf\u5c0f\u65f6\u53ea\u80fd\u7528\u4e00\u6b21\u3002',
         u'farmlandIndex': 0,
         u'humidity': 1,
         u'mph': u'5',
         u'nph': 3,
         u'pId': 1,
         u'pest': 0,
         u'poptype': 1,
         u'tId': 0,
         u'weed': 0}
        '''

        s = '到 %s 的第 %02d 块地【除虫】...  ' \
            %(x['userName'], place+1, )
        self.print_str( s )
        whoNo = x['userId']
        while True:
            data = self.send_request(mod='farmlandstatus', act='spraying', whoNo=whoNo, place=place)
            if data['code']:
                if data['pest']==0 and int(data['mph'])==0:
                    if data['direction']:
                        self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                    else:
                        self.print_str( '.'*MSG_HDR_LEN + '杀虫成功！' )
                    break
            else:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '杀虫失败！' )

                break



    def scarify(self,x,place):
        '''
        {u'code': 1,
         u'direction': u'',
         u'exp': 3,
         u'farmlandIndex': 1,
         u'levelUp': False}
        '''
        s = '到 %s 的第 %02d 块地【翻地】...  ' \
            %(x['userName'], place+1, )
        self.print_str( s )
        whoNo = x['userId']
        while True:
            data = self.send_request(mod='farmlandstatus', act='scarify', whoNo=whoNo, place=place)
            if data['code']:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '翻地成功！' )
                break
            else:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                    if data['direction'] == u'已经锄过这块地了哟！'.encode('UTF-8'): #
                        break
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '翻地失败！' )


    def fertilize(self,x,place,tId='1'):
        '''
        {u'code': 1,
         u'farmlandIndex': 6,
         u'status': {u'action': [],
                     u'cId': 10,
                     u'cropStatus': 6,
                     u'fertilize': 5,
                     u'harvestTimes': 0,
                     u'health': 100,
                     u'humidity': 1,
                     u'leavings': 31,
                     u'min': 18,
                     u'mph': 0,
                     u'nph': 0,
                     u'oldhumidity': 1,
                     u'oldpest': 0,
                     u'oldweed': 0,
                     u'output': 31,
                     u'pId': 0,
                     u'pest': 0,
                     u'plantTime': 1248840817,
                     u'thief': [],
                     u'updateTime': 1248998960,
                     u'weed': 0},
         u'tId': 1}
         '''
        s= '到 %s 的第 %02d 块地【施肥】' \
            %( x['userName'], place+1 )
        self.print_str( s )
        whoNo = x['userId']
        if self.parcel.has_key('tId'+tId) and self.parcel['tId'+tId]['amount']:
            data = self.send_request(mod='farmlandstatus', act='fertilize', whoNo=whoNo, place=place, tId=tId)
            if data['code']:
                self.print_str( '.'*MSG_HDR_LEN + '施肥成功！' )
                self.get_package_info()
                return True
            else:
                self.print_str( '.'*MSG_HDR_LEN + '施肥失败！' )
        else:
            ret = self.buy_fertilizer(tId)
            if ret:
               return self.fertilize(x,place,tId='1')

        return False

    def get_rate(self, myexp):
        '''
        calculate user rate
        '''
        for rate in range(1,100):
            exp = rate * (rate+1) * 100
            if myexp < exp:
                break
        return rate-1


    def select_best_seed(self, index=518):
        '''
        select best seed
        '''
        best_seed_cId = 2 # 白萝卜

        if index == self.bestCID.validMaxrateCID:
            # self.print_str( '选择可用最大等级的种子...' )
            self.sorted_seed_info.sort( key = lambda l: [ l[1] ], reverse = True )
            self.print_obj(self.sorted_seed_info,'get_max_rate_seed')
            for item in self.sorted_seed_info:
                if self.host['rate'] >= item[1]:
                    best_seed_cId = item[0]
                    s = '等级：%d' %(best_seed_cId)
                    break



        if index == self.bestCID.earningMostmoneyCID:
            # self.print_str( '选择最赚现金的种子...' )
            self.sorted_seed_info.sort( key = lambda l: [ l[3], l[1] ], reverse = True )
            self.print_obj(self.sorted_seed_info,'getprice_per_hour')
            for item in self.sorted_seed_info:
                if self.host['rate'] >= item[1]:
                    best_seed_cId = item[0]
                    s = '＄%06.2f/小时' %(item[2])
                    break



        if index == self.bestCID.earningMostExpCID:
            # self.print_str( '选择最赚经验的种子...' )
            self.sorted_seed_info.sort( key = lambda l: [ l[2], l[1] ], reverse = True )
            self.print_obj(self.sorted_seed_info,'getexp_per_hour')
            for item in self.sorted_seed_info:
                if self.host['rate'] >= item[1]:
                    best_seed_cId = item[0]
                    s = 'EXP %06.2f/小时' %(item[2])
                    break




        return best_seed_cId

    def buy_seed(self,cId=2,num=1):
        '''
        {u'cId': 10,
         u'cName': u'\u5357\u74dc',
         u'code': 1,
         u'direction': u'',
         u'money': -1260,
         u'num': 1}
        '''

        s = '购买【%s】 %02d 个' \
            %(self.seedinfo[cId]['cName'], num, )
        self.print_str( s )
        if self.host['money'] >= int(self.seedinfo[cId]['price']) * num:
            data = self.send_request(mod='shop', act='buy', cId=cId, num=num, rtype=1)
            if data['code']:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '买种成功！' )
                self.get_package_info()
                return True
            else:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '买种失败！' )
        else:
            self.print_str( '.'*MSG_HDR_LEN + '无钱买种！' )
        return False

    def planting(self,x,place,cId=100):
        '''
        {u'cId': 10,
         u'code': 1,
         u'direction': u'',
         u'exp': 2,
         u'farmlandIndex': 1,
         u'levelUp': False,
         u'poptype': 0}
        '''
        s = '在 %s 的第 %02d 块地【种菜】: %s' \
            %(x['userName'], place+1, self.seedinfo[cId]['cName'])
        self.print_str( s )
        whoNo = x['userId']

        if self.parcel.has_key('cId'+str(cId)) and self.parcel['cId'+str(cId)]['amount']:
            self.scarify(x,place)
            data = self.send_request(mod='farmlandstatus', act='planting', whoNo=whoNo, place=place, cId=cId)
            if data['code']:
                self.print_str( '.'*MSG_HDR_LEN + '种植成功！' )
                if auto_fertilize:
                   self.fertilize(x,place,tId='1')
                self.get_package_info()
                return True
            else:
                self.print_str( '.'*MSG_HDR_LEN + '种植失败！' )
        else:
            self.print_str( '.'*MSG_HDR_LEN + '需要买种！' )

            for cId in self.plant_cId_list:
                ret = self.buy_seed(cId=cId,num=1)
                if ret:
                    break
            if ret:
               return self.planting(x, place, cId)

        return False



    def buy_fertilizer(self,tId='1',num=10):

        s = '购买【%s】 %02d 个' \
            %(self.ferts[tId]['tName'], num, )
        self.print_str( s )

        if self.host['money'] >= int(self.ferts[tId]['list']['1']['price']) * num:
            data = self.send_request(mod='shop', act='buy', tId=tId, num=num, rtype=3)

            if data['code']:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '买肥成功！' )
                self.get_package_info()
                return True
            else:
                if data['direction']:
                    self.print_str( '.'*MSG_HDR_LEN + data['direction'] )
                else:
                    self.print_str( '.'*MSG_HDR_LEN + '买肥失败！' )
        else:
            self.print_str( '.'*MSG_HDR_LEN + '无钱买肥！' )

        return False


    def get_user_crop(self):
        """
        [{u'amount': 7, u'cId': 2, u'cName': u'\u767d\u841d\u535c', u'price': u'23'},
         {u'amount': 4, u'cId': 6, u'cName': u'\u8304\u5b50', u'price': u'32'},
         {u'amount': 7, u'cId': 7, u'cName': u'\u756a\u8304', u'price': u'35'},
         {u'amount': 5, u'cId': 11, u'cName': u'\u82f9\u679c', u'price': u'56'},
         {u'amount': 182, u'cId': 10, u'cName': u'\u5357\u74dc', u'price': u'52'},
         {u'amount': 1, u'cId': 19, u'cName': u'\u6a59\u5b50', u'price': u'81'}]
        """
        data = self.send_request(mod='repertory', act='getUserCrop')

    def get_decoration_info(self):
        """
        {u'2': [{u'FBPrice': u'23',
         u'itemDesc': u'\u54e5\u7279\u5f0f\u573a\u666f',
         u'itemId': u'51',
         u'itemName': u'\u6708\u8ff7\u9b45\u5f71',
         u'itemType': u'1',
         u'itemValidTime': u'2592000',
         u'price': u'23888',
         u'setId': u'10'},
        {u'FBPrice': u'16',
         u'itemDesc': u'\u54e5\u7279\u5f0f\u573a\u666f',
         u'itemId': u'52',
         u'itemName': u'\u5e7b\u591c\u4fe1\u4ef0',
         u'itemType': u'2',
         u'itemValidTime': u'2592000',
         u'price': u'15999',
         u'setId': u'10'},
         ...
        """
        data = self.send_request(mod='shop', act='getShopInfo', rtype=2)

    def get_dog_info(self):
        """
        {u'4': [{u'depict': u'\u72d7\u72d7\u53ef\u4ee5\u4fdd\u62a4\u4f60\u7684\u519c\u573a\uff0c\u9632\u6b62\u597d\u53cb\u4f7f\u574f\u54e6~\u8d2d\u4e70\u540c\u65f6\u8d60\u90013\u5305\u72d7\u7cae\u3002',
         u'effect': u'',
         u'list': {u'1': {u'FBPrice': u'9', u'price': u'0'}},
         u'tId': 1,
         u'tName': u'\u54c8\u58eb\u5947',
         u'type': 4},
        {u'depict': u'\u72d7\u72d7\u53ef\u4ee5\u4fdd\u62a4\u4f60\u7684\u519c\u573a\uff0c\u9632\u6b62\u597d\u53cb\u4f7f\u574f\u54e6~\u8d2d\u4e70\u540c\u65f6\u8d60\u900110\u5305\u72d7\u7cae\u3002',
         u'effect': u'',
         u'list': {u'1': {u'FBPrice': u'19', u'price': u'0'}},
         u'tId': 2,
         u'tName': u'\u9ec4\u91d1\u730e\u72ac',
         u'type': 4},
        {u'depict': u'\u72d7\u72d7\u53ef\u4ee5\u4fdd\u62a4\u4f60\u7684\u519c\u573a\uff0c\u9632\u6b62\u597d\u53cb\u4f7f\u574f\u54e6~\u8d2d\u4e70\u540c\u65f6\u8d60\u900110\u5305\u72d7\u7cae',
         u'effect': u'',
         u'list': {u'1': {u'FBPrice': u'29', u'price': u'0'}},
         u'tId': 3,
         u'tName': u'\u8d35\u5bbe\u72d7',
         u'type': 4}]}
        """
        data = self.send_request(mod='shop', act='getShopInfo', rtype=4)

    def get_tool_info(self):
        """
        {u'3': [{u'depict': u'\u6bcf\u4e2a\u9636\u6bb5\u53ea\u80fd\u4f7f\u7528\u4e00\u6b21\uff0c\u51cf\u5c11\u8be5\u9636\u6bb5\u6210\u957f\u65f6\u95f41\u5c0f\u65f6\u3002',
         u'effect': u'3600',
         u'list': {u'1': {u'FBPrice': 0, u'price': 50},
                   u'10': {u'FBPrice': 0, u'price': 450},
                   u'100': {u'FBPrice': 0, u'price': 4000}},
         u'tId': 1,
         u'tName': u'\u666e\u901a\u5316\u80a5',
         u'timeLimit': u'0',
         u'type': 3},

         ...
        """
        data = self.send_request(mod='shop', act='getShopInfo', rtype=3)
        for key in data:
            for t in data[key]:
                if t['type'] == 3:  # 化肥
                   t['tName'] = t['tName'].encode('UTF-8')
                   self.ferts[str(t['tId'])] = t

        self.print_obj( self.ferts, 'self.ferts' )

    def get_slack_time(self, t):
        slacktime = t - int(time.time())
        if slacktime < 0:
            slacktime = 0
        return slacktime

    def fert2ripe(self, wl):
        slacktime = self.get_slack_time(wl['harvest_time'])

        if slacktime <= fertilize_upper_time \
           and slacktime > fertilize_lower_time \
           and auto_fertilize \
           and wl['userId'] == self.host['uId']:
            ret = self.fertilize(wl,wl['fieldNo'],self.tid)
            if ret:
                self.harvest(wl, wl['fieldNo'])
                return True
        return False

    def sale_all(self):
        """

        """

        data = self.send_request(mod='repertory', act='saleAll')



# init self.seedinfo
    def get_seed_info(self):
        """
        {u'cId': 1,                      # seed index
         u'cLevel': u'10',               # 种植等级
         u'cName': u'\u8349\u8393',      # 草莓
         u'cType': u'1',                 #
         u'cropExp': u'41',              # 收获经验
         u'expect': 4788,                # 预计所得收入
         u'growthCycle': u'205200',      # 成熟时间
         u'maturingTime': u'3',          # 3 季
         u'output': u'21',               # 预计产量
         u'price': u'2237',              #
         u'sale': u'76'},                # 单个售价

         {u'1':
             [{u'cCharm': u'0',
             u'cId': 2,
             u'cLevel': u'0',
             u'cName': u'\u767d\u841d\u535c \u79cd\u5b50',
             u'cType': u'1',
             u'cropChr': u'0',
             u'cropExp': u'15',
             u'expect': 368,
             u'growthCycle': u'36000',
             u'maturingTime': u'1',
             u'output': u'16',
             u'price': u'167',
             u'sale': u'23'},
         """

        # 'http://xn.hf.fminutes.com/api.php?mod=repertory&act=getSeedInfo&farmKey='+farmKey+'&farmTime='+farmTime+'&inuId='
        # data = self.send_request(mod='repertory', act='getSeedInfo')
        data = self.send_request(mod='shop', act='getShopInfo', rtype=1)
        if data:
            for key in data:
                for x in data[key]:
                    self.seedinfo[x['cId']] = x
                    self.seedinfo[x['cId']][u'cName'] = self.seedinfo[x['cId']][u'cName'][:-3].encode('UTF-8')
                    # self.seedinfo[x['cId']][u'growthAgain'] = seedGrowthAgain[int(x['cId'])]

        # other color flower
        maxFlowerSeedID = 200
        for flowerCid in range(101,maxFlowerSeedID,4):
            if self.seedinfo.has_key(flowerCid):
                #delete all the color descriptions in orig flower
                self.seedinfo[flowerCid][u'cName'] = self.seedinfo[flowerCid][u'cName'][:-12]
                #build other color flowers info
                for Color in range(1,4):
                   otherColorFlowerCid = flowerCid + Color
                   self.seedinfo[otherColorFlowerCid] = {}
                   for k in self.seedinfo[flowerCid]:
                       self.seedinfo[otherColorFlowerCid][k] = self.seedinfo[flowerCid][k]
                   self.seedinfo[otherColorFlowerCid][u'cId'] = otherColorFlowerCid
            else:
                break

        self.print_obj(self.seedinfo, 'seedinfo')
        self.sorted_seed_info = [] # cId, cLevel, exp/h, price/h

        for i in self.seedinfo:
            if i < maxFlowerSeedID:
                expect_total_money = int(self.seedinfo[i]['expect'])
                price = int(self.seedinfo[i]['price'])
                maturing_time = int(self.seedinfo[i]['maturingTime'])
                exp = int(self.seedinfo[i]['cropExp'])
                growth_cycle = int(self.seedinfo[i]['growthCycle'])/3600.0

                money_per_hr = (expect_total_money - price) / ( growth_cycle*maturing_time )
                exp_per_hr = ( exp *maturing_time ) / ( growth_cycle*maturing_time )

                self.sorted_seed_info.append([int(self.seedinfo[i]['cId']), int(self.seedinfo[i]['cLevel']), exp_per_hr, money_per_hr])


# init self.parcel dict
# [{"type":3,"tId":1,"tName":"\u666e\u901a\u5316\u80a5" 普通化肥,"amount":97,"view":"1"}]
    def get_package_info(self):
        '''
        [{u'amount': 5, u'cId': 6, u'cName': u'\u8304\u5b50', u'type': 1, u'view': 1},
         {u'amount': 5, u'cId': 10, u'cName': u'\u5357\u74dc', u'type': 1, u'view': 1},
         {u'amount': 81,
          u'tId': 1,
          u'tName': u'\u666e\u901a\u5316\u80a5',
          u'type': 3,
          u'view': u'1'}]
        '''
        # 'http://xn.hf.fminutes.com/api.php?mod=repertory&act=getUserSeed&farmKey='+farmKey+'&farmTime='+farmTime+'&inuId='
        self.parcel = {}
        data = self.send_request(mod='Package', act='getPackageInfo')

        for key in data:
            for x in data[key]:
                if x.has_key('cId'):
                    self.parcel[('cId'+str(x['cId']))]=x

                elif x.has_key('tId'):
                    self.parcel[('tId'+str(x['tId']))] = x

    # dump into log, harvest_wait_list is also printed to sys.out
    def print_obj(self, obj, obj_name='', stream=debug_file, d=DEBUG):
        if d:
            pprint(str(datetime.datetime.now())+ ': ', stream)
            if obj_name:
               pprint('>'*MSG_HDR_LEN + obj_name + ': ', stream)
            pprint(obj, stream)
            pprint('-'*SCREEN_LEN, stream)

        if obj_name == 'harvest_wait_list':
            index = 0
            print '-'*SCREEN_LEN
            for item in obj:
                index = index + 1
                slacktime = self.get_slack_time(item['harvest_time'])
                wait_time = '%02d:%02d:%02d' %(slacktime/3600, (slacktime%3600)/60, slacktime%60 )
                s = '[%02d]:[%8s]第[%02d]块地第[%02d]季[%8s] [%s]后成熟' \
                    %(index, item['userName'], item['fieldNo']+1, item['j']+1, self.seedinfo[item[u'a']]['cName'], wait_time)
                self.print_str( s )
            print '-'*SCREEN_LEN

    # format print str to log and sys.out
    def print_str(self, string):
        # date = str(datetime.datetime.now())
        date = '[%04d.%02d.%02d %02d:%02d:%02d]' %(time.localtime(time.time())[0:6])
        try:
            print date+': '+string.decode('UTF-8').encode(self.type)
        except:
            print date+': '+string

        try:
            logger.info( string.decode('UTF-8').encode(self.type) )
        except:
            logger.info( string )

        pprint(date+': '+string, debug_file)


    def check_update_info(self):

        try:
            url = 'http://wahaha02.spaces.live.com'
            results = self.req(url)
            parser = UpdateInfo()
            parser.feed(results)
            parser.close()

            # compare version **.**
            if int(parser.latestVer[0]+parser.latestVer[1]) > int(self.releaseVer[0]+self.releaseVer[1]):
                print '*'*SCREEN_LEN
                s = "发现最新版本V%s.%s，请更新！(wahaha02.spaces.live.com)" %(parser.latestVer[0], parser.latestVer[1])
                self.print_str(s)
                print '*'*SCREEN_LEN

            # s = "当前版本V%s.%s为最新版本，无需更新！" %(self.releaseVer[0], self.releaseVer[1])
            # self.print_str(s)
            return parser.latestVer
        except:
            # s = "自动更新出错，请手动更新！"
            # self.print_str(s)
            return []

    def print_why_info(self):

        latestVer = self.check_update_info()

        print
        print "-"*SCREEN_LEN
        if latestVer == []:
            s = " Oops, PLEASE CHECK YOUR NETWORK CONDITIONS. "
            print s.center(SCREEN_LEN, '-').decode('UTF-8').encode(self.type)

        elif int(latestVer[0]+latestVer[1]) > int(self.releaseVer[0]+self.releaseVer[1]):
            s = " YOU ARE OUT, PLEASE USE LATEST VERSION:V%s.%s. " %(latestVer[0], latestVer[1])
            print s.center(SCREEN_LEN, '-').decode('UTF-8').encode(self.type)

        else:
            s = " Oops, PLEASE TRY AGAIN AND REPORT THIS FAILURE TO ME. "
            print s.center(SCREEN_LEN, '-').decode('UTF-8').encode(self.type)

        print "    http://wahaha02.spaces.live.com   ".center(SCREEN_LEN, '-')
        print "-"*SCREEN_LEN


    # for help to debug code when code fail, dump into both log and sys.out
    def print_debug_info(self, person, fieldNo, mlist):
        s= "FAIL TO HARVEST>> person: %s fNo: %d" %(person, fieldNo)
        self.print_obj(obj=mlist, obj_name=s)

# log in, get self.host, self.friends, self.person_hav_farm
    def init_robot(self):
        self.bestCID = BestSeed()
        # log in, init self.friends, self.person_hav_farm
        self.farm_init()

        # 种子
        self.get_seed_info()

        # 道具
        self.get_tool_info()

        # self.get_decoration_info()
        # self.get_dog_info()

        # init self.host, self.farmlandStatus, add me to self.person_hav_farm
        self.farm_data()

        # print
        if show_friends_list:
            # init self.person_hav_farm
            self.print_str( '搜索拥有HAPPYFARM的好友名单，请等待...' )
            for f in self.friends:
                self.farm_data(f['userId'],showNameList=True)
        else:
            for f in self.friends:
                self.person_hav_farm.append(f)


    def robot(self):

        self.check_update_info()
        self.init_robot()
        # self.buy_seed(cId=101,num=1)   # for test
        # self.buy_fertilizer(tId='1',num=10)

        while True:
            self.print_str( '信息同步中... ' )
            ret = self.get_info(self.farm_url)
            if not ret:
                self.print_str( '信息同步失败, 重启机器人... ' )
                HappyFarm().robot()

            # 已经购买的物品
            self.get_package_info()
            # 仓库
            self.get_user_crop()

            self.harvest_wait_list = [] # init

            for x in self.person_hav_farm:

                if x['userId'] == self.host['uId']:
                    self.print_str( '------------------------' )
                    self.print_str( '...只偷不种，照样致富...' )
                    self.print_str( '------------------------' )
                    continue

                self.farm_data(x['userId'])

                self.print_obj(self.farmlandStatus, 'farmlandStatus: '+x['userId'])

                if not self.farmlandStatus:
                    continue

                if x['userId'] != self.host['uId'] and self.dog['dogId'] and not always_steal:
                        s = '%s 养狗了,不偷!' %(x['userName'])
                        self.print_str( s )

                for k, v in enumerate(self.farmlandStatus):
                    v['userId'] = x['userId']
                    v['userName'] = x['userName']

                    if auto_planting and (x['userId'] == self.host['uId']) and (v['q'] == 0):
                        self.planting(v, k, seed_CID)
                        continue

                    if auto_water and v[u'h'] == 0:
                        self.water(x, k)

                    if auto_clear_weed and v[u'f'] > 0:
                        self.clear_weed(x, k)

                    if auto_spraying and (v[u'g'] > 0 or int(v[u'u']) > 0): # u'u':u'5'
                        self.spraying(x, k)

                    if x['userId'] != self.host['uId'] and self.dog['dogId'] and not always_steal:
                        continue

                    if not v[u'q']:
                        continue

                    if v[u'a'] == 2001: # 神秘玩具不偷
                        continue
#作物成熟时间

                    try:
                        growthCycle = int(self.seedinfo[v[u'a']][u'growthCycle'])
                    except:
                        self.print_obj( v[u'a'] , 'va')
                        continue

                    last_ripe_time = v[u'q']


                    harvest_time = last_ripe_time + growthCycle - self.difftime
                    slacktime = self.get_slack_time(harvest_time)
                    if slacktime > 0:
                        if slacktime < max_delay_time:
                        # if slacktime < 3600*10:
                           wl = { 'userId':x['userId'],'userName':x['userName'],'fieldNo':k,'cName':self.seedinfo[v[u'a']]['cName'],'harvest_time':harvest_time,'j':v[u'j'],'a':v[u'a']}
                           # if wait list is my fruit, it don't need to come into harvest_wait_list
                           # fertilize it to ripe right now
                           if self.fert2ripe(wl):
                              continue
                           self.harvest_wait_list.append(wl)
#收获
                    else:

                        try:
                            if x['userId'] == self.host['uId']:
                                self.harvest(v, k)
                            else:
                                has_stealed = false
                                if v['n'] == 2:
                                    has_stealed = false
                                else:
                                    has_stealed = true
                                if (not has_stealed) and ( int(v[u'm'])>int(v[u'l']) ): # could stealed
                                    self.scrounge(v, k)
                        except:
                            self.print_debug_info(v['userName'], k+1, v)
                            raise


            # enter wait_list
            # sort by harvest_time
            j = 1
            m = len(self.harvest_wait_list)
            while(j<m):
                for i in range(m-j):
                    if self.harvest_wait_list[i]['harvest_time']>self.harvest_wait_list[i+1]['harvest_time']:
                        temp = self.harvest_wait_list[i]
                        self.harvest_wait_list[i] = self.harvest_wait_list[i+1]
                        self.harvest_wait_list[i+1] = temp
                j+=1
# wait for harvesting
            minitor_window = '[%02d:%02d:%02d]' %(max_delay_time/3600, (max_delay_time%3600)/60, max_delay_time%60)
            s = '监控%s内成熟列表... ' \
                %(minitor_window )
            self.print_str( s )
            self.print_obj(self.harvest_wait_list, 'harvest_wait_list')

            self.check_update_info()

            if m == 0 or self.get_slack_time(self.harvest_wait_list[0]['harvest_time']) > max_delay_time:
                t = random.randrange(random_lower, random_upper)
                times = '< %04d分钟%02d秒 >' %(t/60, t%60)
                strAlarm = '[ %04d.%02d.%02d %02d:%02d:%02d ]' %(time.localtime(time.time()+t)[0:6])
                self.print_str( str(max_delay_time) + ' 秒内无果实成熟, 随机等待 ' + times )
                self.print_str( '到 ' + strAlarm + ' 时再开始巡视' )

                time.sleep(t)
                continue



            for wait_list in self.harvest_wait_list:
                t = self.get_slack_time(wait_list['harvest_time'])
                if t > max_delay_time:
                    break

                if t <= 0:
                    try:
                        if wait_list['userId'] == self.host['uId']:
                            self.harvest(wait_list, wait_list['fieldNo'])
                            continue
                        else:
                            self.scrounge(wait_list, wait_list['fieldNo'])
                            continue
                    except:
                        self.print_debug_info(wait_list['userName'], wait_list['fieldNo']+1, wait_list)
                        raise

                strAlarm = '[ %04d分钟%02d秒 ]' %(t/60, t%60)
                strAlarm = strAlarm + ' 即到 [ %04d.%02d.%02d %02d:%02d:%02d ] 时' %(time.localtime(wait_list['harvest_time'])[0:6])
                s = '等待 %s  ' %(strAlarm)
                self.print_str( s )
                s = '到 %s 的第 %02d 块地【查】第 %02d 季菜: %s ...' \
                    %(wait_list['userName'], wait_list['fieldNo']+1, wait_list['j']+1, self.seedinfo[wait_list[u'a']]['cName'])
                self.print_str( s )

                time.sleep(t)
                try:
                    if wait_list['userId'] == self.host['uId']:
                        self.harvest(wait_list, wait_list['fieldNo'])
                        continue
                    else:
                        self.scrounge(wait_list, wait_list['fieldNo'])
                        continue
                except:
                    self.print_debug_info(wait_list['userName'], wait_list['fieldNo']+1, wait_list)
                    raise




def main():

    while True:
        try:
            farm = HappyFarm()
            farm.robot()
        except KeyboardInterrupt:
            s = "Keyboard Interrupt!! Rerun HF_ROBOT."
            farm.print_str( s )
            traceback.print_exc(file=debug_file)
            logger.info( traceback.format_exc() )
            continue
        except:
            farm.print_why_info()
            traceback.print_exc(file=debug_file)
            logger.info( traceback.format_exc() )
            # raise
            break

    while True:
        pass


if __name__ == "__main__":
    try:
        os.system("color 0A")
        os.system("mode con cols=90 lines=3000")
    except:
        pass

    print '-'*SCREEN_LEN

    print "hf_robot %s ( %s ) on Win32" %(__version__, __date__)
    print "http://wahaha02.spaces.live.com"
    print
    print 'This program is distributed in the hope that it will be useful,'
    print 'but WITHOUT ANY WARRANTY; without even the implied warranty of'
    print 'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the'
    print 'GNU General Public License for more details.'

    print '-'*SCREEN_LEN
    print

    main()

