import argparse
import requests
import json
import time
from http import cookiejar
from math import floor
from os.path import exists
import m3u8
from Crypto.Cipher import AES
import cloudscraper


class ProgressBar:
    """
    This class allows you to make easily a progress bar.
    """
    def __init__(self, steps, maxbar=100, title='Chargement',blocsize=1000):
        if steps <= 0 or maxbar <= 0 or maxbar > 200:
            raise ValueError
        self.steps = steps
        self.maxbar = maxbar
        self.title = title
        self.perc = 0
        self._completed_steps = 0
        self.blocsize=blocsize
        self.start_time=time.time()
        # self.update(False)
    def update(self, increase=True):
        if increase:
            self._completed_steps += 1
        self.perc = floor(self._completed_steps / self.steps * 100)
        if self._completed_steps > self.steps:
            self._completed_steps = self.steps
        steps_bar = floor(self.perc / 100 * self.maxbar)
        if steps_bar == 0:
            visual_bar = self.maxbar * ' '
        else:
            visual_bar = (steps_bar - 1) * '═' + '>' + (self.maxbar - steps_bar) * ' '
        speedy=(self._completed_steps*self.blocsize)/(time.time()-self.start_time)
        return self.title + ' [' + visual_bar + '] ' + str(self.perc) + '% '


def cookie_remover(cj,name):
    try:cj.clear(domain=".crunchyroll.com",path="/",name=name)
    except:pass

def getter(url):
    if exists("cookies.txt"):
        cj=cookiejar.MozillaCookieJar("cookies.txt")
        cj.load()
        cookie_remover(cj,"OptanonControl")
        cookie_remover(cj,"__cfduid")
        cookie_remover(cj,"c_visitor")
        print("Cookies miam🍪.. Loaded")
    # session.cookies=cj #when add cookie can't bypass cloudflare
    scraper = cloudscraper.create_scraper(browser='chrome')#sess=session)
    scraper.cookies=cj#.set_cookie(cookiejar.Cookie(version=0, name='OptanonAlertBoxClosed', value='2020-06-23T11:42:41.657Z', port=None, port_specified=False, domain='.www.crunchyroll.com', domain_specified=True, domain_initial_dot=True, path='/', path_specified=False, secure=False, expires=1624448561, discard=False, comment=None, comment_url=None, rest={}, rfc2109=False))
    wb_page=scraper.get(url)#"https://www.crunchyroll.com/fr/tower-of-god/episode-11-underwater-hunt-part-one-794529").text
    if wb_page.ok:
        if "showmedia-trailer-notice" in wb_page.text:
            raise Exception("Your are not premium")
        infos=wb_page.text.split("vilos.config.media = ")[1].split(";")[0]
        infos=json.loads(infos)["streams"]
        best=None
        for i in infos:
            if i["hardsub_lang"]=="frFR" and ".m3u8" in i["url"]:
                tmp=m3u8.load(i["url"])
                # tmp=m3u8.loads(scraper.get(i["url"]).text)
                print("==============")
                print(tmp.data)
                if tmp.playlists:
                    for arg in tmp.playlists:
                        # arg=re.search(tmp.text,re.MULTILINE).groupdict()
                        # print(arg)
                        if not best or best.stream_info.resolution[0]<arg.stream_info.resolution[0]:
                            best=arg
                        elif best.stream_info.resolution[0]==arg.stream_info.resolution[0]:
                            if best.stream_info.resolution[1]<arg.stream_info.resolution[1]:
                                best=arg
                            elif best.stream_info.resolution[1]==arg.stream_info.resolution[1]:
                                if best.stream_info.frame_rate<arg.stream_info.frame_rate:
                                    best=arg
                                elif best.stream_info.frame_rate==arg.stream_info.frame_rate:
                                    if  best.stream_info.bandwidth<arg.stream_info.bandwidth:
                                        best=arg
                else:
                    print("Oh that's a recent airing anime")
                    return i["url"]
        return best
    raise Exception("Error")


