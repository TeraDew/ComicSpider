from selenium import webdriver
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


def image_retrieve(src_list, lock, sleep_lock, sleep_time, parsing_flag):
    sleep_limit = 65
    while(src_list and sleep_time < sleep_limit):
        lock.acquire()
        folder_name, image_src, idx = src_list.pop(-1)
        lock.release()
        try:
            print(
                f'downloading {folder_name} page {idx}                ', end='\r')
            urllib.request.urlretrieve(
                image_src, os.path.join(folder_name, str(idx)+'.jpg'))
            sleep_time = 1
        except HTTPError:
            print(
                f'failed to download {folder_name} page {idx}      ')
            sleep_lock.acquire()
            sleep_time *= 2
            print(
                f'download thread sleep for {sleep_time} seconds         ', end='\r')
            time.sleep(sleep_time)
            src_list.append([folder_name, image_src, idx])
            sleep_lock.release()
        except urllib.error.ContentTooShortError as err:
            print(f'failed to download {folder_name} page {idx} for {err}')

    if((not src_list) and sleep_time < sleep_limit and parsing_flag):
        sleep_lock.acquire()
        sleep_time *= 2
        print(
            f'download thread sleep for {sleep_time} seconds waiting for task  ', end='\r')
        time.sleep(sleep_time)
        sleep_lock.release()
        image_retrieve(src_list, lock, sleep_lock, sleep_time, parsing_flag)
    elif(sleep_time > sleep_limit):
        err_msg = '\n------------------------\nfail to download these pages: \n'+'\n'.join(
            [f'{folder_name} page {idx}' for folder_name, image_src, idx in src_list])+'\nterminationg...'
        print(err_msg)


def get_local_download_list(folder_name):
    if os.path.exists(os.path.join(folder_name, '.complete')):
        return
    else:
        try:
            downloaded_list = [int(os.path.splitext(x)[0])
                               for x in os.listdir(folder_name) if x[0] != '.']
        except:
            print(folder_name)
        with open(os.path.join(folder_name, '.incomplete'), 'r', encoding='utf-8') as f:
            src_list = []
            for line in f:
                folder_name = line.strip('\n').split('\t')[0]
                image_url = line.strip('\n').split('\t')[1]
                page_no = int(line.strip('\n').split('\t')[2])
                if page_no not in downloaded_list:
                    src_list.append([folder_name, image_url, page_no])
        return src_list


def get_chapter_image_list(driver, chapter_url, folder_name):
    if os.path.exists(folder_name):
        return get_local_download_list(folder_name)
    else:
        driver.get(chapter_url)
        locator = (By.ID, 'images')

        try:
            image = WebDriverWait(driver, 10, 0.4).until(
                EC.presence_of_element_located(locator))
            image_src = image.find_element_by_tag_name('img')
            image_url = image_src.get_attribute('src')
            image_list = driver.execute_script("return chapterImages")
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
            return src_list
        except:
            print(f'{folder_name} download complete.')
            return


def retrieve_list_lock(driver, task_list, lock, src_list, parsing_flag):

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
    if not task_list:
        parsing_flag = False


def thred_get_src(driver_number, task_list, wd):

    lock = threading.Lock()
    sleep_lock = threading.Lock()
    download_thread_number = 4
    initial_sleep_time = 1
    threads = []
    src_list = []
    driver_list = []
    parsing_flag = True
    unparsed_chapter_list = [[chapter_url, idx, folder_name] for chapter_url,
                             idx, folder_name in task_list if not os.path.exists(folder_name)]
    if unparsed_chapter_list:
        driver_number = driver_number if driver_number < len(
            unparsed_chapter_list) else len(unparsed_chapter_list)
        for i in range(driver_number):
            driver_list.append(wd())
        for driver in driver_list:
            threads.append(threading.Thread(target=retrieve_list_lock, args=(
                driver, task_list,  lock, src_list, parsing_flag)))

    else:
        parsing_flag = False
        for chapter_url, idx, folder_name in task_list:
            src_list += get_local_download_list(folder_name)
    for i in range(download_thread_number):
        threads.append(threading.Thread(
            target=image_retrieve, args=(src_list, lock, sleep_lock, initial_sleep_time, parsing_flag)))
    for td in threads:
        td.start()
    for td in threads:
        td.join()

    if unparsed_chapter_list:
        for driver in driver_list:
            driver.quit()

    return src_list


def thread_image_retrieve(src_list, other_threads):
    thread_number = 4
    lock = threading.Lock()
    threads = []
    for i in range(thread_number):
        threads.append(threading.Thread(
            target=image_retrieve, args=(src_list, lock, other_threads)))

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


if __name__ == "__main__":

    src_list = user_interface()
