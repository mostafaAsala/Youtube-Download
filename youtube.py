from typing import Any
import numpy as np
from typing_extensions import Literal
import pytube
from pytube import YouTube,Playlist,request
from tkinter import  Menu, Misc, filedialog
from tkinter import *
import requests
import re,os
import threading
import time
root = Tk()
entry = Entry(root)
entry.pack(side='left')
youtube_pattern = re.compile(r'(?:https?:\/\/)?(?:www\.)?youtu(?:be\.com\/(?:watch\?.*v=|embed\/)|\.be\/)([\w\-]+)(?:.*)?(?:[\?&]t=([\dhms]*))?')
youtube_PlayList = re.compile(r'(?:https?:\/\/)?(?:www\.)?youtu(?:be\.com\/(?:playlist\?.*list=|embed\/)|\.be\/)([\w\-]+)(?:.*)?(?:[\?&]t=([\dhms]*))?')
resList = ['144p','240p','360p','480p','720p','1080p','2K','4K']
typeList=['48kbps','50kbps','70kbps','128kbps','160kbps']

class DownloadPaused(Exception):
            pass
class YouTubeDownloader:
    def __init__(self,parent,youtubeV=None,stream=None,filter=None):
        self.video = youtubeV
        self.filter=filter
        self.parent=parent
        self.stream = stream
        self.filesize = None
        self.downloaded = 0
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._stop_event.clear()
        self._pause_event.set()
        self._finish_event = threading.Event()
        self._finish_event.clear()
    def on_progress(self,chunk: bytes, file_handler:Any, bytes_remaining: int):
            self._pause_event.wait()
            if self._stop_event.is_set():
                raise DownloadPaused('Download paused')
            
            print(bytes_remaining/self.filesize)
            pass
    def on_complete(self,Any,file_path: str | None):
            print(file_path)
            pass
            
    def _download_thread(self, filepath):
        print("first video")
        if self.stream==None and self.video!=None:
            self.stream = self.video.streams.filter(res=self.filter,progressive=True).first()
        if self.video==None and self.stream==None:
            print("No data prvided.....")
            return
        self.filesize = self.stream.filesize
        self.downloaded = 0
        self._pause_event.set()
        
        self.video:pytube.YouTube
        
        self.video.register_on_progress_callback(self.on_progress)
        self.video.register_on_complete_callback(self.on_complete)
        self.stream:pytube.Stream
        
        #self.stream.on_progress = self.on_progress
        #self.stream.on_complete = on_complete
        filepath = filepath+".mp4"
        self.stream.download(filename=filepath)
        if False:
            with open(filepath, 'wb') as f:
                self.stream:pytube.Stream
                for chunk in self.stream.on_progress():
                    if self._stop_event.is_set():
                        self._finish_event.set()
                        break
                    self._pause_event.wait()
                    f.write(chunk)
                    self.downloaded += len(chunk)

                    if self.downloaded == self.filesize:
                        break
        self._finish_event.set()
    def start_download(self, filepath):
        self._stop_event.clear()
        self._pause_event.clear()
        download_thread = threading.Thread(target=self._download_thread, args=(filepath,))
        download_thread.start()
        

    def pause_download(self):
        
        self._pause_event.clear()

    def resume_download(self):
        self._pause_event.set()

    def stop_download(self):
        self._stop_event.set()
        self._pause_event.set()

