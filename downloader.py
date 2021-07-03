import requests
import os
import pathlib
import queue
import threading, time
import json

DOWNLOAD_URL = "https://raw.githubusercontent.com/drumbart/VFA-27_Ready_Room/master/"

PATH = str(os.path.abspath('')).replace('\\', '/').replace('dist', '')
if PATH[-1] != '/':
    PATH = PATH + '/'

f = open(f'{PATH}conf/setup.json', 'r')
settings = json.load(f)
path_data = settings["download_path"]
DOWNLOAD_PATH = str(path_data[0]).replace('\\', '/').replace('dist', '')
if DOWNLOAD_PATH[-1] == '/':
    DOWNLOAD_PATH = DOWNLOAD_PATH[:-1]

try:
    output_data = settings["output_path"]
    OUTPUT_PATH = str(output_data[0]).replace('\\', '/').replace('dist', '')
    if OUTPUT_PATH[-1] == '/':
        OUTPUT_PATH = OUTPUT_PATH[:-1]
except:
    pass

class Downloader():
    def __init__(self):
        self.bytes_downloaded = 0
        self.files_downloaded = 0

        self.download_q = queue.Queue()
        self.liveries = []

       
        f = open("action.txt", "r")
        action = f.read()

        action = action.split(".")
        print(action)

        if action[0] == "action:DownloadKneeboards":
            self.getKneeboards()
            input("\n \n Download of kneeboards is complete. Press enter it exit \n")    
        elif action[0] == "action:DownloadLiveries":
            self.get_skins()
            self.start_download()   
            input("\n \n Download is complete. Press enter it exit \n")   

        elif action[0] == "action:DownloadEventKneeboards":
            self.getEventKneeboards(action[1])
            input("\n \n Download is complete. Press enter it exit \n")  

        elif action[0] == "action:RemoveEventKneeboards":
            self.removeEventKneeboards(action[1])
            input("\n \n Event kneeboards removed. Press enter it exit \n")   

        elif action[0] == "admin:SetPathFor": # admin:SetPathFor.path.delete
            response = requests.get('https://raw.githubusercontent.com/MrRavenMan/WCDownloader/main/paths.json')
            self.liveries = response.json()  
            print(self.liveries)
            # f = open('paths.json')
            # self.liveries = json.load(f)

            if action[2] == "true" or action[2] == "True":
                delete = True
            else:
                delete = False 
            
            self.get_paths(f"https://api.github.com/repos/drumbart/VFA-27_Ready_Room/contents/{action[1]}", delete)
            with open(OUTPUT_PATH + "/paths.json", 'w') as fp:
                json.dump(self.liveries, fp, indent=4)




    def start_download(self):

        t1 = threading.Thread(target=self.downloader, daemon=True)
        t1.start()
        time.sleep(0.2)
        t2 = threading.Thread(target=self.downloader, daemon=True)
        t2.start()
        time.sleep(0.2)
        t3 = threading.Thread(target=self.downloader, daemon=True)
        t3.start()
        time.sleep(0.2)
        t4 = threading.Thread(target=self.downloader, daemon=True)
        t4.start()
        time.sleep(0.2)
        t5 = threading.Thread(target=self.downloader, daemon=True)
        t5.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()
        t5.join()


    def downloader(self):
        while self.download_q.empty() is False:
            item = self.download_q.get()
            self.download_file(item)
            self.download_q.task_done()


    def get_skins(self):
        # f = open('paths.json', 'r')
        # paths = json.load(f)
        # f.close()

        response = requests.get("https://raw.githubusercontent.com/MrRavenMan/WCDownloader/main/paths.json")
        paths = response.json()

        for file in paths:
            try:
                if int(os.path.getmtime(DOWNLOAD_PATH + file["path"])) < int(file["date"]):
                    os.remove(DOWNLOAD_PATH + file["path"])
                    if file["delete"] is True:
                        print(f"Removing {file['path']}")
                    else:
                        print(f"Updating {file['path']}")
                        self.download_q.put(file)
                elif int(os.path.getmtime(DOWNLOAD_PATH + file["path"])) >= int(file["date"]) and file["delete"] is True:
                    os.remove(DOWNLOAD_PATH + file["path"])
                    print(f"Removing {file['path']}")
                else:
                    print(f"File {file['path']} already exists and is up to date")
            except FileNotFoundError:
                print("File not foundd")
                print(DOWNLOAD_PATH  + file["path"])
                if file["delete"] is False:
                    self.download_q.put(file)


    def get_paths(self, url: str, delete: bool = False):
        response = requests.get(url)
        items = response.json()

        add_liveries = []
                
        try:
            for item in items:
                if item["type"] == "dir":  # If file is a directory, make if not already exist
                        self.get_paths(f'https://api.github.com/repos/drumbart/VFA-27_Ready_Room/contents/{item["path"]}')
                else:  # File is not a directory and does not already exist --> download
                    # self.download_file(item)
                    # self.download_q.put(item)
                    for idx, file in enumerate(self.liveries):
                        exists = False
                        if file["path"].replace("/", "") == item["path"].replace("/", ""):
                            exists = True
                            self.liveries[idx] = {"path": '/' + item["path"],
                                                    "date": int(time.time()),
                                                    "delete": delete,
                                                    "size": item["size"]}
                            break
                    if exists == False:
                        add_liveries.append({"path": '/' + item["path"],
                                                "date": int(time.time()),
                                                "delete": delete,
                                                "size": item["size"]})
            for i, file in enumerate(add_liveries):
                self.liveries.append(file)

        except FileExistsError:
            print("API rate limit exceeded. Script can only be run once an hour!")


    def download_file(self, item):
        print(item["path"])
        print(f'Downloading {item["path"]}')
        url = DOWNLOAD_URL + item["path"]
        response = requests.get(url, allow_redirects=True)
        try:
            f = open(DOWNLOAD_PATH + item["path"], 'w+')
            f.close()
            open(DOWNLOAD_PATH + item["path"], 'wb').write(response.content)
        except FileNotFoundError:
            self.make_prev_dirs(DOWNLOAD_PATH + item["path"], False)


        # self.bytes_downloaded =+ int(item["size"])
        # self.files_downloaded =+ 1


    def make_prev_dirs(self, path, is_folder: bool):
        print("MAKING DIR AT " + path)
        dirs = path.split("/")
        if is_folder is False:
            del dirs[-1]


        dirs[0] = dirs[0].replace("/", "")
        for idx, dir_path in enumerate(dirs):
            path = ""
            for x, dir_path in enumerate(dirs):
                if x <= idx:
                    path = path + "/" + dir_path
            if path[0] == "/":
                path = path[1:]
                
            if os.path.isdir(path) is False:
                os.mkdir(path)
                print(f'Making directory {path}')
                
        # if is_folder is False:
        #     f = open(PATH + path, 'w+')
        #     f.close()
        #     url = DOWNLOAD_URL + path
        #     response = requests.get(url, allow_redirects=True)
        #     open(PATH + path, 'wb').write(response.content)

    
    def getKneeboards(self):
        f = open(PATH + 'KneeboardConfig.json')
        data = json.load(f)

        kneeboard_families = data

        for group in kneeboard_families:
            for subcat in group["subcat"]:
                    for file in subcat["files"]:
                        file_path = group["parent"] + file
                        if subcat["default"] == True:
                            try:
                                if int(os.path.getmtime(PATH + file_path)) < subcat["date"]:  
                                    print(f"Updating {file_path}")

                                    url = DOWNLOAD_URL + file_path
                                    response = requests.get(url, allow_redirects=True)
                                    try:
                                        f = open(DOWNLOAD_PATH + file_path, 'w+')
                                        f.close()
                                        open(DOWNLOAD_PATH + file_path, 'wb').write(response.content)
                                    except FileNotFoundError or PermissionError:
                                        try:
                                            self.make_prev_dirs(DOWNLOAD_PATH + file_path, False)
                                        except PermissionError:
                                            pass
                                        f = open(DOWNLOAD_PATH + file_path, 'w+')
                                        f.close()
                                        open(DOWNLOAD_PATH + file_path, 'wb').write(response.content)
                                    self.files_downloaded =+ 1
                                else:
                                    print("Kneeboard is already downloaded and up to date!")

                            except FileNotFoundError:
                                print(f"Downloading {file_path}")
                                url = DOWNLOAD_URL + file_path
                                response = requests.get(url, allow_redirects=True)
                                try:
                                    f = open(DOWNLOAD_PATH + file_path, 'w+')
                                    f.close()
                                    open(DOWNLOAD_PATH + file_path, 'wb').write(response.content)
                                except FileNotFoundError or PermissionError:
                                    try:
                                        self.make_prev_dirs(DOWNLOAD_PATH + file_path, False)
                                    except PermissionError:
                                        pass
                                    f = open(DOWNLOAD_PATH + file_path, 'w+')
                                    f.close()
                                    open(DOWNLOAD_PATH + file_path, 'wb').write(response.content)
                                    self.files_downloaded =+ 1

                        elif subcat["default"] == False:
                            try:
                                os.remove(DOWNLOAD_PATH + file_path)
                                print(f"Removing {file_path}")
                            except FileNotFoundError:
                                pass

    def getEventKneeboards(self, flight: str):
        url = f'https://api.github.com/repos/MrRavenMan/WCDownloader/contents/eventKneeboards/{flight}'
        response = requests.get(url)
        items = response.json()

        kneeboards = []

        try:
            for item in items:
                kneeboards.append(item["name"])

                # url = DOWNLOAD_URL + item["path"]
                print(f"Downloading kneeboard: {item['name']} for {flight}")
                url = f'https://api.github.com/repos/MrRavenMan/WCDownloader/contents/eventKneeboards/{flight}/{item["name"]}'
                response = requests.get(url, allow_redirects=True)
                try:
                    f = open(DOWNLOAD_PATH + "/Kneeboard/" +  item["name"], 'w+')
                    f.close()
                    open(DOWNLOAD_PATH + "/Kneeboard/" +  item["name"], 'wb').write(response.content)
                except FileNotFoundError:
                    self.make_prev_dirs(DOWNLOAD_PATH + "/Kneeboard/", False)
                    f = open(DOWNLOAD_PATH + "/Kneeboard/" +  item["name"], 'w+')
                    f.close()
                    open(DOWNLOAD_PATH + "/Kneeboard/" +  item["name"], 'wb').write(response.content)
        except FileExistsError:
            print("API rate limit exceeded. Script can only be run once an hour!")



    def removeEventKneeboards(self, flight):
        url = f'https://api.github.com/repos/MrRavenMan/WCDownloader/contents/eventKneeboards/{flight}'
        response = requests.get(url)
        items = response.json()

        kneeboards = []

        try:
            for item in items:
                kneeboards.append(item["name"])

                # url = DOWNLOAD_URL + item["path"]
                print(f"Removing kneeboard: {item['name']} for {flight}")
                try:
                    os.remove(DOWNLOAD_PATH + "/Kneeboard/" +  item["name"])
                except FileNotFoundError:
                    pass
        except FileExistsError:
            print("API rate limit exceeded. Script can only be run once an hour!")