def main(infos,outfile,username=None,password=None):
    print("======================")
    print(infos)
    print(type(infos))
    print("======================")
    if "stream_info" in dir(infos):
        print("\033[1m"+"╔"+"═"*40+"╗")
        print("║"+("Resolution: "+str(infos.stream_info.resolution[0])+"x"+str(infos.stream_info.resolution[1])).ljust(40)+"║")
        print("║"+("Framerate:  "+str(infos.stream_info.frame_rate)).ljust(40)+"║")
        print("║"+("Bandwidth:  "+str(infos.stream_info.bandwidth)).ljust(40)+"║")
        print("╚"+"═"*40+"╝"+ "\033[0m")
        r=m3u8.load(infos.uri)
        key=requests.get(r.keys[0].uri).content
        progress_bar=ProgressBar(len(r.segments))
        with open(outfile,"wb") as output_file:
            for fil in r.segments:
                input_stream=requests.get(fil.uri,stream=True) 
                cipher_encrypt = AES.new(key, AES.MODE_CBC, key)
                for part in input_stream.iter_content(chunk_size=512):
                    output_file.write(cipher_encrypt.decrypt(part))
                print(progress_bar.update(),end="\r")
    # elif True:
    #     URL="https://dl.v.vrv.co/evs/10ac443c0ba37d3d252ef9e4fe819657/assets/10ac443c0ba37d3d252ef9e4fe819657_3831456.mp4/clipFrom/0000/clipTo/120000/index.m3u8?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cCo6Ly9kbC52LnZydi5jby9ldnMvMTBhYzQ0M2MwYmEzN2QzZDI1MmVmOWU0ZmU4MTk2NTcvYXNzZXRzLzEwYWM0NDNjMGJhMzdkM2QyNTJlZjllNGZlODE5NjU3XzM4MzE0NTYubXA0L2NsaXBGcm9tLzAwMDAvY2xpcFRvLzEyMDAwMC9pbmRleC5tM3U4IiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNTkzMDk2MTU0fX19XX0_&Signature=Ej5fX5Zs9OB3Rxm9hCbLDLhl~SDOYS1xa6THOSEfyNqEc25bhewGIFGPY-pGDWNeKAqqVcFx6sG4ZUIl313hML2kXaaiG86OfN0Z9FUqAKXVLra8hH5AFbMKxhzbQaHpU~9Nb7k59MUFjC9Tk653-Iwl1qmVP4hnWq3E2I2ps-KCoTnQj5LY1ZnJm~7Euv6j5mXAZoAJmBlLPZ-mW-U8zJSilWz4n2EfM8u9xvcz3WwWG5FO0WU0Kr3a5XTyK89GkCglEobxIGGXZlf9NoF22SIpk79HbJSoveTm0I1Al-45Va-Sno1Rx0YEy2TEBrQ~JBPsQ3J9aJC60HSfRT7WYQ__&Key-Pair-Id=DLVR"
    #     r=m3u8.load(URL)
    #     key=requests.get(r.keys[0].uri).content
    #     progress_bar=ProgressBar(len(r.segments))
    #     with open(outfile,"wb") as output_file:
    #         for fil in r.segments:
    #             input_stream=requests.get(fil.uri,stream=True) 
    #             cipher_encrypt = AES.new(key, AES.MODE_CBC, key)
    #             for part in input_stream.iter_content(chunk_size=512):
    #                 output_file.write(cipher_encrypt.decrypt(part))
    #             print(progress_bar.update(),end="\r")
    else:
        print("\033[1m"+"╔"+"═"*40+"╗")
        print("║"+"Humm something happen have you crunchy premium?".ljust(40)+"║")
        print("╚"+"═"*40+"╝"+ "\033[0m")


parser = argparse.ArgumentParser()
parser.add_argument("l", type=str, help="link")
parser.add_argument("o", type=str, help="output file")
parser.add_argument("-u", "--username", type=str, help="username", default=None)#,required=False)
parser.add_argument("-p", "--password", type=str, help="password", default=None)#,required=False)
args = parser.parse_args()
main(getter(args.l),args.o,args.username,args.password)