class Youtube_Video(Frame):
    def __init__(self,link, master=None):
        Frame.__init__(self,master=master)
        self.video = YouTube(link,use_oauth=True,allow_oauth_cache=True)
        self.streams = self.video.streams
        self.resolution =StringVar(self)
        self.resolution.set(resList[0])
        self.type =StringVar(self)
        self.type.set(typeList[0])
        self.filter = StringVar(self)
        self.filteredStreams : list(pytube.Stream)=[]
        self.CreateFrame()
        self.download:list(pytube.Stream)=[]
        pass
    def selres(self):
        print(self.filter.get())
        self.filteredStreams = self.streams.filter(res=self.filter.get())
        self.updateList()
    def seltype(self):
        self.filteredStreams = self.streams.filter(abr=self.filter.get())
        self.updateList()
    def updateList(self):
        self.l.delete(0,END)
        for i,d in enumerate(self.filteredStreams):
            size = d.filesize
            strd="" 
            for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
                if abs(size) < 1024.0:
                    strd = f"{size:3.1f}{unit}"
                    break
                size/=1024.0
            data = strd +": " +str(d) 
            self.l.insert(i,data)
        self.l.update()
    def getSelectedStream(self):
        self.download=[]
        for item in self.l.curselection():
            self.download.append(self.filteredStreams[item])
        for i in range(len(self.download)):
            self.download[i].download()
        print( self.download)
    def findRes(self):
        if self.filter in resList:
            self.filteredStreams = self.streams.filter(res=self.filter.get())
        if self.filter in typeList : 
            self.filteredStreams = self.streams.filter(type=self.filter.get())

        print("streams: ",self.streamMap)
    def CreateFrame(self):
        header_label = Label(root, text="Video", font=('Helvetica', 21, 'bold'))
        header_label.pack()
        header_label = Label(root, text=self.video.title, font=('Helvetica', 18, 'bold'))
        header_label.pack()
        
        self.l = Listbox(self)
        self.l.pack(expand=True,fill='both')

        f1=Frame(self)
        Label(f1,text="Audio").pack()
        f1.pack()
        for i in typeList:
            Radiobutton(f1,text=i,variable=self.filter,value=i,command=self.seltype).pack(side='left')
        f2=Frame(self)
        Label(f2,text="Video").pack()
        f2.pack()   
        for i in resList:
            Radiobutton(f2,text=i,variable=self.filter,value=i,command=self.selres).pack(side='left')
        self.filter.set('144p')
        Button(self,text="Downlad",command=self.getSelectedStream).pack()
class DownloadList(Toplevel):
    def __init__(self,filter,DList,Title="", master: Misc | None = None):
        super().__init__(master)
        self.downloadList=[]
        self.filter=filter
        self.title = Title
        self.Build(DList=DList)
        downloadThread = threading.Thread(target= self.DownloadThread)
        downloadThread.start()
    def Build(self,DList):
        for vid in DList:
            f=Frame(self)
            v = YouTubeDownloader(self,youtubeV=vid,filter=self.filter)
            f2 = Frame(f)
            f2.pack(side=TOP)

            l1=Label(f2,text=vid.title)
            l1.pack(side=RIGHT)
            l2=Label(f2,text="pending..")
            l2.pack(side=RIGHT)
            b1=Button(f,text="resume",command=v.resume_download)
            b1.pack()
            b1["state"] = DISABLED
            b2=Button(f,text="stop",command=v.stop_download)
            b2.pack()
            b2["state"] = DISABLED
            b3=Button(f,text="pause",command=v.pause_download)
            b3.pack()
            b3["state"] = DISABLED
            self.downloadList.append((l2 ,v,b1,b2,b3,vid.title))
            
    def DownloadThread(self):
        
        path = filedialog.askdirectory()

        path = path+f"/{self.title}"
        if not os.path.isdir(path):
            os.mkdir(path)
            pass
        print(path)
        for L,DE,b1,b2,b3,t in self.downloadList:
            L:Label
            DE:YouTubeDownloader
            DE.start_download(path+f"/{t}")
            b1["state"] = NORMAL
            b2["state"] = NORMAL
            b3["state"] = NORMAL
            while not DE._finish_event.is_set():
                time.sleep(1)
                L.config(text=f"Downloading {DE.downloaded}/{DE.filesize}")
            L.config(text=f"finished")
            b1["state"] = DISABLED
            b2["state"] = DISABLED
            b2["state"] = DISABLED
            
            

        
