#!/usr/bin/env python
# coding:utf-8
# maclient!
# Contributor:
#      fffonion        <fffonion@gmail.com>
from __future__ import print_function
import math
import os
import os.path as opath
import re
import sys
import time
import locale
import base64
import datetime
from xml2dict import XML2Dict
from xml2dict import object_dict
import random
import threading
import traceback
from cross_platform import *
if PYTHON3:
    import configparser as ConfigParser
else:
    import ConfigParser
import maclient_player
import maclient_network
import maclient_logging
import maclient_smart
import maclient_plugin

__version__ = 1.72
# CONSTS:
EXPLORE_BATTLE, NORMAL_BATTLE, TAIL_BATTLE, WAKE_BATTLE = 0, 1, 2, 3
GACHA_FRIENNSHIP_POINT, GACHAgacha_TICKET, GACHA_11 = 1, 2, 4
EXPLORE_HAS_BOSS, EXPLORE_NO_FLOOR, EXPLORE_OK, EXPLORE_ERROR, EXPLORE_NO_AP = -2, -1, 0, 1, 2
BC_LIMIT_MAX, BC_LIMIT_CURRENT = -2, -1
HALF_TEA, FULL_TEA = 0, 1
GUILD_RACE_TYPE = ['11','12']
CMD_NOLOGIN = ['ss', 'set_server', 'l', 'login', 'rl', 'relogin']
#SERV_CN, SERV_CN2, SERV_TW = 'cn', 'cn2', 'tw'
# eval dicts
eval_fairy_select = [('LIMIT', 'time_limit'), ('NOT_BATTLED', 'fairy.not_battled'), ('.lv', '.fairy.lv'), ('IS_MINE', 'user.id == self.player.id'), ('IS_WAKE_RARE', 'wake_rare'), ('IS_WAKE', 'wake'),  ('IS_GUILD', "fairy.race_type in GUILD_RACE_TYPE"), ('0BC', 'put_down == "4"')]
eval_fairy_select_carddeck = [('IS_MINE', 'discoverer_id == self.player.id'), ('IS_WAKE_RARE', 'wake_rare'), ('IS_WAKE', 'wake'), ('LIMIT', 'time_limit'),  ('IS_GUILD', "race_type in GUILD_RACE_TYPE"), ('NOT_BATTLED', 'not_battled'),('fairy.hp%', 'float(fairy.hp)/float(fairy.hp_max)')]
eval_explore_area = [('IS_EVENT', "area_type=='1'"), ('IS_GUILD', "race_type in GUILD_RACE_TYPE"), ('IS_DAILY_EVENT', "id.startswith('5')"), ('NOT_FINNISHED', "prog_area!='100'")]
eval_explore_floor = [('NOT_FINNISHED', 'progress!="100"'), ('not floor.IS_GUILD', "(not area_race_type or area_race_type not in GUILD_RACE_TYPE)"),
('floor.IS_GUILD', "(not area_race_type or area_race_type in GUILD_RACE_TYPE)"),#little hack, 进入时area_race_type=0
('floor.HAS_FACTOR', '[floor.found_item_list.found_item[z] for z in range(len(floor.found_item_list.found_item)) if floor.found_item_list.found_item[z].type=="2"]')]
eval_select_card = [('atk', 'power'), ('mid', 'master_card_id'), ('price', 'sale_price'), ('sid', 'serial_id'), ('holo', 'holography==1')]

eval_task = []
#duowan = {'cn':'http://db.duowan.com/ma/cn/card/detail/%s.html', 'tw':'http://db.duowan.com/ma/card/detail/%s.html'}

if PYTHON3:
    setT = lambda strt : os.system(raw_du8('TITLE %s' % strt))
elif NICE_TERM:
    setT = lambda strt : print(raw_du8('[SET-TITLE]%s'%strt))
else:
    #if not PYTHON3:
    #    strt = strt.decode('utf-8').encode('cp936', 'ignore')
    if sys.platform == 'cli':
        import System.Console
        def setT(strt):
            System.Console.Title = strt
    else:
        setT = lambda strt : os.system(raw_du8('TITLE %s' % strt).encode(locale.getdefaultlocale()[1] or 'utf-8', 'replace'))

class set_title(threading.Thread):
    def __init__(self, macInstance):
        threading.Thread.__init__(self)
        self.macInstance = macInstance
        self.flag = 1
    def run(self):
        if not self.macInstance.settitle:
            self.flag = 0
       # if os.name == 'nt':
        while self.flag == 1:
            self.macInstance.player.calc_ap_bc()
            strt = '[%s] AP:%d/%d BC:%d/%d G:%d F:%d SP:%d 卡片:%d%s%s' % (
                self.macInstance.player.name,
                self.macInstance.player.ap['current'], self.macInstance.player.ap['max'],
                self.macInstance.player.bc['current'], self.macInstance.player.bc['max'],
                self.macInstance.player.gold, self.macInstance.player.friendship_point,
                self.macInstance.player.ex_gauge, self.macInstance.player.card.count,
                self.macInstance.player.fairy['alive'] and ' 妖精存活' or '',
                self.macInstance.player.fairy['guild_alive'] and ' 公会妖存活' or '')
            setT(strt)
            time.sleep(28)
        # elif os.name == 'posix':
         #   pass

