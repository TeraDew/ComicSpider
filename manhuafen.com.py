from selenium import webdriver
import queue
import time
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin, urlparse
import os
import sys
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException
from urllib.error import HTTPError
import random


def highLightElement(driver, element):
    # 封装好的高亮显示页面元素的方法
    # 使用JavaScript代码将传入的页面元素对象的背景颜色和边框颜色分别
    # 设置为绿色和红色
    driver.execute_script("arguments[0].setAttribute('style',arguments[1]);",
                          element, "background:green ;border:2px solid red;")


class Consumer(threading.Thread):
    def __init__(self, name, queue):
        threading.Thread.__init__(self, name=name)
        self.data = queue

    def run(self):
        while True:
            val = self.data.get()
            if val:
                folder_name, image_src, idx = val
                print(f'downloading {folder_name} page {idx}')
                try:
                    urllib.request.urlretrieve(image_src, os.path.join(
                        folder_name, str(idx)+'.jpg'))
                except HTTPError:
                    print(f'failed to download {folder_name} page {idx}')
                except urllib.error.ContentTooShortError as err:
                    print(
                        f'failed to download {folder_name} page {idx} for {err}')
            elif(val == None):
                self.data.put(val)
                break
            else:
                time.sleep(0.5)
        print(f'{self.getName()} download compelte.')


def get_local_download_list(folder_name):
    if os.path.exists(os.path.join(folder_name, '.complete')):
        return
    else:
        try:
            downloaded_list = [int(os.path.splitext(x)[0])
                               for x in os.listdir(folder_name) if x[0] != '.']
            src_list = []
            with open(os.path.join(folder_name, '.incomplete'), 'r', encoding='utf-8') as f:
                for line in f:
                    folder_name = line.strip('\n').split('\t')[0]
                    image_url = line.strip('\n').split('\t')[1]
                    page_no = int(line.strip('\n').split('\t')[2])
                    if page_no not in downloaded_list:
                        src_list.append([folder_name, image_url, page_no])
            if not src_list:
                print(f'{folder_name} download complete.')
            return src_list

        except ValueError:
            print(f'error occured in{folder_name}.')
            return []


class LocalProducer(threading.Thread):
    def __init__(self, name, queue, task_queue):
        threading.Thread.__init__(self, name=name)
        self.data = queue
        self.task_queue = task_queue

    def run(self):
        while True:
            task_val = self.task_queue.get()
            if task_val:
                chapter_url, current_page_no, folder_name = task_val
                self.add_local_download_list(folder_name)
                self.add_stop_flag()
            elif(task_val == None):
                self.task_queue.put(task_val)
                break
            else:
                time.sleep(0.5)

        print(f'Page parse complete')

    def add_stop_flag(self):
        if (self.task_queue.qsize() == 1):
            temp_task = self.task_queue.get()
            if (temp_task == None):
                self.task_queue.put(None)
                self.data.put(None)
            else:
                self.task_queue.put(temp_task)

    def add_local_download_list(self, folder_name):
        if os.path.exists(folder_name):
            src_list = get_local_download_list(folder_name)
            for src_download in src_list:
                self.data.put(src_download)
            return True
        else:
            return False


class OnlineProducer(LocalProducer):
    def __init__(self, name, queue, task_queue, driver):
        LocalProducer.__init__(self, name, queue, task_queue)
        self.driver = driver

    def run(self):
        while True:
            task_val = self.task_queue.get()

            if task_val:
                chapter_url, current_page_no, folder_name = task_val
                if not self.add_local_download_list(folder_name):
                    self.driver.get(chapter_url)
                    locator = (By.ID, 'images')
                    try:
                        image = WebDriverWait(self.driver, 10, 0.4).until(
                            EC.presence_of_element_located(locator))
                        image_src = image.find_element_by_tag_name('img')
                        image_url = image_src.get_attribute('src')
                        image_list = self.driver.execute_script(
                            "return chapterImages")
                        src_list = []
                        for idx, page_image_url in enumerate(image_list, 1):
                            if urlparse(page_image_url).netloc:
                                src_list.append([folder_name,
                                                 image_url.split(urlparse(page_image_url).netloc)[
                                                     0]+urlparse(page_image_url).netloc+page_image_url.split(urlparse(page_image_url).netloc)[-1],
                                                 idx])
                            else:
                                src_list.append([folder_name,
                                                 os.path.join(os.path.split(image_url)[0],
                                                              page_image_url), idx])

                        if not os.path.exists(folder_name):
                            os.mkdir(folder_name)
                            with open(os.path.join(folder_name, '.incomplete'), 'a', encoding='utf-8') as f:
                                for src in src_list:
                                    f.write(f'{src[0]}\t{src[1]}\t{src[2]}\n')
                        for src_download in src_list:
                            self.data.put(src_download)

                    except:
                        print(f'{folder_name} download complete.')
                        return
                    self.add_stop_flag()
            elif(task_val == None):
                self.task_queue.put(task_val)
                break
            else:
                time.sleep(0.5)
        self.driver.quit()