class Youtube_List(Frame):
    def __init__(self,link, master=None):
        Frame.__init__(self,master=master)
        self.list = Playlist(link)
        self.videos = self.list.videos
        self.resolution =StringVar(self)
        self.DL = None
        self.resolution.set(resList[0])
        self.type =StringVar(self)
        self.type.set(typeList[0])
        self.filter = StringVar(self)
        self.filteredStreams : list(pytube.Stream)=[]
        self.CreateFrame()
        self.download:list(pytube.Stream)=[]
        pass
    def selres(self):
        print(self.filter.get())
        self.filteredStreams = self.streams.filter(res=self.filter.get())
        self.updateList()
    def seltype(self):
        self.filteredStreams = self.streams.filter(abr=self.filter.get())
        self.updateList()
    def updateList(self):
        self.l.delete(0,END)
        for i,d in enumerate(self.filteredStreams):
            size = d.filesize
            strd="" 
            for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
                if abs(size) < 1024.0:
                    strd = f"{size:3.1f}{unit}"
                    break
                size/=1024.0
            data = strd +": " +str(d) 
            self.l.insert(i,data)
        self.l.update()
    def getSelectedStream(self):
        self.download=[]
        videos=[]
        for i in self.l.curselection():
            self.download.append(self.videos[i])
        self.DL = DownloadList(self.filter,self.download,self.list.title ,self)
        
    def findRes(self):
        if self.filter in resList:
            self.filteredStreams = self.streams.filter(res=self.filter.get())
        if self.filter in typeList : 
            self.filteredStreams = self.streams.filter(type=self.filter.get())

        print("streams: ",self.streamMap)
    def get_Videos(self):
        loadingL = Label(self,text="Loading Videos.....")
        loadingL.pack()
        titleList = []
        count = len(self.videos)
        i=0
        for v in self.videos:
            i+=1
            loadingL.config(text=f"Loading Videos.....{i}/{count}")
            v.__setattr__('use_oauth', True)
            v.__setattr__('allow_oauth_cache',True)
            titleList.append(v.title)
        for i,v in enumerate(titleList):
            self.l.insert(i,str(i)+v)
        loadingL.pack_forget()
        
    def CreateFrame(self):
        header_label = Label(root, text="PlayList", font=('Helvetica', 21, 'bold'))
        header_label.pack()
        header_label = Label(root, text=self.list.title, font=('Helvetica', 18, 'bold'))
        header_label.pack()
        print("text")
        self.l = Listbox(self,selectmode=MULTIPLE)
        self.l.pack(expand=True,fill='both')
        my_thread = threading.Thread(target=self.get_Videos)
        my_thread.start()

        #videos = self.list.video_urls()
        
        f0=Frame(self)
        button_click = lambda: self.l.select_set(0,END)

        b1=Button(f0,text="selectAll",command=button_click)
        b1.pack(side='left')
        f0.pack()
        f1=Frame(self)
        Label(f1,text="Audio").pack()
        f1.pack()
        for i in typeList:
            Radiobutton(f1,text=i,variable=self.filter,value=i).pack(side='left')
        f2=Frame(self)
        Label(f2,text="Video").pack()
        f2.pack()
                 
        for i in resList:
            Radiobutton(f2,text=i,variable=self.filter,value=i).pack(side='left')
        self.filter.set('144p')
        Button(self,text="Downlad",command=self.getSelectedStream).pack()
          
globalText = ""
def getText():
    global globalText
    text = entry.get()
    if text==globalText:return
    globalText=text
    isVid = youtube_pattern.match(text)
    isPlaylist = youtube_PlayList.match(text)
    response = requests.get(text)
    if(response):
        if isVid!=None:
            res=''
            'https://www.youtube.com/watch?v=9K0cVIpEFfY'
            try:
                vidFrame = Youtube_Video(text,root)
                vidFrame.pack()
                


                pass
            except Exception as e:
                print("can't find the video: ",e)
            pass
        elif isPlaylist!=None:  
            try:

                playlist_F = Youtube_List(text,root)
                playlist_F.pack()
            except Exception as e:
                print(e)
            pass

submit = Button(root,text="submit",command=getText)
submit.pack(side='left')

#v = Youtube_Video('https://www.youtube.com/watch?v=9K0cVIpEFfY',root)
#v.pack()
#Button(root,text="Downlad",command=v.getSelectedStream).pack()
                
root.mainloop()