class conn_ani(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.flag = 1
    def run(self):
        cnt = 0
        while self.flag == 1:
            print('Connecting.%s%s%s' % ('.' * cnt, ' ' * (3 - cnt), '\b' * 20), end = '')
            cnt = (cnt + 1) % 4
            time.sleep(0.15)

class MAClient(object):
    global plugin
    plugin = maclient_plugin.plugins(maclient_logging.Logging('plugin_logging'), __version__)
    def __init__(self, configfile = '', savesession = False, servloc = None):
        if not PYTHON3:
            reload(sys)
            sys.setdefaultencoding('utf-8')
        self.cf = ConfigParser.ConfigParser()
        if configfile == '':
            if not os.path.exists('%s%sconfig.ini' % (getPATH0, opath.sep)):
                print(du8('正在尝试以默认配置文件启动，但该文件(config.ini)不存在'))
                self._exit(1)
            self.configfile = getPATH0 + opath.sep + 'config.ini'
        else:
            if not os.path.exists(configfile):
                print(du8('正在尝试以配置文件(%s)启动，但该文件不存在' % configfile))
                self._exit(1)
            self.configfile = configfile
        self.logger = maclient_logging.Logging('logging')  # =sys.modules['logging']
        # configuration
        self.cf.read(self.configfile)
        self.load_config(loc_override = servloc)
        # 映射变量
        plugin.set_maclient_val(self.__dict__)
        # 添加引用
        self.plugin = plugin
        self.cfg_save_session = savesession
        self.settitle = False
        self.posttime = 0
        # self.set_remote(None)
        ua = self._read_config('system', 'user-agent')
        try:
            self.poster = maclient_network.poster(self.loc, self.logger, ua)
        except ImportError as ex:
            # No module named xxxx
            mod_name = str(ex)[16:]
            self.logger.error('%s模块不存在%s' % (mod_name, '，无法运行韩服' if mod_name == 'maclient_crypt_ext' else ''))
            self._exit(10)
        if ua:
            self.logger.debug('system:ua changed to %s' % (self.poster.header['User-Agent']))
        self.load_cookie()
        if self.cfg_save_traffic:
            self.poster.enable_savetraffic()
        # eval
        self.evalstr_fairy = self._eval_gen(self._read_config('condition', 'fairy_select') or 'True', eval_fairy_select, 'fairy')
        self.evalstr_area = self._eval_gen(self._read_config('condition', 'explore_area'), eval_explore_area,'area')
        self.evalstr_floor = self._eval_gen(self._read_config('condition', 'explore_floor'), eval_explore_floor, 'floor')
        self.evalstr_selcard = self._eval_gen(self._read_config('condition', 'select_card_to_sell'), eval_select_card, 'card')
        self.evalstr_fairy_select_carddeck = self._eval_gen(self._read_config('condition', 'fairy_select_carddeck'),
            eval_fairy_select_carddeck, 'fairy')
        self.evalstr_factor = self._eval_gen(self._read_config('condition', 'factor'), [])
        # tasker须动态生成#self.evalstr_task=self._eval_gen(self._read_config('system','tasker'),[])
        self.logger.debug('system:知识库版本 %s%s' % (maclient_smart.__version__, str(maclient_smart)[-5:] in ('.so\'>','pyd\'>') and ' C-Extension' or ''))
        self.logger.debug('system:初始化完成(服务器:%s)' % self.loc)
        self.lastposttime = 0
        self.lastfairytime = 0
        self.lastflushcfgtime = 0
        #self.errortimes = 0
        self.player_initiated = False

    def load_config(self, loc_override = None):
        # configurations
        self.loc = loc_override or self._read_config('system', 'server')
        self.uid = self._read_config('account_%s' % self.loc, 'user_id')
        self.playerfile = '.%s-%s.playerdata' % (self.loc, self.uid) if self.uid not in '0' else '--PLACE-HOLDER--'
        self.username = self._read_config('account_%s' % self.loc, 'username')
        self.password = self._read_config('account_%s' % self.loc, 'password')
        self.cfg_auto_explore = not self._read_config('tactic', 'auto_explore') == '0'
        self.cfg_auto_sell = not self._read_config('tactic', 'auto_sell_cards') == '0'
        self.cfg_autogacha = not self._read_config('tactic', 'auto_fp_gacha') == '0'
        self.cfg_auto_fairy_rewards = not self._read_config('tactic', 'auto_fairy_rewards') == '0'
        self.cfg_auto_build = self._read_config('tactic', 'auto_build') == '1' and '1' or '0'
        self.cfg_fpgacha_buld = self._read_config('tactic', 'fp_gacha_bulk') == '1' and '1' or '0'
        self.cfg_sell_card_warning = int(self._read_config('tactic', 'sell_card_warning') or '1')
        self.cfg_auto_rt_level = int(self._read_config('tactic', 'auto_red_tea_level'))
        self.cfg_auto_choose_red_tea = self._read_config('tactic', 'auto_choose_red_tea') != '0'
        self.cfg_strict_bc = self._read_config('tactic', 'strict_bc') == '1'
        self.cfg_fairy_final_kill_hp = int(self._read_config('tactic', 'fairy_final_kill_hp') or '20000')
        self.cfg_save_traffic = not self._read_config('system', 'save_traffic') == '0'
        self.cfg_auto_greet = (self._read_config('tactic', 'auto_greet') or '1') == '1'
        self.cfg_greet_words = self._read_config('tactic', 'greet_words') or (
            self.loc == 'tw' and random.choice(['大家好.', '問好']) or random.choice(['你好！', '你好！请多指教！']))
        self.cfg_factor_getnew = not self._read_config('tactic', 'factor_getnew') == '0'
        self.cfg_auto_update = not self._read_config('system', 'auto_update') == '0'
        self.logger.basicConfig(level = self._read_config('system', 'loglevel') or '2')
        self.logger.setlogfile('events_%s.log' % self.loc)
        self.cfg_delay = float(self._read_config('system', 'delay'))
        self.cfg_display_ani = (self._read_config('system', 'display_ani') or '1') == '1'
        #self.logger = logging  # 映射
        global plugin
        self.plugin = plugin  # 映射
        if (self._read_config('system', 'enable_plugin') or '1') == '1':
            disabled_plugin = self._read_config('plugin', 'disabled').split(',')
            plugin.enable = True
            plugin.load_plugins()
            plugin.set_disable(disabled_plugin)
            plugin.scan_hooks()
            self.logger.debug('plugin:loaded %s' % (','.join(plugin.plugins.keys())) or 'NONE')
        else:
            plugin.enable = False
        _app_ver_override = self._read_config('system', 'app_ver_%s' % self.loc[:2])
        if _app_ver_override:
            if not _app_ver_override.isdigit():
                self.logger.warning('重载版本号"%s"不是数字，将不使用' % _app_ver_override)
            else:
                setattr(maclient_smart, 'app_ver_%s' % self.loc[:2], int(_app_ver_override))


    def load_cookie(self):
        self.cookie = self._read_config('account_%s' % self.loc, 'session')
        self.poster.set_cookie(self.cookie)

    # def set_remote(self,remoteInstance):
    #     self.remote=remoteInstance
    #     self.remoteHdl=(self.remote ==None and (lambda method=None,fairy='':True) or self.remote_Hdl_())
    #     if self.remote:
    #         res,msg=self.remote.login()
    #         if res:
    #             self.logger.debug('remote_hdl:%s'%msg)
    #             return True
    #         else:
    #             self.logger.warning('remote_hdl:%s'%msg)
    #             return False

    def _dopost(self, urikey, postdata = '', usecookie = True, setcookie = True, extraheader = {'Cookie2': '$Version=1'}, xmlresp = True, noencrypt = False, savetraffic = False, no2ndkey=False ):
        # self.remoteHdl()
        if self.cfg_display_ani:
            connani = conn_ani()
            connani.setDaemon(True)
            connani.start()
        if time.time() - self.lastposttime <= self.cfg_delay:
            if  self.cfg_delay == 0:
                self.logger.warning('post:NO DELAY!')
            else:
                #self.logger.debug('post:slow down...')
                time.sleep(random.randint(int(0.75 * self.cfg_delay), int(1.25 * self.cfg_delay)))
        resp, _dec = self.poster.post(urikey, postdata, usecookie, setcookie, extraheader, noencrypt, savetraffic, no2ndkey)
        self.lastposttime = time.time()
        if self.cfg_display_ani:
            connani.flag = 0
            connani.join(0.16)
        if int(resp['status']) >= 400:
            return resp, _dec
        if savetraffic and self.cfg_save_traffic and len(_dec) == 0:
            self.logger.debug('post:save traffic')
            self.lastposttime += 3  # 本来应该过一会才会收到所有信息的
            return resp, _dec
        resp.update({'error':False, 'errno':0, 'errmsg':''})
        if not xmlresp:
            dec = _dec
        else:
            try:
                dec = XML2Dict.fromstring(_dec).response
            except:
                try:
                    dec = XML2Dict.fromstring(re.compile('&(?!#)').sub('&amp;',_dec)).response
                except:
                    self.logger.error('大概是换了版本号/新加密方法等等，总之是跪了orz…请提交debug_xxx.xml\n%s'
                        'http://yooooo.us/2013/maclient' % 
                        ('你也可以试试重新登录(输入rl)\n' if self.loc == 'jp' else ''))
                    with open('debug_%s.xml' % urikey.replace('/', '#').replace('?', '~'),'w') as f:
                        f.write(_dec)
                    self._exit(3)
            try:
                err = dec.header.error
            except:
                pass
            else:
                if err.code != '0':
                    resp['errmsg'] = err.message
                    # 1050木有BC 1010卖了卡或妖精已被消灭 8000基友点或卡满了 1020维护 1030有新版本
                    if not err.code in ['1050', '1010', '1030'] and not (err.code == '1000' and self.loc == 'jp'):  # ,'8000']:
                        self.logger.error('code:%s msg:%s' % (err.code, err.message))
                        resp.update({'error':True, 'errno':int(err.code)})
                    if err.code == '9000':
                        self._write_config('account_%s' % self.loc, 'session', '')
                        self.logger.info('A一个新的小饼干……')
                        #重连策略
                        _gap = self._read_config('system', 'reconnect_gap') or '0'
                        if re.match('\d+\:\d+', _gap):
                            _gap = _gap.split(':')
                            _gap = 60 * (int(_gap[0]) - datetime.datetime.now().hour) +\
                                        int(_gap[1]) - datetime.datetime.now().minute
                            if _gap < 0:#明天
                                _gap += 1440
                        elif _gap.isdigit():
                            _gap = int(_gap)
                        else:
                            self.logger.warning('reconnect_gap配置错误')
                            _gap = 0
                        if _gap:
                            self.logger.sleep('将在%s%d分钟后重连' % 
                                ((_gap >60 and ("%d小时" % (_gap / 60)) or '') , (_gap > 60 and (_gap % 60) or _gap))
                            )
                            time.sleep(_gap * 60)
                        self.login(fast = True)
                        return self._dopost(urikey, postdata, usecookie, setcookie, extraheader, xmlresp, noencrypt)
                    elif err.code == '1020':
                        self.logger.sleep('因为服务器维护，休息约30分钟')
                        time.sleep(random.randint(28, 32) * 60)
                        if hasattr(self, 'player'):
                            self.player.rev_update_checked = False  # 置为未检查
                        return resp, dec
                    elif err.code == '1030':
                        self.logger.error('客户端版本号升级了\n'
                            '你可以在GUI中手动更改，或者在MAClient发布更新后使用pu更新\n'
                            '当前版本号是%d，一般来说加1就可以了' % getattr(maclient_smart, 'app_ver_%s' % self.loc[:2]))
                        _v = self._read_config('system', 'app_ver_%s' % self.loc)
                        if _v and _v.isdigit():
                            self.logger.warning('注意：你可能在配置文件中设置了错误的重载版本号，请删除system块下的app_ver_%s项'
                                    % self.loc[:2])
                        self._exit(int(err.code))
                    #return resp, dec
            if not self.player_initiated :
                open(self.playerfile, 'w').write(_dec)
            else:
                # check revision update
                if sum(self.player.rev_need_update) >=1:
                    if self.cfg_auto_update:
                        self.logger.info('更新%s%s%s%s数据……' % (
                            ' 卡片' if self.player.rev_need_update[0] else '',
                            ' 道具' if self.player.rev_need_update[1] else '',
                            ' 强敌' if self.player.rev_need_update[2] else '',
                            ' Combo' if self.player.rev_need_update[3] else ''))
                        import maclient_update
                        crev, irev, brev, cbrev = maclient_update.update_master(self.loc[:2], self.player.rev_need_update, self.poster)
                        self.logger.info('%s%s%s%s' % (
                            '卡片数据更新为rev.%s' % crev if crev else '',
                            '道具数据更新为rev.%s' % irev if irev else '',
                            '强敌数据更新为rev.%s' % brev if brev else '',
                            'Combo数据更新为rev.%s' % cbrev if cbrev else ''))
                        self.player.reload_db()
                        self.player.rev_need_update = False, False, False, False
                    else:
                        self.logger.warning('检测到服务器游戏数据与游戏数据不一致，请手动更新数据库')
                if not resp['error'] or resp['errno'] == 8000:
                    # update profile
                    update_dt = self.player.update_all(dec)
                    # self.remoteHdl(method='PROFILE')
                    if self.settitle:
                        setT('[%s] AP:%d/%d BC:%d/%d G:%d F:%d SP:%d 卡片:%d%s%s' % (
                            self.player.name,
                            self.player.ap['current'], self.player.ap['max'],
                            self.player.bc['current'], self.player.bc['max'],
                            self.player.gold, self.player.friendship_point,
                            self.player.ex_gauge, self.player.card.count,
                            self.player.fairy['alive'] and ' 妖精存活' or '',
                            self.player.fairy['guild_alive'] and ' 公会妖存活' or ''))
                    else:
                        if self.posttime == 5:
                            self.logger.sleep('汇报 AP:%d/%d BC:%d/%d G:%d F:%d SP:%d%s%s' % (
                                self.player.ap['current'], self.player.ap['max'],
                                self.player.bc['current'], self.player.bc['max'],
                                self.player.gold, self.player.friendship_point, self.player.ex_gauge,
                                self.player.fairy['alive'] and ' FAIRY_ALIVE' or '',
                                self.player.fairy['guild_alive'] and ' GUILD_FAIRY_ALIVE' or ''))
                        self.posttime = (self.posttime + 1) % 6
                    if update_dt[1]:
                        self.logger.debug(update_dt[0])
                        open(self.playerfile, 'w').write(_dec)
                        self.logger.debug('post:master cards saved.')
                    # auto check cards and fp
                    if not self.auto_check(urikey):
                        self.logger.error('由于以上↑的原因，无法继续执行！')
                        self._exit(1)
        if setcookie and 'set-cookie' in resp:
            self.cookie = resp['set-cookie'].split(',')[-1].rstrip('path=/').strip()
            if self.cfg_save_session:
                self._write_config('account_%s' % self.loc, 'session', self.cookie)

        return resp, dec

    def _read_config(self, sec, key):
        if not self.cf.has_section(sec):
            self.cf.add_section(sec)
        if self.cf.has_option(sec, key):
            val = self.cf.get(sec, key)
            if sys.platform == 'win32' and not PYTHON3:
                val = val.decode(CODEPAGE)  # .encode('utf-8')
        else:
            val = ''
        if val == '':
            return ''
        else:
            return val

    def _write_config(self, sec, key, val):
        if not self.cf.has_section(sec):
            self.cf.add_section(sec)
        self.cf.set(sec, key, val)
        self._request_flush_config()

    def _list_option(self, sec):
        return self.cf.options(sec)

    def _del_option(self, sec, key):
        ret = self.cf.remove_option(sec, key)
        self._request_flush_config()
        return ret

    def _request_flush_config(self, force = False):
        if self.lastflushcfgtime - time.time() > 300 or force:#5分钟写一次
            f = open(self.configfile, "w")
            self.cf.write(f)
            f.flush()
            f.close()
            self.lastflushcfgtime = time.time()

    def _eval_gen(self, streval, repllst = [], super_prefix = None):
        repllst2 = [('HH', "datetime.datetime.now().hour"), ('MM', "datetime.datetime.now().minute"), ('FAIRY_ALIVE', 'self.player.fairy["alive"]'), ('GUILD_ALIVE', "self.player.fairy['guild_alive']"), ('BC%', '1.0*self.player.bc["current"]/self.player.bc["max"]'), ('AP%', '1.0*self.player.ap["current"]/self.player.ap["max"]'), ('BC', 'self.player.bc["current"]'), ('AP', 'self.player.ap["current"]'), ('SUPER', 'self.player.ex_gauge'), ('GOLD', 'self.player.gold'), ('FP', 'self.friendship_point')]
        if streval == '':
            return 'True'
        if super_prefix:
            streval = streval.replace('$.', '%s.'%super_prefix)
        for (i, j) in repllst + repllst2:
            streval = streval.replace(i, j)
        return streval

    def tolist(self, obj):
        if not isinstance(obj, list):
            if isinstance(obj, unicode):
                return [object_dict({'value':obj})]
            return [obj]
        else:
            return obj

    @plugin.func_hook
    def tasker(self, taskname = '', cmd = ''):
        cnt = int(self._read_config('system', 'tasker_times') or '1')
        if cnt == 0:
            cnt = 9999999
        if taskname == '':
            taskname = self._read_config('system', 'taskname')
            if taskname == '':
                self.logger.info('没有配置任务！')
                return
        if  cmd != '':
            tasks = cmd
            cnt = 1
        taskeval = self._eval_gen(self._read_config('tasker', taskname), eval_task)
        for c in xrange(cnt):
            self.logger.debug('tasker:loop %d/%d' % (c + 1, cnt))
            if cmd == '':
                tasks = eval(taskeval)
                self.logger.debug('tasker:eval result:%s' % (tasks))
            if isinstance(tasks, bool):
                self.logger.error('任务表达式为空或格式错误，可使用GUI作参考:\n表达式 %s\n输出 %s' % (taskeval, tasks))
                self._exit(1)
            for task in tasks.split('|'):
                if task.startswith('t:'):#is task
                    return self.tasker(taskname = task[2:])
                elif task.split()[0] in CMD_NOLOGIN or \
                    (self.plugin.enable and task.split()[0] in self.plugin.extra_cmd_no_login):#无需登录可执行的命令
                    pass
                elif not self.player_initiated:
                    self.login()
                task = (task + ' ').split(' ')
                self.logger.debug('tasker:%s' % task[0])
                task[0] = task[0].lower()
                if task[0] in plugin.extra_cmd:
                    plugin.do_extra_cmd(' '.join(task))
                elif task[0] == 'set_card' or task[0] == 'sc':
                    if task[1] == '':
                        self.logger.error('set_card need 1 argument')
                    else:
                        self.set_card(' '.join(task[1:-1]))
                elif task[0] == 'auto_set' or task[0] == 'as':
                    self.invoke_autoset(' '.join(task[1:]))
                elif task[0] == 'explore' or task[0] == 'e':
                    self.explore(' '.join(task[1:]))
                elif task[0] == 'factor_battle' or task[0] == 'fcb':
                    arg_lake = ''
                    arg_minbc = 0
                    if len(task) > 2:
                        for i in range(len(task) - 2):
                            if task[i + 1].startswith('lake:') or task[i + 1].startswith('l:'):
                                arg_lake = task[i + 1].split(':')[1]
                            else:
                                arg_minbc = int(task[i + 1])
                    self.factor_battle(minbc = arg_minbc, sel_lake = arg_lake)
                elif task[0] == 'fairy_battle' or task[0] == 'fyb':
                    self.fairy_battle_loop(task[1])
                elif task[0] == 'fairy_select' or task[0] == 'fs':
                    for i in xrange(1, len(task)):
                        if task[i].startswith('deck:'):
                            self.fairy_select(cond = ' '.join(task[1:i]), carddeck = ' '.join(task[i:-1])[5:])
                            break
                    if i == len(task) - 1:
                        self.fairy_select(cond = ' '.join(task[1:]))
                elif task[0] == 'green_tea' or task[0] == 'gt':
                    self.green_tea(tea = HALF_TEA if '/' in ' '.join(task[1:]) else FULL_TEA)
                elif task[0] == 'red_tea' or task[0] == 'rt':
                    self.red_tea(tea = HALF_TEA if '/' in ' '.join(task[1:]) else FULL_TEA)
                elif task[0] == 'sell_card' or task[0] == 'slc':
                    self.select_card_sell(' '.join(task[1:]))
                elif task[0] == 'set_server' or task[0] == 'ss':
                    if task[1] not in ['cn','cn1','cn2','cn3','tw','kr','jp','sg','my']:
                        self.logger.error('服务器"%s"无效'%(task[1]))
                    else:
                        self._write_config('system', 'server', task[1])
                        self.loc = task[1]
                        self.poster.load_svr(self.loc)
                        self.load_config()
                elif task[0] == 'relogin' or task[0] == 'rl':
                    self._write_config('account_%s' % self.loc, 'session', '')
                    self.login()
                elif task[0] == 'login' or task[0] == 'l':
                    if len(task) == 2:
                        task.append('')
                    self.login(uname = task[1], pwd = task[2])
                elif task[0] == 'friend' or task[0] == 'f':
                    if len(task) == 2:
                        task = [task[0], '', '']
                    self.friends(task[1], task[2] == 'True')
                elif task[0] == 'point' or task[0] == 'p':
                    self.point_setting()
                elif task[0] == 'rb' or task[0] == 'reward_box':
                    if len(task) == 2:
                        task = [task[0], '12345']
                    self.reward_box(task[1])
                elif task[0] == 'gacha' or task[0] == 'g':
                    if len(task) == 2:
                        task[1] = GACHA_FRIENNSHIP_POINT
                    else:
                        task[1] = int(task[1])
                    self.gacha(gacha_type = task[1])
                elif task[0] in ['greet', 'gr', 'like']:
                    self.like(words = task[1])
                elif task[0] in ['sleep', 'slp']:
                    slptime = float(eval(self._eval_gen(task[1])))
                    self.logger.sleep('睡觉%s分' % slptime)
                    time.sleep(slptime * 60)
                else:
                    self.logger.warning('command "%s" not recognized.' % task[0])
                if cnt != 1:
                    self.logger.sleep('tasker:正在滚床单wwww')
                    time.sleep(3.15616546511)
                    resp, ct = self._dopost('mainmenu', no2ndkey = True)  # 初始化

    def login(self, uname = '', pwd = '', fast = False):
        # sessionfile='.%s.session'%self.loc
        while True:
            if os.path.exists(self.playerfile) and self._read_config('account_%s' % self.loc, 'session') != '' \
                and (time.time() - os.path.getmtime(self.playerfile) < 43200) and uname == '':
                self.logger.info('加载了保存的账户XD')
                dec = open(self.playerfile, 'r').read()  # .encode('utf-8')
                ct = xmldict = XML2Dict.fromstring(dec).response
            else:
                self.username = uname or self.username
                self.password = pwd or self.password
                if self.username == '':
                    self.username = raw_inputd('Username:')
                if self.password == '' or (uname != '' and pwd == ''):
                    self.password = getpass('Password:')
                    if raw_inputd('是否保存密码(y/n)？') == 'y':
                        self._write_config('account_%s' % self.loc, 'password', self.password)
                        self.logger.warning('保存的登录信息没有加密www')
                token = self._read_config('system', 'device_token').replace('\\n', '\n') or \
                'nuigiBoiNuinuijIUJiubHOhUIbKhuiGVIKIhoNikUGIbikuGBVININihIUniYTdRTdREujhbjhj'
                if not fast:
                    ct = self._dopost('check_inspection', xmlresp = False, extraheader = {}, usecookie = False, no2ndkey = True)[1]
                    # self.poster.update_server(ct)
                    pdata='login_id=%s&password=%s&app=and&token=%s' % (self.username, self.password, token)
                    # if self.loc == 'kr':
                    #      pdata='S=nosessionid&%s' % pdata
                    if self.loc not in ['jp', 'my']:
                        self._dopost('notification/post_devicetoken', postdata = pdata , xmlresp = False, no2ndkey = True)
                if self.loc == 'my':
                    login_uri = 'actozlogin'
                else:
                    login_uri = 'login'
                if self.loc == 'kr':
                    pdata = 'login_id=%s&IsGetPus=1&DeviceKey=35%d&PushId=%s&Language=zh&CountryCode=CN&password=%s' % (self.username, random.randrange(0, 1000000000), token, self.password)
                else:
                    pdata = 'login_id=%s&password=%s' % (self.username, self.password)
                resp, ct = self._dopost(login_uri, postdata = pdata, no2ndkey = True)
                if resp['error']:
                    self.logger.info('登录失败么么哒w')
                    self._exit(1)
                else:
                    pdata = ct.header.your_data
                    self.logger.info('[%s] 登录成功!\n' % self.username + \
                        'AP:%s/%s BC:%s/%s 金:%s 基友点:%s %s\n' % (
                            pdata.ap.current, pdata.ap.max,
                            pdata.bc.current, pdata.bc.max,
                            pdata.gold, pdata.friendship_point,
                            pdata.fairy_appearance == '1' and '妖精出现中!!' or '') +
                        '蛋蛋卷:%s 等级:%s 完成度:%s %s%s%s\n' % (
                            pdata.gacha_ticket,
                            pdata.town_level,
                            pdata.percentage,
                            pdata.free_ap_bc_point != '0' and '有未分配的点数yo~ ' or '',
                            pdata.friends_invitations != '0' and '收到好友邀请了呢 ' or '',
                            ct.body.mainmenu.rewards == '1' and '收到礼物了~' or '')
                    )
                    self._write_config('account_%s' % self.loc, 'username', self.username)
                    self._write_config('record', 'last_set_card', '')
                    self._write_config('record', 'last_set_bc', '0')
            if self.initplayer(ct):
                break

    def initplayer(self, xmldict):
        if self.player_initiated:  # 刷新
            try:
                self.player.update_all(xmldict)
            except AttributeError:
                self.logger.warning('error parsing playerdata')
        else:  # 第一次
            try:
                self.player = maclient_player.player(xmldict, self.loc)
            except AttributeError:
                self.logger.warning('保存的登录信息有误，将重新登录')
                if opath.exists(self.playerfile):
                    os.remove(self.playerfile)
                return False
            if not self.player.success:
                self.logger.error('当前登录的用户(%s)已经运行了一个MAClient' % (self.username))
                self._exit(2)
            self.carddb = self.player.card.db
            self.player.boss.name_wake = '|'.join((self.player.boss.name_wake,maclient_smart.name_wake_rare))
            self.player_initiated = True
            if self.player.id != '0':
                self._write_config('account_%s' % self.loc, 'user_id', self.player.id)
            else:
                self.player.id = self._read_config('account_%s' % self.loc, 'user_id')
            # for jp server, regenerate
            if self.loc == 'jp':
                self.poster.gen_2nd_key(self.username,self.loc)
        if self.settitle:
            # 窗口标题线程
            self.stitle = set_title(self)
            self.stitle.setDaemon(True)
            self.stitle.start()
        if self.loc[:2] in ['cn', 'tw'] and not self.player.card.latest_multi:
            self.logger.warning('倍卡数据可能已过期，请通过"更新数据库"选项更新\n一般请在维护后一天左右使用更新')
        return True

    @plugin.func_hook
    def auto_check(self, doingwhat):
        if doingwhat in ['exploration/fairybattle', 'exploration/explore', 'gacha/buy']:
            if int(self.player.card.count) >= getattr(maclient_smart, 'max_card_count_%s' % self.loc[:2]):
                if self.cfg_auto_sell:
                    self.logger.info('卡片放满了，自动卖卡 v(￣▽￣*)')
                    return self.select_card_sell()
                else:
                    self.logger.warning('卡片已经放不下了，请自行卖卡www')
                    return False
            if self.player.friendship_point > getattr(maclient_smart, 'max_fp_%s' % self.loc[:2]) * 0.95 and \
                doingwhat != 'gacha/buy':
                if self.cfg_autogacha:
                    self.logger.info('绊点有点多，自动转蛋(*￣▽￣)y ')
                    self.gacha(gacha_type = GACHA_FRIENNSHIP_POINT)
                    return True
                else:
                    self.logger.warning('绊点已经很多，请自行转蛋消耗www')
                    return True #not fatal
        return True

    @plugin.func_hook
    def check_strict_bc(self, cost = None, refresh = False):
        if not self.cfg_strict_bc:
            return False
        last_set_bc = cost or int(self._read_config('record', 'last_set_bc') or '0')
        if self.player.bc['current'] < last_set_bc:
            self.logger.warning('strict_bc:严格BC模式已触发www')
            return True
        else:
            self.logger.debug('strict_bc:nothing happened~')
            return False

    @plugin.func_hook
    def invoke_autoset(self, autoset_str, cur_fairy = None):
        aim, fairy, maxline, test_mode, delta, includes, bclimit, fast_mode, sel = 'MAX_DMG', None, 1, True, 1, [], BC_LIMIT_CURRENT, True, 'card.lv>=70 or card.plus_limit_count == 0'
        save2deck, _just_set_save2deck = None, False
        if cur_fairy:
            fairy = cur_fairy
        args = autoset_str.split(' ')
        for _idx in range(len(args)):
            if _just_set_save2deck:
                _just_set_save2deck = False
                continue
            arg = args[_idx]
            if arg.startswith('aim:'):
                aim = arg[4:]
            elif arg.startswith('fairy:'):
                fairy = object_dict()
                fairy.lv, fairy.hp, nothing = map(int, (arg[6:] + ',-325').split(','))
                if nothing != -325:
                    fairy.IS_WAKE = False
                else:
                    fairy.IS_WAKE = True
                aim = 'DEFEAT'
            elif arg.startswith('line:'):
                maxline = int(arg[5:])
            elif arg == 'notest':
                test_mode = False
            elif arg.startswith('sel'):
                sel = arg[4:]
            elif arg.startswith('bc:'):
                _l = arg[3:]
                if _l == 'max':
                    bclimit = BC_LIMIT_MAX
                elif _l in ['cur', 'current']:
                    bclimit = BC_LIMIT_CURRENT
                else:
                   bclimit = int(_l)
            elif arg.startswith('delta:'):
                delta = float(arg[6:])
            elif arg.startswith('nofast'):
                fast_mode = False
            elif arg.startswith('incl:'):
                includes = map(int, arg[5:].split(','))
            elif arg.startswith('>'):
                if len(arg) > 1:#'xxx >deck1'
                    save2deck = arg[1:]
                elif _idx + 1 < len(args):
                    save2deck = args[_idx + 1]
                    _just_set_save2deck = True
                else:
                    self.logger.warning('无法从"%s"中提取卡组名' % arg)
            elif arg != '':
                self.logger.warning('未识别的参数 %s' % arg)
        try:
            aim = getattr(maclient_smart, aim.upper())
        except AttributeError:
            self.logger.warning('未识别的目标 %s' % aim)
        return self.set_card('auto_set', aim = aim, includes = includes, maxline = maxline, seleval = sel, fairy_info = fairy, delta = delta, test_mode = test_mode, bclimit = bclimit, fast_mode = fast_mode, save2deck = save2deck)

    @plugin.func_hook
    def set_card(self, deckkey, **kwargs):
        '''
        Returns: whether changes, cost
        '''
        if deckkey == 'no_change':
            self.logger.debug('set_card:no_change!')
            return False, int(self._read_config('record', 'last_set_bc') or '0')
        elif deckkey.startswith('auto_set'):
            if len(deckkey) > 8:  # raw string : auto_set(CONDITIONS)
                if 'cur_fairy' in kwargs:
                    cf = kwargs.pop('cur_fairy')
                else:
                    cf = None
                return self.invoke_autoset('%s notest' % deckkey[9:-1], cur_fairy = cf)
            else:
                test_mode = kwargs.pop('test_mode')
                bclimit = kwargs.pop('bclimit')
                save2deck = kwargs.pop('save2deck')
                res = maclient_smart.carddeck_gen(
                    self.player.card,
                    bclimit = (bclimit == BC_LIMIT_MAX and self.player.bc['max'] or (
                                bclimit == BC_LIMIT_CURRENT and self.player.bc['current'] or bclimit)),
                    **kwargs)
                if len(res) == 5:
                    atk, hp, last_set_bc, sid, mid = res
                    param = map(str, sid)
                    # 别看比较好
                    print(du8('设置卡组为: ATK:%d HP:%d COST:%d\n%s' % (
                        sum(atk),
                        hp,
                        last_set_bc,
                            '\n'.join(
                                map(lambda x, y: '%s\tATK:%-5d' % (x, y),
                                    ['|'.join(map(
                                            lambda x:'   %-12s' % self.carddb[x][0],
                                            mid[i:min(i + 3, len(mid))]
                                         ))
                                        for i in range(0, len(mid), 3)
                                    ],  # 卡组分成一排排
                                    atk
                                    )
                                )
                            )
                        ))
                else:
                    self.logger.error(res[0])
                    return False, -1
                if save2deck:
                    self.logger.info('保存卡组到了 %s' % save2deck)
                    self._write_config('carddeck', save2deck, ','.join(param))
                if test_mode:
                    return False, 0
        else:
            try:
                cardid = self._read_config('carddeck', deckkey)
            except AttributeError:
                self.logger.warning('set_card:忘记加引号了？')
                return False, 0
            if cardid == self._read_config('record', 'last_set_card'):
                self.logger.debug('set_card:card deck satisfied, not changing.')
                return False, int(self._read_config('record', 'last_set_bc') or '0')
            if cardid == '':
                self.logger.warning('set_card:不存在的卡组名？')
                return False, -1
            cardid = cardid.split(',')
            param = []
            last_set_bc = 0
            for i in xrange(len(cardid)):
                if cardid[i] == 'empty':
                    param.append('empty')
                elif len(cardid[i]) > 4:
                    try:
                        mid = self.player.card.sid(cardid[i]).master_card_id
                    except IndexError:
                        self.logger.error('你木有sid为 %s 的卡片' % (cardid[i]))
                    else:
                        last_set_bc += int(self.carddb[int(mid)][2])
                        param.append(str(cardid[i]))
                else:
                    c = self.player.card.cid(cardid[i])
                    if c != []:
                        param.append(str(c[-1].serial_id))
                        last_set_bc += int(self.carddb[int(cardid[i])][2])
                    else:
                        self.logger.error('你木有id为 %s (%s)的卡片' % (cardid[i], self.carddb[int(cardid[i])][0]))
        noe = ','.join(param).replace(',empty', '').replace('empty,', '').split(',')
        lc = random.choice(noe)
        t = 5 + random.random() * len(noe) * 0.7
        param = param + ['empty'] * (12 - len(param))
        while True:
            if param == ['empty'] * 12:
                break
            if self._dopost('roundtable/edit', postdata = 'move=1')[0]['error']:
                break
            self.logger.sleep('休息%d秒，假装在找卡' % t)
            time.sleep(t)
            postparam = 'C=%s&lr=%s&deck_id=1' % (','.join(param), lc)
            #if self.loc != 'tw':#cn, jp, kr:
            if self._dopost('cardselect/savedeckcard', postdata = postparam)[0]['error']:
                break
            self.logger.info('更换卡组为%s cost%d' % (deckkey, last_set_bc))
            # 保存
            self._write_config('record', 'last_set_card', self._read_config('carddeck', deckkey) or ','.join(param).rstrip(',empty'))
            # 记录BC
            self._write_config('record', 'last_set_bc', str(last_set_bc))
            return True, last_set_bc
        self.logger.info('卡组没有改变')
        return False, 0

    @plugin.func_hook
    def _use_item(self, itemid, noerror = False):
        if itemid == 0:
            self.logger.debug('pseudo item id.')
            return
        if self.player.item.get_count(int(itemid)) == 0 :
            if not noerror:
                self.logger.error('道具 %s 数量不足' % self.player.item.get_name(int(itemid)))
            return False
        param = 'item_id=%s' % itemid
        resp, ct = self._dopost('item/use', postdata = param)
        if resp['error']:
            return False
        else:
            self.logger.info('使用了道具 %s' % self.player.item.get_name(int(itemid)))
            self.logger.debug('useitem:item %s : %d left' % (itemid, self.player.item.get_count(int(itemid))))
            return True

    @plugin.func_hook
    def red_tea(self, silent = False, tea = FULL_TEA, noerror = False):
        auto = float(self._read_config('tactic', 'auto_red_tea') or '0')
        if auto >= 1 or (auto >= 0.5 and tea == HALF_TEA):
            self._write_config('tactic', 'auto_red_tea', str(auto - (1 if tea == FULL_TEA else 0.5)))
            res = self._use_item(
                   str((0 if tea == FULL_TEA else getattr(maclient_smart, 'half_bc_offset_%s' % self.loc[:2])) + 2)
                , noerror = noerror)
        else:
            if silent:
                self.logger.debug('red_tea:auto mode, let it go~')
                return False
            else:
                if raw_inputd('来一坨红茶？ y/n ') == 'y':
                    res = self._use_item(
                               str((0 if tea == FULL_TEA else getattr(maclient_smart, 'half_bc_offset_%s' % self.loc[:2])) + 2)
                            , noerror = noerror)
                else:
                    res = False
        #if res:
        #    self.player.bc['current'] = self.player.bc['max'] * res
        return res

    @plugin.func_hook
    def green_tea(self, silent = False, tea = FULL_TEA, noerror = False):
        auto = float(self._read_config('tactic', 'auto_green_tea') or '0')
        if auto >= 1 or (auto >= 0.5 and tea == HALF_TEA):
            self._write_config('tactic', 'auto_green_tea', str(auto - (1 if tea == FULL_TEA else 0.5)))
            res = self._use_item(
                       str((0 if tea == FULL_TEA else getattr(maclient_smart, 'half_ap_offset_%s' % self.loc[:2])) + 1)
                    , noerror = noerror)
        else:
            if silent:
                self.logger.debug('green_tea:auto mode, let it go~')
                return False
            else:
                if raw_inputd('嗑一瓶绿茶？ y/n ') == 'y':
                    res = self._use_item(
                           str((0 if tea == FULL_TEA else getattr(maclient_smart, 'half_ap_offset_%s' % self.loc[:2])) + 1)
                        , noerror = noerror)
                else:
                    res = False
        #if res:
        #    self.player.ap['current'] = self.player.ap['max'] * res
        return res

    @plugin.func_hook
    def explore(self, cond = ''):
        # 选择秘境
        has_boss = []
        while True:
            resp, ct = self._dopost('exploration/area')
            if resp['error']:
                return
            areas = ct.body.exploration_area.area_info_list.area_info
            if not self.cfg_auto_explore:
                for i in xrange(len(areas)):
                    print(du8('%d.%s(%s%%/%s%%) %s' % \
                        (i + 1, areas[i].name, areas[i].prog_area, areas[i].prog_item, (areas[i].area_type == '1' and 'EVENT' or ''))))
                areasel = [areas[int(raw_inputd('选择： ') or '1') - 1]]
            else:
                self.logger.info('自动选图www')
                areasel = []
                cond_area = (cond == '' and self.evalstr_area or self._eval_gen(cond, eval_explore_area, 'area')).split('|')
                while len(cond_area) > 0:
                    if cond_area[0] == '':
                        cond_area[0] = 'True'
                    self.logger.debug('explore:eval:%s' % (cond_area[0]))
                    for area in areas:
                        if eval(cond_area[0]) and not area.id in has_boss:
                            areasel.append(area)
                    cond_area = cond_area[1:]
                    if areasel != []:
                        break
                if areasel == []:
                    self.logger.info('没有符合条件的秘境www')
                    return

            area = random.choice(areasel)
            self.logger.debug('explore:area id:%s' % area.id)
            self.logger.info('选择了秘境 %s(%s%%/%s%%)' % (area.name, area.prog_area, area.prog_item))
            next_floor = 'PLACE-HOLDER'
            while next_floor:
                next_floor, msg = self._explore_floor(area, next_floor)
            if msg == EXPLORE_OK:  # 进入过秘境
                # 走形式
                if self._dopost('exploration/floor', postdata = 'area_id=%s' % (area.id))[0]['error']:
                    break
            elif msg == EXPLORE_NO_AP:
                break
            elif msg == EXPLORE_HAS_BOSS:
                has_boss.append(area.id)
            else:  # NO_FLOOR or ERROR
                break

    def _check_floor_eval(self, floors, area_race_type):
        sel_floor = []
        cond_floor = self.evalstr_floor.split('|')       
        while len(cond_floor) > 0:
            if cond_floor[0] == '':
                cond_floor[0] = 'True'
            self.logger.debug('explore:eval:%s' % (cond_floor[0]))
            for floor in floors:
                floor.cost = int(floor.cost)
                if eval(cond_floor[0]):
                    nofloorselect = False
                    sel_floor.append(floor)
            if len(sel_floor) > 0:  # 当前条件选出了地区
                break
            cond_floor = cond_floor[1:]  # 下一条件
        return len(sel_floor) == 0, sel_floor and random.choice(sel_floor) or None

    @plugin.func_hook
    def _explore_floor(self, area, floor = None):
        EXPLORE_URI = 'exploration/guild_explore' if self.loc == 'jp' else 'exploration/explore'
        EXPLORE_PARAM = 'area_id=%s&auto_build=1&auto_explore=0&floor_id=%s' if self.loc == 'jp' \
                    else 'area_id=%s&auto_build=1&floor_id=%s'
        while True:
            if floor == None or floor == 'PLACE-HOLDER':  # 没有指定
                # 选择地区
                param = 'area_id=%s' % (area.id)
                resp, ct = self._dopost('exploration/floor', postdata = param)
                if resp['error']:
                    return None, EXPLORE_ERROR
                floors = self.tolist(ct.body.exploration_floor.floor_info_list.floor_info)
                # if 'found_item_list' in floors:#只有一个
                #    floors=[floors]
                # 选择地区，结果在floor中
                nofloorselect, floor = self._check_floor_eval(floors, 0)
                if nofloorselect:
                    msg = EXPLORE_NO_FLOOR
                    break  # 更换秘境
            self.logger.info('进♂入地区 %s' % floor.id)
            if floor.type == '1':
                self.logger.info('秘境守护者出现，将使用最大卡组干掉之')
                param = 'area_id=%s&check=1&floor_id=%s' % (area.id, floor.id)
                if self._dopost('exploration/boss_floor', postdata = param)[0]['error']:
                    return None, EXPLORE_ERROR
                self._boss_battle(area_id = area.id, floor_id = floor.id)
                # 退出秘境
                break
            # 进入
            param = 'area_id=%s&check=1&floor_id=%s' % (area.id, floor.id)
            if self._dopost('exploration/get_floor', postdata = param)[0]['error']:
                return None, EXPLORE_ERROR
            # 走路
            param = EXPLORE_PARAM % (area.id, floor.id)
            while True:
                resp, ct = self._dopost(EXPLORE_URI, postdata = param)
                if resp['error']:
                    return None, EXPLORE_ERROR
                info = ct.body.explore
                self.logger.debug('explore:event_type:' + info.event_type)
                if info.event_type != '6':
                    self.logger.info('获得:%sG %sEXP, 进度:%s, 升级剩余:%s' % (info.gold, info.get_exp, info.progress, info.next_exp))
                    # 已记录1 2 3 4 5 6(AP不足) 7(打秘境守护者胜利) 12 13 15 19; 22jp = 1
                    if info.event_type == '1' or info.event_type == '22':
                        if info.event_type == '22':
                            fairy_info = ct.body.explore.ex_fairy.fairy
                            fairy_info['race_type'] = '0'
                        else:
                            fairy_info = info.fairy
                        '''<fairy>
                                <serial_id>20840184</serial_id>
                                <master_boss_id>2043</master_boss_id>
                                <hp_max>753231</hp_max>
                                <time_limit>7200</time_limit>
                                <discoverer_id>532554</discoverer_id>
                                <attacker_history></attacker_history>
                                <rare_flg>0</rare_flg>
                                <event_chara_flg>0</event_chara_flg>
                        </fairy>'''
                        fairy_info.lv, fairy_info.hp = int(fairy_info.lv), int(fairy_info.hp)
                        self.logger.info('碰到只妖精:%s lv%d hp%d' % (fairy_info.name, fairy_info.lv, fairy_info.hp))
                        self.logger.debug('sid' + fairy_info.serial_id + ' mid' + fairy_info.master_boss_id + ' uid' + fairy_info.discoverer_id)
                        if 'race_type' not in fairy_info:
                            fairy_info['race_type'] = '0'
                        if fairy_info.race_type in GUILD_RACE_TYPE:
                            self.player.fairy['guild_alive'] = True
                        else:
                            self.player.fairy.update({'id':fairy_info.serial_id, 'alive':True})
                        # evalfight=self._eval_gen(self._read_config('condition','encounter_fairy'),\
                        #    {'fairy':'info.fairy'})
                        # self.logger.debug('eval:%s result:%s'%(evalfight,eval(evalfight)))
                        # if eval(evalfight):
                        self.logger.sleep('3秒后开始战斗www')
                        time.sleep(3)
                        self._fairy_battle(fairy_info, bt_type = EXPLORE_BATTLE)
                        time.sleep(5.5)
                        if self._check_floor_eval([floor], fairy_info.race_type)[0]:  # 若已不符合条件
                            return None, EXPLORE_OK
                        # 回到探索界面
                        if self._dopost('exploration/get_floor',
                            postdata = 'area_id=%s&check=1&floor_id=%s' % (area.id, floor.id)
                            )[0]['error']:
                            return None, EXPLORE_ERROR
                    elif info.event_type == '2':
                        self.logger.info('碰到个傻X：{0} -> {1}'.format(info.encounter.name, info.message).replace('%', '%%'))
                        time.sleep(1.5)
                    elif info.event_type == '3':
                        usercard = info.user_card
                        self.logger.debug('explore:cid %s sid %s' % (usercard.master_card_id, usercard.serial_id))
                        self.logger.info('获得了 %s %s' % (self.carddb[int(usercard.master_card_id)][0],
                            '☆' * self.carddb[int(usercard.master_card_id)][1]))
                    elif info.event_type == '15':
                        if self.loc == 'jp':
                            compcard = info.autocomp_card.base_card
                            self.logger.info('合成了 %s lv%s exp%s%%' % (
                                self.carddb[int(compcard.master_card_id)][0],
                                compcard.lv,
                                compcard.exp_per))
                        else:
                            compcard = info.autocomp_card[-1]
                            # self.logger.debug('explore:cid %s sid %s' % (
                            #     compcard.master_card_id,
                            #     compcard.serial_id))
                            self.logger.info('合成了 %s lv%s exp%s nextexp%s' % (
                                self.carddb[int(compcard.master_card_id)][0],
                                compcard.lv,
                                compcard.exp,
                                compcard.next_exp))
                    elif info.event_type == '5':
                        self.logger.info('AREA %s CLEAR -v-' % floor.id)
                        time.sleep(2)
                        if 'next_floor' in info:
                            next_floor = info.next_floor.floor_info
                            return next_floor, EXPLORE_OK
                        else:
                            if 'bonus_list' in ct.body:
                                msgs = self.tolist(ct.body.bonus_list.message)
                                bns = self.tolist(ct.body.bonus_list.bonus)
                                rwds = []
                                msg = ""
                                for b in range(len(bns)):
                                    if bns[b].type == '1' and not self.cfg_auto_fairy_rewards:#借用一下吧ww
                                        continue
                                    msg += '%s:%s , ' % (msgs[b].value ,self._parse_reward(bns[b]))
                                    rwds.append(bns[b].id)
                                self.logger.info(msg.rstrip(' , '))
                                self._get_rewards(rwds)
                            return None, EXPLORE_OK
                    elif info.event_type == '12':
                        self.logger.info('AP回复[%s]~' % info.recover)
                    elif info.event_type == '13':
                        self.logger.info('BC回复[%s]~' % info.recover)
                    elif info.event_type == '19':
                        try:
                            itemid = info.special_item.item_id
                        except KeyError:
                             self.logger.debug('explore:item not found?')
                        else:
                            itembefore = int(info.special_item.before_count)
                            itemnow = int(info.special_item.after_count)
                            self.logger.debug('explore:itemid:%s' % (itemid))
                            self.logger.info('获得收集品[%s] x%d' % (self.player.item.get_name(int(itemid)), itemnow - itembefore))
                    elif info.event_type == '4':
                        self.logger.info('获得了因子碎片 湖:%s 碎片:%s' % (
                            info.parts_one.lake_id, info.parts_one.parts.parts_num))
                        if int(resp['content-length']) > 10000:
                            self.logger.info('收集碎片合成了新的骑士卡片！')
                    elif info.event_type != '0':
                        self.logger.warning('unrecognized event_type:%s' % info.event_type)
                else:
                    self.logger.warning('AP不够了TUT')
                    # 先半绿，再大绿
                    if not self.green_tea(self.cfg_auto_explore, tea = HALF_TEA, noerror = True) and \
                        not self.green_tea(self.cfg_auto_explore):
                        self.logger.error('不给喝，不走了o(￣ヘ￣o＃) ')
                        return None, EXPLORE_NO_AP
                    else:
                        if self._check_floor_eval([floor], 0)[0]:  # 若已不符合条件
                            return None, EXPLORE_NO_AP
                        continue
                if info.lvup == '1':
                    self.logger.info('升级了：↑%s' % self.player.lv)
                    time.sleep(3)
                # if info.progress=='100':
                #     break
                time.sleep(int(self._read_config('system', 'explore_sleep')))
        return None, EXPLORE_OK
                # print '%s - %s%% cost%s'%\
                    # (floors[i].id,floors[i].progress,floors[i].cost)

    @plugin.func_hook
    def _boss_battle(self, area_id = None, floor_id = None):
        if not (area_id and floor_id):
            return False
        self.set_card('auto_set', aim = maclient_smart.MAX_DMG, maxline = 4, seleval = 'card.lv>45', test_mode = False, bclimit = BC_LIMIT_MAX, fast_mode = True, save2deck = None)
        param = "area_id=%s&floor_id=%s" % (area_id, floor_id)
        resp, ct = self._dopost('exploration/battle', postdata = param)
        if resp['error']:
            return False
        if ct.body.battle_result.winner == '1':
            self.logger.info('战斗胜利o(*￣▽￣*)o ')
            return True
        else:
            self.logger.info('输了呢Σ( ° △ °|||)︴ ')
            return False

    @plugin.func_hook
    def gacha(self, gacha_type = GACHA_FRIENNSHIP_POINT):
        if gacha_type == GACHA_FRIENNSHIP_POINT:
            ab = self.cfg_auto_build
            bulk = self.cfg_fpgacha_buld
        else:
            ab = '0'
            bulk = '0'
        if self._dopost('gacha/select/getcontents')[0]['error']:
            return
        self.logger.debug("gacha:auto_build:%s bulk:%s product_id:%d" % (ab, bulk, gacha_type))
        param = "auto_build=%s&bulk=%s&product_id=%d" % (ab, bulk, gacha_type)
        resp, ct = self._dopost('gacha/buy', postdata = param)
        if resp['error']:
            return
        gacha_buy = ct.body.gacha_buy
        excards = self.tolist(gacha_buy.final_result.ex_user_card)
        excname = []
        # if 'is_new_card' in excards:#只有一个
        #    excards=[excards]
        for card in excards:
            try:
                mid = self.player.card.sid(card.serial_id).master_card_id
            except IndexError:
                self.logger.debug('gacha:没找到卡片，刚被卖了？')
                excname.append('?')
                continue
            if gacha_type > GACHA_FRIENNSHIP_POINT:
                rare = ['R', 'R+', 'SR', 'SR+','MR']
                rare_str = ' ' + rare[self.carddb[int(mid)][1] - 3]
            else:
                rare = ['', '', '', 'R+', 'SR', 'SR+','MR']
                rare_str = ' %s' % (rare[self.carddb[int(mid)][1] - 1])
            excname.append('[%s]%s%s%s' % (
                self.carddb[int(mid)][0],
                self.player.card.sid(card.serial_id).holography == '1' and '(闪)' or '',
                rare_str,
                card.is_new_card =='1' and ' NEW' or ''
            ))

        self.logger.info('获得%d张新卡片: %s' % (len(excname), ', '.join(excname)))
        self.player.friendship_point = self.player.friendship_point - 200 * len(excname)
        if ab == '1' and 'auto_compound' in gacha_buy:
            try:
                autocname = []
                for card in self.tolist(gacha_buy.auto_compound.compound):
                    mid = card.base_card.master_card_id
                    autocname.append('[%s]Lv%s' % (self.carddb[int(mid)][0], card.base_card.lv))
                self.logger.info('合成了%d张新卡片: %s' % (len(autocname), ', '.join(autocname)))
            except:
                self.logger.debug('gacha:no auto build')
        time.sleep(7.3890560964)

    def _get_rewards(self, notice_id):
        hasgot = False
        if not notice_id:
            return False,  None
        while len(notice_id) > 0:
            # 一次20个
            if len(notice_id) > 20:
                self.logger.debug('_get_rewards:too many rewards (%d)' % (len(notice_id)))
                no_id = notice_id[:20]
            else:
                no_id = notice_id
            notice_id = notice_id[len(no_id):]
            param = "notice_id=%s" % (','.join(no_id))
            resp, ct = self._dopost('menu/get_rewards', postdata = param)
            if not resp['error'] or resp['errno'] == 8000:
                self.logger.debug('_get_rewards:get successfully.')
                hasgot = True
            else:
                break
        return hasgot, resp['errmsg']

    @plugin.func_hook
    def select_card_sell(self, cond = ''):
        cinfo = []
        sid = []
        warning_card = []
        self.logger.debug('select_card:eval:%s' % (self.evalstr_selcard))
        for card in self.player.card.cards:
            card.star = int(self.carddb[int(card.master_card_id)][1])
            evalres = eval(self.evalstr_selcard) and not card.master_card_id in [390, 391, 392, 404]  # 切尔莉
            if evalres:
                if card.star > 3:
                    warning_card.append('%s lv%d %s' % (
                        self.carddb[int(card.master_card_id)][0],
                        card.lv,
                        '☆' * self.carddb[int(card.master_card_id)][1])
                    )
                sid.append(card.serial_id)
                cinfo.append('%s lv%d %s' % (
                    self.carddb[int(card.master_card_id)][0],
                    card.lv,
                    '☆' * self.carddb[int(card.master_card_id)][1])
                )
        if len(sid) == 0:
            self.logger.info('没有要贩卖的卡片')
        else:
            self.logger.info('将要贩卖这些卡片：%s' % (', '.join(cinfo)))
        if len(warning_card) > 0:
            if self.cfg_sell_card_warning >= 1:
                self.logger.warning('存在稀有以上卡片：%s\n真的要继续吗？y/n' % (', '.join(warning_card)))
                if raw_inputd('> ') != 'y':
                    self.logger.debug('select_card:user aborted')
                    return False
        else:
            if self.cfg_sell_card_warning == 2:
                self.logger.warning('根据卖卡警告设置，需要亚瑟大人的确认\n真的要继续吗？y/n')
                if raw_inputd('> ') != 'y':
                    self.logger.debug('select_card:user aborted')
                    return False
        return self._sell_card(sid)

    def _sell_card(self, serial_id):
        if serial_id == []:
            self.logger.debug('sell_card:no cards selected')
            return False
        if self._dopost('card/exchange', postdata = 'mode=1')[0]['error']:
            return False
        serial_id = map(str, serial_id)  # to string
        while len(serial_id) > 0:
            # >30张要分割
            if len(serial_id) > 30:
                self.logger.debug('_sell_card:too many cards (%d)' % (len(serial_id)))
                se_id = serial_id[:30]
            else:
                se_id = serial_id
            serial_id = serial_id[len(se_id):]
            # 卖
            paramsell = 'serial_id=%s' % (','.join(se_id))
            slp = random.random() * 4 + len(se_id) * 0.6 + 2
            self.logger.sleep('%f秒后卖卡……' % slp)
            time.sleep(slp)
            resp, ct = self._dopost('trunk/sell', postdata = paramsell)
            if not resp['error']:
                self.logger.info('%s(%d张卡片)' % (resp['errmsg'], len(se_id)))
        return True

    @plugin.func_hook
    def fairy_battle_loop(self, ltime = None):
        if ltime != None and ltime != '':
            looptime = ltime
        else:
            looptime = self._read_config('system', 'fairy_battle_times')
        if looptime == '0' or looptime == '':
            looptime = '9999999'
        looptime = int(looptime)
        slpfactor = float(self._read_config('system', 'fairy_battle_sleep_factor') or '1')
        # if slptime=='':
        #    slptime=1.5
        secs = self._read_config('system', 'fairy_battle_sleep').split('|')
        hour_last = 25
        refresh = False
        for l in xrange(looptime):
            hour_now = datetime.datetime.now().hour
            if hour_now != hour_last:
                slptime = 1.5
                for s in secs:
                    low, up, t = s.split(',')
                    if hour_now in xrange(int(low), int(up)):
                        slptime = float(t)
                        break
                if slptime * slpfactor * 60 < 20:
                    self.logger.warning('间隔至少为20秒，但当前设置为%d' % (slptime * 60))
                    slptime = 1.0 / 3 / slpfactor
                hour_last = hour_now
            self.logger.debug('fairy_battle_loop:%d/%d' % (l + 1, looptime))
            self.fairy_select()
            if looptime != l + 1:  # 没有立即刷新
                s = random.randint(int(60 * slptime * 0.8 * slpfactor), int(60 * slptime * 1.2 * slpfactor))
                self.logger.sleep('%d秒后刷新……' % s)
                time.sleep(s)

    @plugin.func_hook
    def fairy_select(self, cond = '', carddeck = None):
        FAIRY_SELECT_URI = 'private_fairy/private_fairy_select' if self.loc == 'jp' else 'menu/fairyselect'
        # 走个形式
        resp, ct = self._dopost('menu/menulist')
        if resp['error']:
            return
        time.sleep(1.2)
        resp, ct = self._dopost('mainmenu', no2ndkey = True)
        if resp['error']:
            return
        if ct.header.your_data.fairy_appearance != '1':  # 没有“妖精出现中”
            if self.player.fairy['alive'] or  self.player.fairy['guild_alive']:
                self.player.fairy = {'alive':False, 'id':0, 'guild_alive':False}
            return
        time.sleep(0.8)
        resp, ct = self._dopost(FAIRY_SELECT_URI)
        if resp['error']:
            return
        fs = ct.body.fairy_select
        fairy_event = self.tolist(fs.fairy_event)
        # 领取妖精奖励
        if fs.remaining_rewards != '0':
            if self.cfg_auto_fairy_rewards:
                self._fairy_rewards()
            else:
                self.logger.debug('fairy_select:do not get rewards')
        else:
            self.logger.debug('fairy_select:no rewards')
        # 清理记录
        fsids = [f.fairy.serial_id for f in fairy_event]
        for fsid in self._list_option('fairy'):
            if int(self._read_config('fairy', fsid).split(',')[0]) < time.time() or not fsid in fsids:
                self.logger.debug('fairy_select:delete sid %s from record' % (fsid))
                self._del_option('fairy', fsid)
        # 筛选
        # 先置为已挂了
        fitemp = self.player.fairy['id']
        self.player.fairy = {'alive':False, 'id':0, 'guild_alive':False}
        evalstr = (cond != '' and self._eval_gen(cond, eval_fairy_select, 'fairy') or self.evalstr_fairy)
        #self.logger.debug('fairy_select:eval:%s' % (evalstr))
        fairies = []
        token = os.urandom(8)
        if self.loc == 'jp':
            self.plugin.set_extras(token, 'fairy_event', [f for f in fairy_event if f.put_down == '5'])
        for fairy in fairy_event:
            # 挂了
            if fairy.put_down not in '014':# 1战斗中 2胜利 3失败 4 0BC 5 可赞的
                continue
            fairy.fairy.lv = int(fairy.fairy.lv)
            # (sid相同，或未记录的)且不是公会妖
            if self.loc == 'jp':
                fairy['user'] = object_dict()
                fairy.user['id'] = fairy.fairy.discoverer_id
                fairy.fairy['race_type'] =  0#日服没有工会
            if (fitemp == fairy.fairy.serial_id or fairy.user.id == self.player.id) and fairy.fairy.race_type not in GUILD_RACE_TYPE:
                self.player.fairy.update({'alive':True, 'id':fairy.fairy.serial_id})
            elif fairy.fairy.race_type in GUILD_RACE_TYPE:
                self.player.fairy['guild_alive'] = True
            fairy['time_limit'] = int(fairy.fairy.time_limit)
            fairy['wake'] = re.search(self.player.boss.name_wake, raw_du8(fairy.fairy.name)) != None
            fairy['wake_rare'] = re.search(maclient_smart.name_wake_rare, raw_du8(fairy.fairy.name)) != None
            ftime = (self._read_config('fairy', fairy.fairy.serial_id) + ',,').split(',')
            fairy.fairy['not_battled'] = ftime[0] == ''
            # self.logger.debug('b%s e%s p%s'%(not fairy['not_battled'],eval(evalstr),fairy.put_down))
            if eval(evalstr):
                # if time.time() - int(ftime[1] or '0') < 180 and cond == '':  # 若手动选择则不受3min限制
                #     self.logger.debug('fairy_select:sid %s battled in less than 3 min' % fairy.fairy.serial_id)
                #     continue
                fairies.append(fairy)
        self.logger.info(len(fairies) == 0 and '木有符合条件的妖精-v-' or '符合条件的有%d只妖精XD' % len(fairies))
        # 依次艹
        for f in fairies:
            self.logger.debug('fairy_select:select sid %s%s%s' % (
                f.fairy.serial_id,
                '' if f.fairy.not_battled else ' battled',
                ' wake' if f.wake else ''))
            f.fairy.discoverer_id = f.user.id
            self._fairy_battle(f.fairy, bt_type = NORMAL_BATTLE, carddeck = carddeck)
            # 走个形式
            resp, ct = self._dopost('menu/fairyselect')
            if resp['error']:
                return
            time.sleep(1.25)
            # fairy.user.name,fairy.fairy.name,fairy.fairy.serial_id,fairy.fairy.lv,fairy.put_down
            # fairy.start_time,fairy.fairy.time_limit

    def _fairy_rewards(self):
        if self.loc == 'jp':
            resp, ct = self._dopost('private_fairy/private_fairy_rewards')
            return
        resp, ct = self._dopost('menu/fairyrewards')
        if resp['errno'] == 8000:
            pass  # self.logger.warning(resp['errmsg'])
        elif resp['error']:
            return
        fw = ct.body.fairy_rewards
        if 'reward_details' in fw:
            rws = self.tolist(fw.reward_details)
            # if 'fairy' in rws:#只有一个
            #    rws=[rws]
            rwname = []
            for rw in rws:
                rwname.append(rw.item_name)
            self.logger.info('%s  已获得' % (', '.join(rwname)))

    @plugin.func_hook
    def _fairy_battle(self, fairy, bt_type = NORMAL_BATTLE, carddeck = None):
        FAIRY_FLOOR_URI = 'private_fairy/private_fairy_top' if self.loc == 'jp' else 'exploration/fairy_floor'
        FAIRY_FLOOR_PARAM = '%sserial_id=%s&user_id=%s' if self.loc == 'jp' else 'check=1&%sserial_id=%s&user_id=%s'
        FAIRY_BATTLE_URI = 'private_fairy/private_fairy_battle' if self.loc == 'jp' else 'exploration/fairybattle'
        #jp no -> carddeck number
        FAIRY_BATTLE_PARAM = 'no=0&%sserial_id=%s&user_id=%s' if self.loc == 'jp' else '%sserial_id=%s&user_id=%s'
        
        while time.time() - self.lastfairytime < 18 and 'race_type' in fairy and fairy.race_type != GUILD_RACE_TYPE:
            self.logger.sleep('等待战斗冷却')
            time.sleep(5)
        def fairy_floor(f = fairy):
            paramfl = FAIRY_FLOOR_PARAM % (
                'race_type' in fairy and ('race_type=%s&' % fairy.race_type) or '',
                f.serial_id, f.discoverer_id)
            resp, ct = self._dopost(FAIRY_FLOOR_URI, postdata = paramfl)
            if resp['error']:
                return None
            else:
                if self.loc == 'jp':
                    if 'recover_by_like' in ct.body.private_fairy_top:
                        self.logger.info('收到点赞回复BC%s点' % ct.body.private_fairy_top.recover_by_like.recover_point)
                    return ct.body.private_fairy_top.private_fairy.fairy
                else:
                    return ct.body.fairy_floor.explore.fairy
        if bt_type == NORMAL_BATTLE or bt_type == TAIL_BATTLE:
            # 列表打开时，传入的fairy只有部分信息，因此客户端都会POST一个fairy_floor来取得完整信息
            # 尾刀需要重新获得妖精血量等
            # 包含了发现者，小伙伴数量，剩余血量等等s
            fairy = fairy_floor()
            if not fairy:
                return False
        # 已经挂了
        if fairy.hp == '0':
            self.logger.warning('妖精已被消灭')
            if fairy.serial_id == self.player.fairy['id']:
                self.player.fairy.update({'id':0, 'alive':False})
            elif 'race_type' in fairy and fairy.race_type in GUILD_RACE_TYPE:
                self.player.fairy['guild_alive'] = False
            return False
        fairy['lv'] = int(fairy.lv)
        fairy['hp'] = int(fairy.hp)
        fairy['time_limit'] = int(fairy.time_limit)
        fairy['wake_rare'] = False
        if 'not_battled' not in fairy:
            ftime = (self._read_config('fairy', fairy.serial_id) + ',,').split(',')
            fairy['not_battled'] = ftime[0] == ''
        fairy['wake_rare'] = re.match(maclient_smart.name_wake_rare, raw_du8(fairy.name)) != None
        fairy['wake'] = fairy.rare_flg == '1' or fairy['wake_rare']
        disc_name = ''
        disc_id = fairy.discoverer_id
        # if self.loc == 'jp':
        #     fairy['race_type'] =  0#日服没有工会
        if disc_id == self.player.id:
            disc_name = self.player.name
        if self.loc == 'jp':
            f_attackers = []#手动获得历史了？
        elif 'attacker' not in fairy.attacker_history:  # 没人打过的
            f_attackers = []
        else:
            f_attackers = self.tolist(fairy.attacker_history.attacker)
            # #只有一个的情况
            # if 'user_id' in fairy.attacker_history.attacker:
            #    fairy.attacker_history.attacker=[fairy.attacker_history.attacker]
            if not disc_name:#不是我的
                for atk in f_attackers:
                    if atk.discoverer == '1' or atk.user_id == disc_id:#preserve for guild fairy
                        disc_name = atk.user_name
                        break
            #if not disc_name and 'race_type' in fairy:
            #    if fairy.race_type == '12':#找不到
            #        disc_name = '公会妖精'
        hms = lambda x:x >= 3600 and time.strftime('%H:%M:%S', time.localtime(x + 16 * 3600)) or time.strftime('%M:%S', time.localtime(x))
        self.logger.info('妖精:%sLv%d hp:%d 发现者:%s 小伙伴:%d 剩余%s%s%s' % (
            fairy.name, fairy.lv, fairy.hp, disc_name,
            len(f_attackers), hms(fairy.time_limit),
            ('race_type' in fairy and fairy.race_type in GUILD_RACE_TYPE) and ' 公会' or '',
            fairy.wake and ' WAKE!' or ''))
        if carddeck:
            cardd = carddeck
            self.logger.debug('fairy_battle:carddeck override:%s' % (cardd))
        else:
            cardd = eval(self.evalstr_fairy_select_carddeck)
            self.logger.debug('fairy_battle:carddeck result:%s' % (cardd))
        if cardd == 'abort':
            self.logger.debug('fairy_battle:abort battle sequence.')
            return False
        elif cardd == 'letitgo':
            self.logger.sleep('坐等%d分钟后妖精逃跑' % (int(fairy.time_limit) / 60))
            time.sleep(int(fairy.time_limit))
            # 如果是自己的妖精则设为死了
            if fairy.serial_id == self.player.fairy['id']:
                self.player.fairy.update({'id':0, 'alive':False})
            # 如果是公会妖精则设为死了
            elif 'race_type' in fairy and fairy.race_type in GUILD_RACE_TYPE:
                self.player.fairy['guild_alive'] = False
            return False
        _has_set, _last_bc = self.set_card(cardd, cur_fairy = fairy)
        if _last_bc == -1:#自动配卡出错或卡组不存在
            _has_set, _last_bc = self.set_card('min')
        if _has_set:
            fairy = fairy_floor()  # 设完卡组返回时
            if not fairy:
                return False
        # 判断BC
        if self.check_strict_bc(cost = _last_bc) or self.player.bc['current'] < 2:  # strict BC或者BC不足
            self.logger.warning('BC不够了TOT')
            autored = (self.cfg_auto_rt_level == 2) or (self.cfg_auto_rt_level == 1 and fairy.rare_flg == '1')
            if autored:
                if self.cfg_auto_choose_red_tea and \
                self.player.item.get_count(getattr(maclient_smart, 'half_bc_offset_%s' % self.loc[:2]) + 2) > 0:
                    if _last_bc > (self.player.bc['max'] / 2 + self.player.bc['current']):#半瓶不够
                        _tea = FULL_TEA
                    else:
                        _tea = HALF_TEA
                else:
                    _tea = FULL_TEA
                if not self.red_tea(silent = True, tea = _tea):
                    self.logger.error('那就不打了哟(*￣︶￣)y ')
                    return False
            else:
                return False
        # 打
        nid = []
        rare_fairy = None
        need_tail = False
        win = False
        self.lastfairytime = time.time()
        savet = (cardd == 'min')
        #race_type?
        paramf =  FAIRY_BATTLE_PARAM % (
            'race_type' in fairy and ('race_type=%s&' % fairy.race_type) or '',
            fairy.serial_id, fairy.discoverer_id)
        resp, ct = self._dopost(FAIRY_BATTLE_URI, postdata = paramf, savetraffic = savet)
        if len(ct) == 0:
            self.logger.info('舔刀卡组，省流模式开启')
        else:
            if resp['error']:
                return
            elif resp['errno'] == 1050:
                self.logger.warning('BC不够了TOT')
                autored = (self.cfg_auto_rt_level == '2') or (self.cfg_auto_rt_level == '1' and fairy.rare_flg == '1')
                if autored:
                    if not self.red_tea(True):
                        self.logger.error('那就不打了哟(*￣︶￣)y ')
                        return False
                else:
                    return False
            try:
                res = ct.body.battle_result
            except KeyError:
                self.logger.warning('没有发现战斗结果，妖精已经挂了？')
                if fairy.serial_id == self.player.fairy['id']:
                    self.player.fairy.update({'id':0, 'alive':False})
                elif 'race_type' in fairy and fairy.race_type in GUILD_RACE_TYPE:
                    self.player.fairy['guild_alive'] = False
                return False
            # 通知远程
            # self.remoteHdl(method='FAIRY',fairy=fairy)
            # 战斗结果
            # 测试！
            # if os.path.exists('debug') and cardd!='min':
            #   open('debug/%slv%s_%s.xml'%(fairy.name,fairy.lv,fairy.serial_id),'w').write(ct)
            if res.winner == '1':  # 赢了
                win = True
                self.logger.info('YOU WIN 233')
                # if bt_type!=NORMAL_BATTLE:#探索中遇到的、打死变成觉醒后的和尾刀的
                #     self.player.fairy={'id':0,'alive':False}
                # 觉醒
                body = ct.body
                if 'rare_fairy' in body.explore:
                    rare_fairy = body.explore.rare_fairy
                # 奖励
                bonus = body.bonus_list.bonus
                for b in bonus:
                    # type 1:卡片 2:道具 3:金 4:绊点 5:蛋卷
                    if b.type == '1':#卡片
                        # self.logger.debug('fairy_battle:type:%s card_id %s holoflag %s'%(b.type,b.card_id,b.holo_flag))
                        self.logger.info('获得卡片 %s%s' % (self.carddb[int(b.card_id)][0], (b.holo_flag == '1' and '(闪)' or '')))
                    else:
                        nid.append(b.id)
                        if b.type == '2':
                            # 收集品 情况1：要通过点击“立即领取”领取的，在sleep之后领取
                            # 没有考虑日服，res.private_fairy_reward_list.reward_item_list[item_id, item_count]
                            # self.logger.debug('fairy_battle:type:%s item_id %s count %s'%(b.type,b.item_id,b.item_num))
                            if int(b.item_id) <= 3:
                                self.logger.info('获得物品[%s] x%s' % (self.player.item.get_name(int(b.item_id)), b.item_num))
                            else:
                                self.logger.info('获得收集品[%s] x%s' % (self.player.item.get_name(int(b.item_id)), b.item_num))
                        elif b.type == '3':
                            self.logger.info('获得金币 %s' % b.get_money)
                        elif b.type == '4':
                            self.logger.info('获得绊点 %s' % b.get_point)
                        elif b.type == '5':
                            self.logger.info('获得蛋蛋卷')#我猜的
                        else:
                            self.logger.warning('未识别的奖励类型:%s' % b.type)
                # 如果是自己的妖精则设为死了
                if fairy.serial_id == self.player.fairy['id']:
                    self.player.fairy.update({'id':0, 'alive':False})
                # 如果是公会妖精则设为死了
                elif 'race_type' in fairy and fairy.race_type in GUILD_RACE_TYPE:
                    self.player.fairy['guild_alive'] = False
            else:  # 输了
                hpleft = int(ct.body.explore.ex_fairy.fairy.hp) if self.loc == 'jp' else int(ct.body.explore.fairy.hp)
                self.logger.info('YOU LOSE- - Fairy-HP:%d' % hpleft)
                # 立即尾刀触发,如果补刀一次还没打死，就不打了-v-
                if self.cfg_fairy_final_kill_hp >= hpleft and (not bt_type == TAIL_BATTLE or hpleft < 5000):
                    need_tail = True
            # 金币以及经验
            self.logger.info('EXP:+%d(%s) G:+%d(%s)' % (
                int(res.before_exp) - int(res.after_exp),
                res.after_exp,
                int(res.after_gold) - int(res.before_gold),
                res.after_gold
            ))
            # 是否升级
            if not res.before_level == res.after_level:
                self.logger.info('升级了：↑%s' % res.after_level)
            # 收集品 情况2：自动往上加的
            if 'special_item' in res or (self.loc == 'jp' and 'special_item' in res.private_fairy_reward_list):
                if self.loc == 'jp':
                    it = res.private_fairy_reward_list.special_item
                else:
                    it = res.special_item
                self.logger.info('收集品[%s]:+%d(%s)' % (\
                    self.player.item.get_name(int(it.item_id)), int(it.after_count) - int(it.before_count), it.after_count))
            # 战斗详情分析
            # <battle_action_list>
            #     <action_player>0</action_player>
            #     <skill_id>208</skill_id>
            #     <skill_type>2</skill_type>
            #     <skill_card>604</skill_card>
            #     <skill_hp_player>3240</skill_hp_player>
            #     <attack_card>604</attack_card>
            #     <attack_type>1</attack_type>
            #     <attack_damage>11967</attack_damage>
            # </battle_action_list>
            if cardd != 'min':
                fatk, matk, satk, rnd = 0, 0, 0, 0
                skills = []
                cbos = []
                skill_type = ['0', 'ATK↑', 'HP↑', '3', '4', '5']
                blist = ct.body.battle_battle.battle_action_list
                token = os.urandom(8)
                self.plugin.set_extras(token, 'battle_result', blist)
                self.plugin.set_extras(token, 'battle_player', ct.body.battle_battle.battle_player_list)
                try:
                    for l in blist:
                        if 'turn' in l:  # 回合数
                            rnd = float(l.turn) - 0.5
                        else:
                            if 'attack_damage' in l:  # 普通攻击
                                if l.action_player == '0':  # 玩家攻击
                                    matk += int(l.attack_damage)
                                else:  # 妖精攻击
                                    fatk += int(l.attack_damage)
                                    rnd += 0.5  # 妖精回合
                                if l.attack_type not in '12':
                                    self.logger.debug('fairy_battle%satk_type%s' % (_for_debug, l.attack_type))
                            if 'special_attack_damage' in l:  # SUPER
                                satk = int(l.special_attack_damage)
                                if l.special_attack_id != '1':  # 和阵营有关？
                                    self.logger.debug('fairy_battle%ssatk_id%s dmg%s' % (_for_debug, l.special_attack_id, l.special_attack_damage))
                            if 'skill_id' in l:
                                # skillcnt+=1
                                skill_var = l.skill_type == '1' and l.attack_damage or l.skill_hp_player
                                skills.append('[%d]%s(%s).%s' % (
                                    math.ceil(rnd), skill_type[int(l.skill_type)], skill_var, self.carddb[int(l.skill_card)][0])
                                )
                            if 'combo_name' in l:
                                cbos.append('%s.%s' % (
                                    skill_type[int(l.combo_type)] + ('' if l.combo_hp_player == '0' else l.combo_hp_player),
                                    l.combo_name)
                                )
                except:
                    self.logger.warning('提取战斗详情时遇到了奇怪的问题:\n%s' %
                        "".join(traceback.format_exception(*sys.exc_info()))
                    )
                else:
                    self.logger.info('战斗详情:\nROUND:%d/%d 平均ATK:%.1f/%.1f%s %s %s %s' %
                        (math.ceil(rnd), math.floor(rnd),
                        matk / math.ceil(rnd), 0 if rnd < 1 else fatk / math.floor(rnd),
                        ' SUPER:%d' % satk if satk > 0 else '',
                        res.winner == '1' and '受到伤害:%d' % fatk or '总伤害:%d' % matk,
                        len(cbos) > 0 and '\nCOMBO:%s' % (','.join(cbos)) or '',
                        len(skills) > 0 and '\nSKILL:%s' % (','.join(skills)) or '')
                    )
                
        # 记录截止时间，上次战斗时间，如果需要立即刷新，上次战斗时间为0.1
        self._write_config('fairy', fairy.serial_id,
            '%d,%.0f' % (int(fairy.time_limit) + int(float(time.time())), time.time()))
        # 等着看结果
        time.sleep(random.randint(8, 15))
        # 领取收集品
        if nid != []:
            res = self._get_rewards(nid)
            if not res[0]:
                self.logger.warning(res[1])
        # 立即尾刀
        if need_tail:
            self.logger.debug('fairy_battle:tail battle!')
            self._fairy_battle(fairy, bt_type = TAIL_BATTLE)
        # 接着打醒妖:
        if rare_fairy != None:
            rare_fairy = fairy_floor(f = rare_fairy)  #
            self.logger.warning('WARNING WARNING WARNING WARNING WARNING')
            self.logger.info('妖精真正的力量觉醒！'.center(39))
            self.logger.warning('WARNING WARNING WARNING WARNING WARNING')
            time.sleep(3)
            if 'race_type' in rare_fairy and rare_fairy.race_type in GUILD_RACE_TYPE:
                self.player.fairy['guild_alive'] = True
            else:
                self.player.fairy.update({'alive':True, 'id':rare_fairy.serial_id})
            self._fairy_battle(rare_fairy, bt_type = WAKE_BATTLE)
        # 输了，
        if not win:
            # 回到妖精界面; 尾刀时是否回妖精界面由尾刀决定，父过程此处跳过
            if not need_tail:
                fairy_floor()
             # 如果是醒妖且不是公会妖则问好
            if bt_type == WAKE_BATTLE and 'race_type' in fairy and fairy.race_type not in GUILD_RACE_TYPE and self.cfg_auto_greet :
                self.like()

    @plugin.func_hook
    def like(self, words = '你好！'):
        if words == '':
            words = self.cfg_greet_words
        words = words.encode('utf-8')
        # os._exit(0)
        resp, ct = self._dopost('menu/friendlist', postdata = 'move=0')
        if resp['error']:
            return
        uids = []
        for u in self.tolist(ct.body.friend_list.user):
            uids.append(u.id)
        resp, ct = self._dopost('friend/like_user', postdata = ('dialog=1&user_id=%s' % ','.join(uids)))
        if resp['error']:
            return
        body = ct.body
        if body.friend_act_res.success != '1':
            self.logger.error(body.friend_act_res.message)
            return
        else:
            self.logger.info(body.friend_act_res.message)
        if len(body.friend_comment_id.comment_id) == 1:
            comment_ids = [body.friend_comment_id.comment_id]
        else:
            comment_ids = []
            for cmid in body.friend_comment_id.comment_id:
                comment_ids.append(cmid.value)
        resp, ct = self._dopost('comment/send', postdata = ('comment_id=%s&like_message=%s&user_id=%s' %
            (','.join(comment_ids), words, ','.join(uids))
            ))
        if resp['error']:
            return
        self.logger.info(ct.header.error.message)
        # 走个形式
        resp, ct = self._dopost('menu/friendlist', postdata = 'move=0')
        resp, ct = self._dopost('menu/menulist')
        return True

    @plugin.func_hook
    def friends(self, choice = '', autodel = False):
        delfriend = int(self._read_config('tactic', 'del_friend_day') or '5')
        loop = 999
        lastmove = 0
        while loop - 1 > 0:
            loop -= 1
            if choice == '':
                print(du8('选择操作\n1.删除好友\n2.查找添加好友\n3.处理好友邀请\n4.返回'))
                choice = raw_inputd('> ')
            else:
                loop = 1
            if choice == '1':
                resp, ct = self._dopost('menu/friendlist', postdata = 'move=0')
                lastmove = 1
                if resp['error']:
                    return
                try:
                    users = self.tolist(ct.body.friend_list.user)
                except KeyError:
                    users = []
                # else:
                #    if 'name' in users:#只有一个
                #        users=[users]
                strf = '已有好友个数：%d\n' % len(users)
                i = 1
                deluser = None
                maxlogintime = 0
                for user in users:
                    strf += '%d.%s\t最后上线:%s  LV:%s  BC:%s\n' % (
                        i, user.name, user.last_login, user.town_level, user.cost
                    )
                    try:
                        user.logintime = int(user.last_login[:-1])
                    except UnicodeEncodeError:
                        if user.last_login.endswith('月前'):
                            user.logintime = 31
                        else :
                            user.logintime = 0
                    if user.logintime >= delfriend and user.logintime >= maxlogintime:
                        deluser = user
                        maxlogintime = user.logintime
                    i += 1
                print(du8(strf))
                confirm = False
                if deluser != None:
                    if not autodel:
                        self.logger.warning('即将删除%d天以上没上线的：%s 最后上线:%s ID:%s' % (
                            delfriend, deluser.name, deluser.last_login, deluser.id
                        ))
                        if raw_inputd('y/n >') == 'y':
                            confirm = True
                else:
                    u = raw_inputd('没有要删除的好友\n输入序号可以手动删除好友，按回车返回> ')
                    if not u:
                        pass
                    elif not u.isdigit():
                        self.logger.warning('输入"%s"非数字' % u)
                    else:
                        deluser = users[int(u) - 1]
                        if not autodel:
                            self.logger.warning('即将删除：%s 最后上线:%s ID:%s' % (
                                deluser.name, deluser.last_login, deluser.id
                            ))
                            if raw_inputd('y/n >') == 'y':
                                confirm = True
                if autodel or confirm:
                    param = 'dialog=1&user_id=%s' % deluser.id
                    resp, ct = self._dopost('friend/remove_friend', postdata = param)
                    self.logger.info(resp['errmsg'])
            elif choice == '3':
                lastmove = 3
                resp, ct = self._dopost('menu/friend_notice', postdata = 'move=0')
                if resp['error']:return
                try:
                    users = self.tolist(ct.body.friend_notice.user_list.user)
                except KeyError:
                    users = []
                # else:
                #    if 'name' in users:#只有一个
                #        users=[users]
                i = 1
                strf = ''
                for user in users:
                    strf += '%d.%s\tLV:%s\t最后上线:%s\t好友:%s/%s\tBC:%s\n' % (
                        i, user.name, user.town_level, user.last_login, user.friends, user.friend_max, user.cost
                    )
                    i += 1
                print(du8('%s%s' % ('申请列表:\n', strf)))
                adduser = raw_inputd('选择要添加的好友序号，空格分割，序号前加减号表示拒绝> ').split(' ')
                if adduser != ['']:
                    for u in adduser:
                        if not u:
                            continue
                        if not (u.isdigit() or (u[0] == '-' and u[1:].isdigit())):
                            self.logger.warning('输入"%s"非数字' % u)
                            continue
                        if u.startswith('-'):
                            u = u[1:]
                            param = 'dialog=1&user_id=%s' % users[int(u) - 1].id
                            resp, ct = self._dopost('friend/refuse_friend', postdata = param)
                        else:
                            if users[int(u) - 1].friends == users[int(u) - 1].friend_max:
                                self.logger.warning('无法成为好友ww')
                            param = 'dialog=1&user_id=%s' % users[int(u) - 1].id
                            resp, ct = self._dopost('friend/approve_friend', postdata = param)
                        self.logger.info(resp['errmsg'])
                        time.sleep(2)
            elif choice == '2':
                if lastmove != 2:
                    resp, ct = self._dopost('menu/other_list')
                lastmove = 2
                qry = raw_inputd('输入关键词> ')
                param = 'name=%s' % qry
                resp, ct = self._dopost('menu/player_search', postdata = param)
                if resp['error']:return
                try:
                    users = self.tolist(ct.body.player_search.user_list.user)
                except:
                    users = []
                # else:
                #    if 'name' in users:#只有一个
                #        users=[users]
                i = 1
                strf = ''
                for user in users:
                    strf += '%d.%s\tLV:%s\t最后上线:%s\t好友:%s/%s\tBC:%s\n' % (
                        i, user.name, user.town_level, user.last_login, user.friends, user.friend_max, user.cost
                    )
                    i += 1
                print(du8('%s%s' % ('搜索结果:\n', strf)))
                usel = raw_inputd('选择要添加的好友序号, 空格分割多个，回车返回> ')
                uids = []
                for u in usel.split(' '):
                    if not u:
                        continue
                    if not (u.isdigit() or (u[0] == '-' and u[1:].isdigit())):
                        self.logger.warning('输入"%s"非数字' % u)
                        continue
                    if int(u) > len(users):
                        self.logger.error('no.%s:下标越界XD' % u)
                    else:
                        if users[int(u) - 1].friends == users[int(u) - 1].friend_max:
                            self.logger.warning('%s %s' % (users[int(u) - 1].name, '对方好友已满ww'))
                        uids.append(users[int(u) - 1].id)
                if uids != []:
                    param = 'dialog=1&user_id=%s' % (','.join(uids))
                    resp, ct = self._dopost('friend/add_friend', postdata = param)
                    self.logger.info(resp['errmsg'])
            elif choice == '4':
                return True
            else:
                self.logger.error('木有这个选项哟0w0')
            choice = ''

    def _parse_reward(self, r):
        # type 1:卡片 2:道具 3:金 4:绊点 5:蛋卷
        if r.type == '1':
            cname = self.carddb[int(r.card_id)][0]
            if 'content' in r :
                if cname in r.content:  # 物品为卡片有时content是卡片名称（吧
                    strl = ('%s:%s' % (r.title, r.content))
                else:
                    strl = ('%s:%s' % (r.content, cname))
            else:#秘境完成奖励
                strl = ('%s%s' % (cname, '(闪)' if r.holo_flag=='1' else ''))
        else:
            if 'content' in r :
                strl = '%s:' % r.title
                if r.type == '2':
                    strl += '%sx%s' % (self.player.item.get_name(int(r.item_id)), r.get_num)
                elif r.type == '3':
                    strl += '%sG' % r.point
                elif r.type == '4':
                    strl += '%sFP' % r.point
                elif r.type == '5':
                    strl += '%sx%s' % ('蛋蛋卷', r.get_num)
                else:
                    strl += r.type
            else:#秘境完成奖励
                strl = ""
                if r.type == '2':
                    strl = '%sx%s' % (self.player.item.get_name(int(r.item_id)), r.item_num)
                elif r.type == '3':
                    strl = '%sG' % r.get_money
                elif r.type == '4':
                    strl = '%sFP' % r.get_point
                elif r.type == '5':
                    strl = '%sx%s' % ('蛋蛋卷', r.item_num)
                else:
                    strl = r.type
        return strl

    @plugin.func_hook
    def reward_box(self, rw_type = '12345'):
        if self._dopost('menu/menulist')[0]['error']:
            return False
        resp, ct = self._dopost('mainmenu', no2ndkey = True)
        if resp['error']:
            return False
        if ct.body.mainmenu.rewards == '0':
            self.logger.info('木有礼物盒wwww')
            return False
        resp, ct = self._dopost('menu/rewardbox', xmlresp = False)  # 只能额外处理
        # if resp['error']:
        #    return False
        rwds = self.tolist(XML2Dict.fromstring(re.sub('&(?!#)', '--', ct)).response.body.rewardbox_list.rewardbox)  # .replace('&','--')
        # if 'id' in rwds:#只有一个
        #    rwds=[rwds]
        strl = ''
        nid = []
        no_detail = False
        no_get = False
        if rw_type[-1] == '>':
            no_detail = True
            rw_type = rw_type[:-1]
        if rw_type[-1] == '<':
            no_get = True
            rw_type = rw_type[:-1]
        rw_type = raw_du8(rw_type)
        real_desc_match = not rw_type.isdigit() or not rw_type
        for r in rwds:
            if (real_desc_match and \
                    re.search(rw_type, r.content + r.title + (r.type == '1' and self.carddb[int(r.card_id)][0] or ''))
                ) or (\
                    not real_desc_match and \
                    r.type in rw_type
                ):
                strl += self._parse_reward(r) + ' , ' 
                if not no_get:
                    nid.append(r.id)
        if not strl:
            self.logger.info('没有符合筛选的奖励(%d)' % (len(rwds)))
        else:
            if no_detail:
                self.logger.info('将领取%d件奖励，剩余%d件未领取' % (len(strl.split(' , ')) - 1, len(rwds)) )
            else:
                self.logger.info(maclient_network.htmlescape(strl.rstrip(' , ').replace('--', '&')).replace('\n',' '))
            if no_get:
                return
            res = self._get_rewards(nid)
            if res[0]:
               self.logger.info(res[1])


    @plugin.func_hook
    def point_setting(self):
        if self._dopost('menu/menulist')[0]['error']:
            return
        if self._dopost('menu/playerinfo', postdata = 'kind=6&user_id=%s' % self.player.id)[0]['error']:
            return
        resp, ct = self._dopost('town/lvup_status', postdata = 'kind=6&user_id=%s' % self.player.id)
        if resp['error']:
            return
        free_points = int(ct.header.your_data.free_ap_bc_point)
        if free_points == 0:
            self.logger.info('没有未分配的点数233')
            return False
        else:
            self.logger.info('还有%d点未分配点数' % free_points)
        while True:
            try:
                ap, bc = raw_inputd('输入要分配给AP BC的点数，空格分隔> ').split(' ')
            except ValueError:
                self.logger.warning('少输入了一个数或者多输了一个数吧')
            else:
                break
        if not self._dopost('town/pointsetting', postdata = 'ap=%s&bc=%s' % (ap, bc))[0]['error']:
            self.logger.info('点数分配成功！')
            return True

    @plugin.func_hook
    def factor_battle(self, minbc = 0, sel_lake = ''):
        # if self.loc =='tw':
        #     def get_parts():
        #         self._dopost('battle/area', xmlresp = False)
        #         return self._dopost('battle/competition_parts?redirect_flg=1', noencrypt = True)
        # else:
        minbc = int(minbc)
        # try count
        trycnt = self._read_config('system', 'try_factor_times')
        if trycnt == '0':
            trycnt = '999'
        sel_lake = sel_lake.split(',')
        battle_win = 1
        if self.loc in ['jp', 'sg']:
            self._dopost('battle/area', xmlresp = False)
            resp, cmp_parts_ct = self._dopost('battle/competition_parts?redirect_flg=1', noencrypt = True)
        else:
            resp, cmp_parts_ct = self._dopost('battle/area')
        if resp['error']:
            return
        cmp_parts = cmp_parts_ct.body.competition_parts
        for i in xrange(int(trycnt)):
            self.logger.info('factor_battle:因子战:第%d/%s次 寻找油腻的师姐' % (i + 1, trycnt))
            lakes = cmp_parts.lake
            # only one
            if len(lakes) == 1:
                lakes = [lakes]
            # EVENT HANDLE
            if 'event_point' in cmp_parts:
                self.logger.info('BP:%s Rank:%s x%s %s left.' % (
                    cmp_parts.event_point, cmp_parts.event_rank, cmp_parts.event_bonus_rate,
                    time.strftime('%M\'%S"', time.localtime(int(cmp_parts.event_bonus_end_time) / 1000 - time.time())) if cmp_parts.event_bonus_end_time != '0' else '0'))
            random.shuffle(lakes)
            if sel_lake == ['']:
                l = lakes[0]
            else:
                not_set = True
                for l in lakes:
                    if 'lake_id' not in l:
                        l['lake_id'] = l.event_id
                    if l.lake_id in sel_lake:
                        not_set = False
                        break
                if not_set:
                    self.logger.warning('筛选条件 %s 未能选出符合的湖，将随机选择' % ','.join(sel_lake))
                    l = random.choice(lakes)
            if 'event_id' not in l:
                l['event_id'] = '0'
                partids = [0]

            # if battle_win>0:#赢过至少一次则重新筛选
            partids = []
            battle_win = 0
            if l.lake_id == '0':
                l['event_id'] = '0'  # 补全参数
                partids = [0] #未选择湖只有一个碎片
            elif l.event_id != '0':
                partids = [0] #pvp只有一个碎片
            else:
                # 只打没有的碎片
                if self.cfg_factor_getnew:
                    for p in l.parts_list.parts:
                        if int(p.parts_have) == 0:
                            partids.append(int(p.parts_num))
                else:
                    partids = [i for i in xrange(1, 10)]
                    random.shuffle(partids)
            # circulate part id
            for partid in partids:
                if self.player.bc['current'] <= minbc:
                    self.logger.info('BC已突破下限%d，退出o(*≧▽≦)ツ ' % minbc)
                    return
                self.logger.info('选择因子 %s:%s(%s), 碎片id %d%s' % (
                    l.lake_id,
                    l.lake_id == '0' and 'NONE' or l.title,
                    self.carddb[int(l.master_card_id)][0] if 'master_card_id' in l else 'x',
                    0 if (l.event_id != '0') else partid,
                    ' 待选:%d' % (len(partids) - battle_win) if self.cfg_factor_getnew else ''
                ))
                if l.event_id != '0':  # event
                    param = 'event_id=%s&move=1' % (l.lake_id)
                else:
                    param = 'knight_id=%s&move=1&parts_id=%d' % (l.lake_id, partid)
                resp, ct = self._dopost('battle/battle_userlist', postdata = param)
                if resp['error']:
                    continue
                # print xml2.response.body.battle/battle_userlist.user_list
                time.sleep(3.1415926)
                try:
                    userlist = ct.body.battle_userlist.user_list.user
                except KeyError:  # no user found
                    continue
                for u in self.tolist(userlist):
                    cid = int(u.leader_card.master_card_id)
                    cost = int(u.cost)
                    friends = int(u.friends)
                    deck_rank = int(u.deck_rank)
                    rank = int(u.rank)
                    lv = int(u.town_level)
                    star = int(self.carddb[cid][1])
                    # try:
                    #     star = int(self.carddb[cid][1])
                    # except KeyError:
                    #     self.logger.warning('id为 %d 的卡片木有找到. 你可能想要查看这个网页:\n%s' % (
                    #         cid,
                    #         duowan[self.loc[:2]] % (base64.encodestring('{"no":"%d"}' % cid).strip('\n').replace('=', '_3_'))))
                    # else:
                    self.logger.debug('factor_battle: star:%s, cid:%d, deckrank:%d, cost:%d, result:%s' % (
                        star,
                        cid,
                        deck_rank,
                        cost,
                        eval(self.evalstr_factor))
                    )
                    if eval(self.evalstr_factor):
                        self.logger.debug('factor_battle:->%s @ %s' % (u.name, u.leader_card.master_card_id))
                        ap = self.player.ap['current']
                        bc = self.player.bc['current']
                        self.logger.info('%s%s%s' % ('艹了一下一个叫 ', u.name, ' 的家伙'))
                        if l.event_id != '0':  # event
                            fparam = 'battle_type=0&event_id=%s&user_id=%s' % (l.event_id, u.id)
                        else:
                            fparam = 'lake_id=%s&parts_id=%d&user_id=%s' % (l.lake_id, partid, u.id)
                        resp, ct = self._dopost('battle/battle', postdata = fparam)
                        if resp['error']:
                            time.sleep(2)
                            continue
                        elif resp['errno'] == 1050:
                            self.logger.warning('BC不够了TOT')
                            if not self.red_tea(False):
                                self.logger.error('那就不打了哟(*￣︶￣)y ')
                                return
                        else:
                            try:
                                result = ct.body.battle_result.winner
                            except KeyError:
                                self.logger.warning('no BC ?')
                                return
                            if int(resp['content-length']) > 10000:
                                self.logger.info('收集碎片合成了新的骑士卡片！')
                                return
                            # print bc,self.player.bc.current
                            self.logger.info((result == '0' and '擦输了QAQ' or '赢了XDDD') +
                                ' AP:%+d/%s/%s' % (
                                    self.player.ap['current'] - ap,
                                    self.player.ap['current'],
                                    self.player.ap['max']) +
                                ' BC:%+d/%s/%s' % (
                                    self.player.bc['current'] - bc,
                                    self.player.bc['current'],
                                    self.player.bc['max']))
                            time.sleep(8.62616513)
                            resp, cmp_parts_ct = self._dopost('battle/area')
                            if result == '1':  # 赢过一次就置为真
                                battle_win += 1
                                cmp_parts = cmp_parts_ct.body.competition_parts
                            break
                time.sleep(int(self._read_config('system', 'factor_sleep')))
            self.logger.sleep('换一个碎片……：-/')
            #time.sleep(int(self._read_config('system', 'factor_sleep')))

    # def remote_Hdl_(self):
    #     def do(method=None,fairy=''):
    #         if method==None:
    #             sleeped=False
    #             while True:
    #                 ##print(self.remote.status,self.remote.STARTED)
    #                 if self.remote.status==self.remote.STARTED:
    #                     if self.remote.tasker!='':
    #                         self.tasker(cmd=self.remote.get_task())
    #                     break
    #                 if not sleeped:
    #                     self.logger.sleep(du8('remote_hdl:已被远程停止，等待开始信号ww'))
    #                     sleeped=True
    #                 time.sleep(30)
    #         elif method=='PROFILE':
    #             self.remote.set(
    #                 {'ap_current':self.player.ap['current'],
    #                 'ap_max':self.player.ap['max'],
    #                 'bc_current':self.player.bc['current'],
    #                 'bc_max':self.player.bc['max'],
    #                 'gold':self.player.gold})
    #         elif method=='FAIRY':
    #             self.remote.fckfairy(fairy)
    #         if self.remote.lastprofile!=0:
    #             self.logger.debug('remote_hdl:profile has been uploaded %s seconds ago'%
    #                 (int(time.time()-self.remote.lastprofile)))
    #             self.remote.lastprofile=0
    #     return do

    @plugin.func_hook
    def _exit(self, code = 0):
        # if self.settitle:
        #     self.stitle.flag=0
        #     self.stitle.join(0.1)
        try:
            self.logger.logfile.flush()
            self._request_flush_config(force = True)
        except:
            pass
        # if code > 0:
        #     raw_inputd('THAT\'S THE END')
        sys.exit(code)




if __name__ == '__main__':
    if len(sys.argv) >= 2:
        MAClient1 = MAClient(configfile = sys.argv[1], savesession = True)
    else:
        MAClient1 = MAClient(savesession = True)
    MAClient1.login()