class TaskProducer(threading.Thread):
    def __init__(self, name, online_q, offline_q, url):
        threading.Thread.__init__(self, name=name)
        self.oneline_q = online_q
        self.offline_q = offline_q
        self.url = url

    def run(self):
        domain_url = 'https://www.manhuafen.com'
        html = urllib.request.urlopen(self.url)
        soup = BeautifulSoup(html.read(), "html.parser")

        chapter_list = soup.findAll('span', {'class': 'list_con_zj'})
        comic_name = soup.title.text.split(
            '-')[0] if len(soup.title.text.split('-')) > 1 else soup.title.text
        if not os.path.exists(comic_name):
            os.mkdir(comic_name)
        for chapter in chapter_list:
            chapter_name = chapter.text.strip()
            folder_name = os.path.join(comic_name, chapter_name)
            chapter_url = urljoin(domain_url, chapter.parent.get('href'))
            if os.path.exists(folder_name):
                self.offline_q.put([chapter_url, 0, folder_name])
            else:
                self.offline_q.put([chapter_url, 0, folder_name])
        self.oneline_q.put(None)
        self.offline_q.put(None)


def get_content_urllib(url):
    domain_url = 'https://www.manhuafen.com'
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html.read(), "html.parser")

    chapter_list = soup.findAll('span', {'class': 'list_con_zj'})
    comic_name = soup.title.text.split(
        '-')[0] if len(soup.title.text.split('-')) > 1 else soup.title.text
    if not os.path.exists(comic_name):
        os.mkdir(comic_name)
    task_list = []
    for chapter in chapter_list:
        chapter_name = chapter.text.strip()
        folder_name = os.path.join(comic_name, chapter_name)
        chapter_url = urljoin(domain_url, chapter.parent.get('href'))
        task_list.append([chapter_url, 0, folder_name])

    return task_list


def user_interface():
    url = input('输入漫画目录的url,形如 https://www.manhuafen.com/comic/1/:')
    if not url:
        print('不知道去哪找？来这里看看：https://www.manhuafen.com/')
        sys.exit(0)
    if url.isdigit():
        url = 'https://www.manhuafen.com/comic/'+url
    try:
        browser = int(input('用什么浏览器?\nChrome请按0，🦊火狐请按1，默认用Chrome:'))
    except ValueError:
        browser = 0
    try:
        download_mod = int(input('全部下载请按0，单回下载请按1，默认全集下载:'))
        download_mod = 1 if download_mod else 0
    except ValueError:
        download_mod = 0
    try:
        driver_number = int(input('输入线程数,默认为2线程:'))
    except ValueError:
        driver_number = 2
    wd = 0
    if browser:
        wd = webdriver.Firefox
    else:
        wd = webdriver.Chrome

    full_task_list = get_content_urllib(url)
    if download_mod == 0:
        task_list = full_task_list
    elif download_mod == 1:
        for idx, task in enumerate(full_task_list, 1):
            print(f'序号:\t{idx}:\t{task[2]}')
        try:
            task_idx = int(input('输入下载序号，默认下载最新回:'))
            task_idx -= 1
        except ValueError:
            task_idx = 0

        task_list = [x for x in full_task_list if x[2]
                     == full_task_list[task_idx][2]]

    src_list = thred_get_src(driver_number, task_list, wd)

    return src_list


def main(task_list,
         driver_number=2,
         url='https://www.manhuafen.com/comic/856',
         download_range=(-62, -60)):
    online_q = queue.Queue()
    offline_q = queue.Queue()
    src_q = queue.Queue()

    ch_options = webdriver.ChromeOptions()
    ch_options.add_argument('-headless')
    ch_options.add_argument('blink-settings=imagesEnabled=false')
    ff_options = webdriver.FirefoxOptions()
    ff_options.add_argument('-headless')
    ff_options.set_preference('permissions.default.image', 2)

    threads = []

    if not task_list:
        temp_list = get_content_urllib(url)

    range_start, range_end = download_range
    if range_start < 0:
        range_start = len(temp_list)+range_start
    if 0 >= range_end:
        range_end = len(temp_list)+range_end
    task_list = [x for idx, x in enumerate(
        temp_list, 1) if range_end >= idx >= range_start]

    if not task_list:
        print('input invalid range.')
        return

    unparsed_chapter_list = [[chapter_url, idx, folder_name] for chapter_url,
                             idx, folder_name in task_list if not os.path.exists(folder_name)]
    if unparsed_chapter_list:
        driver_number = driver_number if driver_number < len(
            unparsed_chapter_list) else len(unparsed_chapter_list)

        for task in task_list:
            online_q.put(task)

        online_q.put(None)
        for idx in range(driver_number):
            name = 'OnlineProducer'+str(idx+1)
            try:
                driver = webdriver.Firefox(options=ff_options)
                threads.append(OnlineProducer(
                    name, src_q, online_q, driver))

            except WebDriverException:
                try:
                    driver = webdriver.Chrome(options=ch_options)
                    threads.append(OnlineProducer(
                        name, src_q, online_q, driver))

                except WebDriverException:
                    print('Please install driver properly')

    else:
        for task in task_list:
            offline_q.put(task)
        offline_q.put(None)
        threads.append(LocalProducer('LoalProducer', src_q, offline_q))

    threads.append(Consumer('Consumer1', src_q))
    threads.append(Consumer('Consumer2', src_q))
    threads.append(Consumer('Consumer3', src_q))
    threads.append(Consumer('Consumer4', src_q))

    for td in threads:
        td.start()
    for td in threads:
        td.join()

    if not src_q.empty():
        while True:
            val = src_q.get()
            if val:
                print(val)
            elif (val == None):
                print('download complete.')
                break


if __name__ == "__main__":

    # src_list = user_interface()
    main([])
