# coding:utf-8
from _prototype import plugin_prototype
from cross_platform import *
if PYTHON3:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from io import StringIO
    import _webbrowser3 as webbrowser
    import urllib.request as urllib2
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from cStringIO import StringIO
    import _webbrowser as webbrowser
    import urllib2
    try:
        import _winreg as winreg
    except ImportError:
        winreg = None
import os, os.path as opath
import gzip
import socket
import urllib
import maclient_network

# start meta
__plugin_name__ = 'web broswer helper'
__author = 'fffonion'
__version__ = 0.49
hooks = {}
extra_cmd = {'web':'start_webproxy', 'w':'start_webproxy', 'go':'make_request'}
# end meta
# generate weburl
weburl = dict(maclient_network.serv)
for k in weburl:
    if isinstance(weburl[k], list):#new in 1.71
        weburl[k] = 'http://%s:%d/connect/web/?%%s' % (weburl[k][0], weburl[k][2])
    else:#legacy
        weburl[k] = weburl[k].replace('app/', 'web/?%s')

servers = ['static.sdg-china.com' ,'ma.webpatch.sdg-china.com', 'game.ma.mobimon.com.tw', 'web.million-arthurs.com', 'ma.actoz.com']
# other stuffs
headers = {'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'X-Requested-With': 'com.square_enix.million_',
    'User-Agent': '',
    'Accept-Language': 'zh-CN, en-US',
    'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7', }
    # 'Accept-Encoding':'gzip,deflate'}

def _get_temp():
    if sys.platform == 'win32':
        return opath.join(os.environ.get('tmp'), '.MAClient.webhelper_cache')
    else:
        try:
            open('/tmp/.MAClient.test', 'w')
        except OSError:
            return './.MAClient.webhelper_cache'
        except IOError:
            return './.MAClient.webhelper_cache'
        else:
            return '/tmp/.MAClient.webhelper_cache'


MIME_MAP = {'js' : 'application/x-javascript', 'css' : 'text/css',
'jpg' : 'image/jpeg', 'png' : 'image/png', 'gif' : 'image/gif'}
#MITM_MODE = ''

def start_webproxy(plugin_vals):
    def do(args):
        TEMP_PATH = _get_temp()
        if not opath.exists(TEMP_PATH):
            os.mkdir(TEMP_PATH)
        headers['cookie'] = plugin_vals['cookie']
        headers['User-Agent'] = plugin_vals['poster'].header['User-Agent']
        headers['X-Requested-With'] += plugin_vals['loc'][:2]
        homeurl = weburl[plugin_vals['loc']] % (plugin_vals['cookie'].rstrip(';'))
        enable_proxy()
        #if not winreg or True:
        #    global MITM_MODE
        #    MITM_MODE = weburl[plugin_vals['loc']].rstrip('/connect/web/?%s')
        if len(args) == 0 or args[0].rstrip() != '!':
            print(du8('现在将打开浏览器窗口\n'
              '如果没有，请手动打开主页:\n'
              '%s\n'
                % homeurl))
            webbrowser.open(homeurl)
        else:
            print(du8('已设定不自动打开首页'))
        print(du8('对不使用IE代理的浏览器，请将代理设置为127.0.0.1:23301\n'
              '按Ctrl+C关闭并恢复无代理'))
        server = ThreadingHTTPServer(("", 23301) , Proxy)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
            disable_proxy()
    return do

def make_request(plugin_vals):
    def do(args):
        url = args.rstrip()
        if not url:
            return
        headers['cookie'] = plugin_vals['cookie']
        headers['User-Agent'] = plugin_vals['poster'].header['User-Agent']
        headers['X-Requested-With'] += plugin_vals['loc'][:2]
        homeurl = weburl[plugin_vals['loc']] % (plugin_vals['cookie'].rstrip(';'))
        req = urllib2.Request(url, headers = headers)
        resp = opener.open(req)
        body = resp.read()
        print('GET %s received %d bytes.' % (url, len(body)))
    return do

def enable_proxy():
    if winreg:
        INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
            0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyOverride', 0, winreg.REG_SZ, u'127.0.0.1')  # Bypass the proxy for localhost
        winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyServer', 0, winreg.REG_SZ, u'127.0.0.1:23301')
        os.system(du8('TITLE 请按Ctrl+C 退出，不要直接X掉啊'))
    else:
        os.environ['http_proxy'] = 'http://127.0.0.1:23301'

def disable_proxy():
    if winreg:
        INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
            0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(INTERNET_SETTINGS, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
        os.system(du8('TITLE 代理设置已清除ww'))
        # winreg.DeleteKey(INTERNET_SETTINGS, 'ProxyOverride')
        # winreg.DeleteKey(INTERNET_SETTINGS, 'ProxyServer')
    else:
        os.environ['http_proxy'] = ''
# opener
if PYTHON3:
    opener = urllib2.build_opener(urllib2.ProxyHandler(urllib.request.getproxies()))
else:
    opener = urllib2.build_opener(urllib2.ProxyHandler(urllib.getproxies()))
class Proxy(BaseHTTPRequestHandler):
    def do_HDL(self):
        TEMP_PATH = _get_temp()
        #if MITM_MODE and not self.path.startswith(MITM_MODE):
        #    self.path = MITM_MODE + self.path
        ext = opath.splitext(self.path)[1][1:]
        if ext in ['jpg', 'png', 'css', 'js', 'gif'] and self.headers['Host'].rstrip(':10001') in servers:
            url = self.path.lstrip('http://')
            d, f = opath.split(url)
            cache_file = opath.join(TEMP_PATH, opath.join(d.replace('/', '#').replace(':10001', ''), f))
        else:
            cache_file = None
        #try to read cache?
        if cache_file and opath.exists(cache_file):
            body = open(cache_file, 'rb').read()
            self.send_response(200)
            self.send_header('Content-Encoding'.encode('ascii'), 'indentity'.encode('ascii'))
            self.send_header('Content-Length'.encode('ascii'), len(body))
            self.send_header('Content-Type'.encode('ascii'), MIME_MAP[ext].encode('ascii'))
            self.end_headers()
            self.wfile.write(body)
            print('Cache hit : %s' % self.path)
            return
        #no cache
        req = urllib2.Request(self.path, headers = headers)
        try:
            if self.command == 'POST':
                data = self.rfile.read(int(self.headers['Content-Length']))
                resp = opener.open(req, data)
            else:
                resp = opener.open(req)
        except urllib2.HTTPError as e:
            return
        body = resp.read()
        self.send_response(resp.getcode())
        for h in resp.info().items():
            self.send_header(h[0].encode('ascii'), h[1].encode('ascii'))
        self.send_header('Content-Encoding'.encode('ascii'), 'indentity'.encode('ascii'))
        self.end_headers()
        # try:
        #     f = StringIO(body)
        #     gzipper = gzip.GzipFile(fileobj = f)
        #     data = gzipper.read()
        # except:
        #     data = body
        self.wfile.write(body)
        #write to cache
        if cache_file:
            if not opath.exists(opath.split(cache_file)[0]):
                os.makedirs(opath.split(cache_file)[0])
            with open(cache_file, 'wb') as f:
                f.write(body)
                f.close()
    do_GET = do_POST = do_HDL

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    # address_family = socket.AF_INET6
    address_family = socket.AF_INET

if __name__ == "__main__":
    c = start_webproxy({'cookie':'1=2', 'loc':'cn'})
    c('')
