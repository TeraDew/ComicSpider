from selenium import webdriver
import queue
import time
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin, urlparse
import os
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException
from urllib.error import HTTPError


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


class Producer(threading.Thread):
    def __init__(self, name, queue, task_queue):
        threading.Thread.__init__(self, name=name)
        self.data = queue
        self.task_queue = task_queue
        self.driver = None

    def run(self):
        while True:
            task_val = self.task_queue.get()

            if task_val:
                chapter_url, current_page_no, folder_name = task_val
                if not self.add_local_download_list(folder_name):
                    if self.driver == None:
                        self.initiate_driver()
                    self.add_online_download_list(chapter_url, folder_name)
                self.add_stop_flag()
            elif(task_val == None):
                self.task_queue.put(task_val)
                break
            else:
                time.sleep(0.5)
        self.destroy_driver()
        print(f'chapters parse complete')

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
            os.mkdir(folder_name)
            return False

    def initiate_driver(self):
        ch_options = webdriver.ChromeOptions()
        ch_options.add_argument('-headless')
        ch_options.add_argument('blink-settings=imagesEnabled=false')
        ff_options = webdriver.FirefoxOptions()
        ff_options.add_argument('-headless')
        ff_options.set_preference('permissions.default.image', 2)
        print(f'{self.getName()} is initiating browser...')
        try:
            self.driver = webdriver.Firefox(options=ff_options)
            print('Firefox initiated.')
        except WebDriverException:
            try:
                self.driver = webdriver.Chrome(options=ch_options)
                print('Chrome initiated.')
            except WebDriverException:
                print('Please install driver properly')
                os._exit(-1)

    def destroy_driver(self):
        if self.driver != None:
            self.driver.quit()

    def add_online_download_list(self, chapter_url, folder_name):
        print(f'正在获取{folder_name}的页面...')
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
            if src_list:
                with open(os.path.join(folder_name, '.incomplete'), 'a', encoding='utf-8') as f:
                    for src in src_list:
                        f.write(f'{src[0]}\t{src[1]}\t{src[2]}\n')
                        self.data.put(src)
            else:
                print(f'{folder_name} download complete.')
                return

        except:
            print(f'a error occured when parsing {folder_name}.')
            os._exit(-1)


def get_content_urllib(url):
    domain_url = 'https://www.manhuafen.com'
    print('parsing content...')
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
    print(f'{comic_name} content parsing complete.')
    return task_list


def user_interface():
    url = input('输入漫画目录的url,形如 https://www.manhuafen.com/comic/1/:')
    if not url:
        print('不知道去哪找？来这里看看：https://www.manhuafen.com/')
        os._exit(-1)
    if url.isdigit():
        url = 'https://www.manhuafen.com/comic/'+url

    try:
        download_mod = int(input('全部下载请按0，部分下载请按1，默认全集下载:'))
        download_mod = 1 if download_mod else 0
    except ValueError:
        download_mod = 0

    full_task_list = get_content_urllib(url)

    task_start = 0
    task_end = 0
    if download_mod == 1:
        for idx, task in enumerate(full_task_list, 1):
            print(f'序号:\t{idx}:\t{task[2]}')
        try:
            task_start = int(input('输入下载起始序号:'))
        except ValueError:
            task_start = 0
        try:
            task_end = int(input('输入下载终点序号:'))
        except ValueError:
            task_end = 0

    main(full_task_list, (task_start, task_end), url)


def main(full_task_list,
         download_range=(80, 88),
         url='https://www.manhuafen.com/comic/39',
         producer_number=1
         ):

    if not full_task_list:
        full_task_list = get_content_urllib(url)
    range_start, range_end = download_range
    if range_start < 0:
        range_start = len(full_task_list)+range_start
    if 0 >= range_end:
        range_end = len(full_task_list)+range_end
    task_list = [x for idx, x in enumerate(
        full_task_list, 1) if range_end >= idx >= range_start]

    if not task_list:
        print('input invalid range.')
        return
    
    online_q = queue.Queue()
    src_q = queue.Queue()

    threads = []

    unparsed_chapter_list = [[chapter_url, idx, folder_name] for chapter_url,
                             idx, folder_name in task_list if not os.path.exists(folder_name)]
    producer_number = producer_number if producer_number < len(
        unparsed_chapter_list) and len(unparsed_chapter_list) > 0 else len(unparsed_chapter_list)

    for task in task_list:
        online_q.put(task)
    online_q.put(None)

    for idx in range(producer_number):
        producer = Producer(f'Producer{idx+1}', src_q, online_q)
        threads.append(producer)

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

    user_interface()
