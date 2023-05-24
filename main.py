import os
import pickle
import time
import urllib.parse
import requests
from selenium import webdriver

# Define cookies file
cookie_file = "run/cookies.pkl"
url = "https://www.bilibili.com/"
uid = 0

def first(list, condition):
    for element in list:
        if condition(element):
            return element
    return None

# Check if cookies file exists
if os.path.exists(cookie_file):
    # Load cookies from file
    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)

    # Open browser with existing cookies
    browser = webdriver.Chrome()
    browser.get(url)
    for cookie in cookies:
        browser.add_cookie(cookie)
    browser.get(url)
else:
    if not os.path.exists('run'):
        os.makedirs('run')

    browser = webdriver.Chrome()
    browser.get(url)

    # Wait for user to log in
    while first(browser.get_cookies(), lambda cookie: cookie['name'] == 'DedeUserID') is None:
        time.sleep(1)

    # Save cookies to file
    with open(cookie_file, "wb") as f:
        pickle.dump(browser.get_cookies(), f)

cookie_dict = {}
for cookie in browser.get_cookies():
    cookie_dict[cookie['name']] = cookie['value']
    cookie_str = urllib.parse.urlencode(cookie_dict)
uid = int(cookie_dict['DedeUserID'])
print(f'Your uid is {uid}')
browser.quit()
# then use requests to get the json

json = requests.get(f'https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={uid}', cookies=cookie_dict).json()
if json['code'] != 0:
    print('Error: ' + json['message'])
    print(json)
    exit(1)

class FavFolder:
    def __init__(self, id, fid, mid, count, title, attr):
        self.id = id
        self.fid = fid
        self.mid = mid
        self.count = count
        self.title = title
        self.attr = attr
        self.medias: list[FavVideo] = []

class FavVideo:
    def __init__(self, link, bvid, up_id, up_name, title):
        self.link = link
        self.bvid = bvid
        self.up_id = up_id
        self.up_name = up_name
        self.title = title

    def __str__(self):
        return f'{self.title}({self.bvid}) by {self.up_name}'

favs: list[FavFolder] = []

for je in json['data']['list']:
    favs.append(FavFolder(
        id=je['id'],
        fid=je['fid'],
        mid=je['mid'],
        count=je['media_count'],
        title=je['title'],
        attr=je['attr']
    ))

print(f'You have {len(favs)} folders')
for fav in favs:
    pages = fav.count // 20 + 1
    pn = 1
    while pn <= pages:
        json = requests.get(f'https://api.bilibili.com/x/v3/fav/resource/list?media_id={fav.id}&pn={pn}&ps=20', cookies=cookie_dict).json()
        if json['code'] != 0:
            print('Error: ' + json['message'])
            print(json)
            exit(1)
        for je in json['data']['medias']:
            fav.medias.append(FavVideo(
                link=je['link'],
                bvid=je['bvid'],
                up_id=je['upper']['mid'],
                up_name=je['upper']['name'],
                title=je['title']
            ))
        pn += 1
    print(f'Folder {fav.title} has {len(fav.medias)} videos: {", ".join(map(str, fav.medias))}')
total = sum(map(lambda fav: len(fav.medias), favs))
current = 0
print('Start downloading...')
tag_dict = {}
for fav in favs:
    for m in fav.medias:
        time.sleep(0.5)
        'https://api.bilibili.com/x/tag/archive/tags?bvid=BV1c14y1p7VL'
        json = requests.get(f'https://api.bilibili.com/x/tag/archive/tags?bvid={m.bvid}', cookies=cookie_dict).json()
        # B站新api，不确定aid和cid来源
        'https://api.bilibili.com/x/web-interface/view/detail/tag?aid=868850306&cid=1136784190'
        if json['code'] != 0:
            print('Error: ' + json['message'])
            print(json)
            tags = list(tag_dict.keys())
            # sort by values
            tags.sort(key=lambda tag: len(tag_dict[tag]), reverse=True)
            print(f'You have {len(tags)} tags')
            for tag in tags:
                print(f'Tag {tag} has {len(tag_dict[tag])} videos: {", ".join(map(str, tag_dict[tag]))}')
            exit(1)

        for je in json['data']:
            if je['tag_name'] not in tag_dict:
                tag_dict[je['tag_name']] = []
            tag_dict[je['tag_name']].append(m)
        current += 1
        print(f'\r{current}/{total} done')

tags = list(tag_dict.keys())
# sort by values
tags.sort(key=lambda tag: len(tag_dict[tag]), reverse=True)
print(f'You have {len(tags)} tags')
for tag in tags:
    print(f'Tag {tag} has {len(tag_dict[tag])} videos: {", ".join(map(str, tag_dict[tag]))}')

print('Done')


