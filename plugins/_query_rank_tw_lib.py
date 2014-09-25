# coding:utf-8
# Regular expressions are awesome!!
# Contributor:
#      fffonion        <fffonion@gmail.com>
from datetime import datetime
import re
__version__ = 20140925
query_base = 'http://game.ma.mobimon.com.tw:10001/connect/web/revisions_detail?id=%d'
query_goto = ['http://game.ma.mobimon.com.tw:10001/connect/web/mb_ranklist_fairy?to=%s',
'http://game.ma.mobimon.com.tw:10001/connect/web/mb_ranklist?to=%s',
'http://game.ma.mobimon.com.tw:10001/connect/web/mb_ranklist_guild_fairy?to=%s',
'http://game.ma.mobimon.com.tw:10001/connect/web/mb_ranklist_guild?to=%s',
'http://game.ma.mobimon.com.tw:10001/connect/web/mb_ranklist_country?to=%s&country=%d']
query_country = 'http://game.ma.mobimon.com.tw:10001/connect/web/mb_ranklist_country?country=%d'
# self.fairy, self.collect, guild.fairy, guild.collect
query_rev = [496, None, None, None]
#('闇黑帝國',106), ('海洋聯盟',107), ('巨人國度',108)
query_country_id = []
# 有效期
query_lifetime = datetime(2014, 10, 9, 10, 0, 0, 0)
now = datetime.now()

#妖精(种类)计数
fairy_count = 4
#用于妖精排名的道具加权指数，通过len(re.findall('</table))来判断是否存在第二个表格
fairy_item_count = 1
#妖精与收集品排名的种类：1.(1+收集品) * 妖精等级加权和, 2.妖精等级乘积 *　收集品
fairy_with_coll_type = 1

#收集品种类计数
item_count = 4

#预处理
def pre(s):
    #open(r'z:/test.htm','w').write(s)
    return re.sub('<!--.*?-->', lambda x:'', s, flags = re.DOTALL)

_fairy_with_coll_func = (
lambda x : ('%s' if len(re.findall('</table',x)) == 2 else ('(1 + %s) * (%%s)' % 
                    ' + '.join(['*'.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[fairy_count + 2 + idx])[1:3])
                            for idx in range(fairy_item_count)]))) %
            ' + '.join(['*'.join(re.findall('>(.*)<',i)[1:3]) for i in re.findall('tr>(.*?)</tr', x, re.DOTALL)[1:1+fairy_count]])
                ,
lambda x : ('%s' if len(re.findall('</table',x)) == 2 else ('%s * (%%s)' % 
                    ' * '.join(['*'.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[fairy_count + 2 + idx])[1:3])
                            for idx in range(fairy_item_count)]))) %
            ' * '.join(['*'.join(re.findall('>(.*)<',i)[1:3]) for i in re.findall('tr>(.*?)</tr', x, re.DOTALL)[1:1+fairy_count]])
                
)

query_title = lambda x: ''.join(re.findall('class="blanklist comment_news head00">([^<]+)<', x)[0].split())#strip spaces
query_regex = [
[
('玩家名稱' , lambda x : re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[0]),
('目前排名' , lambda x : re.findall('\d+',re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[1])[0]),
('更新時間' , lambda x : re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', x)[0]),
('妖精等級加權總和' , lambda x : re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2]),
('=' , _fairy_with_coll_func[fairy_with_coll_type - 1]),
('可见区域排名Up:' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[fairy_count + 2 + (0 if len(re.findall('</table',x)) == 2 else 2 + fairy_item_count)]))),
('               ' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[fairy_count + 3 + (0 if len(re.findall('</table',x)) == 2 else 2 + fairy_item_count)]))),
('               ', lambda x : '......'),
('               ' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[-2]))),
('          Down:' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[-1])))
],#0
[],#1
[
('玩家名稱' , lambda x : re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[0]),
('所屬公會' , lambda x : re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[1]),
('目前排名' , lambda x : re.findall('\d+',re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2])[0]),
('更新時間' , lambda x : re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', x)[0]),
('妖精等級加權總和' , lambda x : re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[3]),
('=' , lambda x : ' + '.join(['*'.join(re.findall('>(.*)<',i)[1:3]) for i in re.findall('tr>(.*?)</tr', x, re.DOTALL)[1:3]])),
],#2
[],#3
[]#4
]
if item_count == 1:
    coll = ('收集品數量' , lambda x : re.findall('\d+',re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2])[0])
    #coll = ('目前排名' , lambda x : re.findall('\d+',re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2])[0])#temp
    query_regex[1] = query_regex[0][:3] + [coll] + query_regex[0][5:]
    #query_regex[1] = query_regex[0][:3] + [coll] + query_regex[0][5:]#temp
    #query_regex[1].pop(1)#temp
    #fairy
    query_regex[3] = query_regex[2][:4] + [coll] + query_regex[2][6:]
