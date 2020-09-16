from selenium import webdriver
import time
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin
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


def image_retrieve(src_list, lock):
    while(src_list):
        lock.acquire()
        folder_name, image_src, idx = src_list.pop(-1)
        lock.release()
        try:
            print(
                f'downloading {folder_name} page {idx}                ', end='\r')
            if len(image_src.split('http')) > 2:
                image_src = 'http'+image_src.split('http')[-1]
            urllib.request.urlretrieve(
                image_src, os.path.join(folder_name, str(idx)+'.jpg'))
        except HTTPError:
            print(
                f'failed to download {folder_name} page {idx}      ')
            # return [folder_name, image_src, idx]


def get_chapter_image_list(driver, chapter_url, folder_name):
    if os.path.exists(folder_name):
        if os.path.exists(os.path.join(folder_name, 'complete')):
            return
        else:
            downloaded_list = [int(os.path.splitext(x)[0])
                               for x in os.listdir(folder_name) if x[0] != '.']
            with open(os.path.join(folder_name, '.incomplete'), 'r', encoding='utf-8') as f:
                src_list = []
                for line in f:
                    folder_name = line.strip('\n').split('\t')[0]
                    image_url = line.strip('\n').split('\t')[1]
                    page_no = int(line.strip('\n').split('\t')[2])
                    if page_no not in downloaded_list:
                        src_list.append([folder_name, image_url, page_no])
            return src_list
    else:
        driver.get(chapter_url)
        locator = (By.ID, 'images')

        try:
            image = WebDriverWait(driver, 10, 0.4).until(
                EC.presence_of_element_located(locator))
            image_src = image.find_element_by_tag_name('img')
            image_url = image_src.get_attribute('src')
            image_list = driver.execute_script("return chapterImages")

            src_list = [[folder_name, os.path.join(os.path.split(image_url)[0], x), idx]
                        for idx, x in enumerate(image_list, 1) if 'http' not in x]
            if not src_list:
                src_list = [[folder_name, x, idx]
                            for idx, x in enumerate(image_list, 1)]
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
                with open(os.path.join(folder_name, '.incomplete'), 'a') as f:
                    for src in src_list:
                        f.write(f'{src[0]}\t{src[1]}\t{src[2]}\n')
            return src_list
        except:
            print(f'{folder_name} download complete.')
            return


def retrieve_list_lock(driver, task_list, lock, src_list):

    while task_list:
        lock.acquire()
        chapter_url, current_page_no, folder_name = task_list.pop(-1)
        lock.release()

        if not current_page_no:
            chapter_src_list = get_chapter_image_list(
                driver, chapter_url, folder_name)
            if chapter_src_list:
                lock.acquire()
                src_list += chapter_src_list
                lock.release()
            else:
                print(f'{folder_name} download complete.')

        else:
            pass


def thred_get_src(driver_list, task_list):
    lock = threading.Lock()
    threads = []
    src_list = []
    for driver in driver_list:
        threads.append(threading.Thread(target=retrieve_list_lock, args=(
            driver, task_list,  lock, src_list)))
    for td in threads:
        td.start()
    for td in threads:
        td.join()

    return src_list


def thread_image_retrieve(src_list):
    thread_number = 4
    lock = threading.Lock()
    threads = []
    for i in range(thread_number):
        threads.append(threading.Thread(
            target=image_retrieve, args=(src_list, lock)))

    for td in threads:
        td.start()
    for td in threads:
        td.join()


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
        for idx, task in enumerate(full_task_list):
            print(f'序号:\t{idx}:\t{task[2]}')
        try:
            task_idx = int(input('输入下载序号，默认下载最新回:'))
        except ValueError:
            task_idx = 0

        task_list = [x for x in full_task_list if x[2]
                     == full_task_list[task_idx][2]]

    driver_list = []
    for i in range(driver_number):
        driver_list.append(wd())
    src_list = thred_get_src(driver_list, task_list)

    for driver in driver_list:
        driver.quit()
    return src_list


if __name__ == "__main__":

    src_list = user_interface()
    thread_image_retrieve(src_list)