else:
    query_regex[1] = query_regex[0][:3] + [
    ('收集品積分', lambda x : re.findall('\d+', re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2])[0]),
    ('=' , lambda x :  ' + '.join(['/'.join(re.findall('>(.*)<',i)[1:3]) for i in re.findall('tr[\salign="center"]*>(.*?)</tr', x, re.DOTALL)[1:1+item_count]])),
    ('可见区域排名Up:' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr[\salign="center"]*>(.*?)</tr', x, re.DOTALL)[item_count + 2 + (0 if len(re.findall('</table',x)) == 2 else 2)]))),
    ('               ' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr[\salign="center"]*>(.*?)</tr', x, re.DOTALL)[item_count + 3 + (0 if len(re.findall('</table',x)) == 2 else 2)]))),
    ('               ', lambda x : '......'),
    ('               ' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr[\salign="center"]*>(.*?)</tr', x, re.DOTALL)[-2]))),
    ('          Down:' , lambda x : ' / '.join(re.findall('td[\salign="center"]*>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr[\salign="center"]*>(.*?)</tr', x, re.DOTALL)[-1])))
    ]
    query_regex[3] = query_regex[2][:4] + [('收集品積分', lambda x : re.findall('\d+', re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2])[0])] + query_regex[2][6:]
for p in query_regex[0][5:]:
    query_regex[2].append(p)

#country
query_regex[4] = query_regex[0][:3] + [
('加權總和' , lambda x : re.findall('lititle2.*?/span><br[\s/>]*\s+(.*?)\s+<br', x, re.DOTALL)[2] + ' = ' + \
    ' + '.join(map(lambda e:'%s/%s*%s' %(e[0], e[1] if e[1] else '0', e[2]), 
    [re.findall('td>[\s<p>]*(.*?)[\s</p>].*?">(\d*).*?(\d+)',
        re.findall('tr>(.*?)</tr', x, re.DOTALL)[i],re.DOTALL)[0] for i in range(1, 1 + len(query_country_id))]))
    ),
('各國度總分', 
    lambda x: ('\n' + ' '*11).join([' '.join(re.findall('td>[\s<p>]*(.*?)[\s</p>].*?(\d+)',
        re.findall('tr>(.*?)</tr', x, re.DOTALL)[i],re.DOTALL)[0]) for i in range(5, 5 + len(query_country_id))])
    ),
('可见区域排名Up:' , lambda x : ' / '.join(re.findall('td>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[9]))),
('               ' , lambda x : ' / '.join(re.findall('td>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[10]))),
('               ', lambda x : '......'),
('               ' , lambda x : ' / '.join(re.findall('td>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[-2]))),
('          Down:' , lambda x : ' / '.join(re.findall('td>[\s<p>]*(.*?)[\s</p>]*</td',re.findall('tr>(.*?)</tr', x, re.DOTALL)[-1])))
]
broswer_headers = {'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'X-Requested-With': 'com.square_enix.million_tw',
                'User-Agent': '',
                'Accept-Language': 'zh-CN, en-US',
                'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7',
                'Referer': 'http://game.ma.mobimon.com.tw:10001/connect/web/'}
