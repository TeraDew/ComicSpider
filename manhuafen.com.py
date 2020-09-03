from selenium import webdriver
import time
import urllib.request
import os
import sys
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException,TimeoutException
from urllib.error import HTTPError
import random


def write_image(url):
    pass


def open_chapter(url, driver):
    driver.get(url)


def highLightElement(driver, element):
    # 封装好的高亮显示页面元素的方法
    # 使用JavaScript代码将传入的页面元素对象的背景颜色和边框颜色分别
    # 设置为绿色和红色
    driver.execute_script("arguments[0].setAttribute('style',arguments[1]);",
                          element, "background:green ;border:2px solid red;")


def get_download_page_list(folder_name, page_number):
    downloaded_list = [int(os.path.splitext(x)[0])
                       for x in os.listdir(folder_name) if x[0] != '.']
    return [x for x in list(range(1, page_number+1)) if x not in downloaded_list]


def download_chapter(driver, folder_name):
    locator = (By.ID, 'images')
    chapter_url = driver.current_url
    image = driver.find_element_by_id('images')
    page_number = int(image.find_element_by_tag_name(
        'p').text.split('/')[1].strip(')'))
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
        image_src = image.find_element_by_tag_name('img')
        # highLightElement(driver, image_src)
        image_url = image_src.get_attribute('src')
        urllib.request.urlretrieve(
            image_url, os.path.join(folder_name, '1.jpg'))
    download_page_list = get_download_page_list(folder_name, page_number)
    if not download_page_list:
        return

    for i in download_page_list:
        url = chapter_url+'?p='+str(i)
        driver.get(url)
        try:
            image = WebDriverWait(driver, 20, 0.4).until(
                EC.presence_of_element_located(locator))
            # image = driver.find_element_by_id('images')
            image_src = image.find_element_by_tag_name('img')
            image_url = image_src.get_attribute('src')
            urllib.request.urlretrieve(
                image_url, os.path.join(folder_name, str(i)+'.jpg'))
        except:
            print('can not find image')


def download_page(driver, chapter_url, current_page_no, folder_name):
    page_name=0
    if current_page_no == 0:
        url = chapter_url
        page_name=current_page_no+1
    else:
        url = chapter_url+'?p='+str(current_page_no)
        page_name=current_page_no
    # print(f'downloading page {current_page_no}')
    try:
        print(f'downloading {folder_name} page {page_name}                ', end='\r')
        driver.get(url)
    except TimeoutException:
        return
    locator = (By.ID, 'images')
    try:
        image = WebDriverWait(driver, 10, 0.4).until(
            EC.presence_of_element_located(locator))
        # image = driver.find_element_by_id('images')
        image_src = image.find_element_by_tag_name('img')
        image_url = image_src.get_attribute('src')

        if current_page_no == 0:
            try:
                urllib.request.urlretrieve(
                    image_url, os.path.join(folder_name, str(page_name)+'.jpg'))
            except HTTPError:
                print(f'failed to download {folder_name} page {page_name}      ')
                return

            page_number = int(image.find_element_by_tag_name(
                'p').text.split('/')[1].strip(')'))
            return page_number
        else:
            try:
                urllib.request.urlretrieve(
                    image_url, os.path.join(folder_name, str(page_name)+'.jpg'))
            except HTTPError:
                print(f'failed to download {folder_name} page {page_name}      ')
                return
    except:
        print(f'can not find image {current_page_no}')
        with open(os.path.join(folder_name, '.incomplete'), 'a') as f:
            f.write(str(page_name))
        if current_page_no == 0:
            page_number = int(image.find_element_by_tag_name(
                'p').text.split('/')[1].strip(')'))
            return page_number


def list_lock(driver, task_list, folder_name, lock):
    '''
    task_list = [chapter_url, current_page_no, folder_name]
    '''
    while task_list:
        lock.acquire()
        chapter_url, current_page_no, folder_name = task_list.pop(-1)
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        lock.release()
        if not current_page_no:
            page_number = download_page(
                driver, chapter_url, current_page_no, folder_name)
            if page_number:
                with open(os.path.join(folder_name, '.incomplete'), 'w') as f:
                   f.write(str(page_number))
            lock.acquire()
            for i in range(2, page_number+1):
                task_list.append([chapter_url, i, folder_name])
            # random.choice(range(len(download_list))))
            lock.release()
        else:
            download_page(driver, chapter_url, current_page_no, folder_name)
            lock.acquire()
            page_number = 0
            if os.path.exists(os.path.join(folder_name, '.incomplete')):
                with open(os.path.join(folder_name, '.incomplete'), 'r') as f:
                    page_number = int(f.read())
                if len([x for x in os.listdir(folder_name) if 'jpg' in x]) == page_number:
                    os.rename(os.path.join(folder_name, '.incomplete'),
                              os.path.join(folder_name, '.complete'))
                    print(f'{folder_name} completed.                 ')
            lock.release()


def thred_download(driver_list, task_list):

    # download_list = get_download_page_list(folder_name, page_number)
    lock = threading.Lock()
    threads = []
    for driver in driver_list:
        threads.append(threading.Thread(target=list_lock, args=(
            driver, task_list, folder_name, lock)))
    for td in threads:
        td.start()
    for td in threads:
        td.join()
    if os.path.exists(os.path.join(folder_name, '.incomplete')):
        with open(os.path.join(folder_name, '.incomplete'), 'w') as f:
            f.write(int(page_number))
    else:
        with open(os.path.join(folder_name, '.complete'), 'w') as f:
            f.write('')


if __name__ == "__main__":

    # driver = webdriver.Chrome()
    # download_page(
    #     driver, 'https://www.manhuafen.com/comic/2252/457229.html', 4, '125话')

    url = 'https://www.manhuafen.com/comic/2252/'
    url = 'https://www.manhuafen.com/comic/142/'
    url = input('输入漫画目录的url:')
    if not url:
        print('不知道去哪找？来这里看看：https://www.manhuafen.com/comic/142/')
        sys.exit(0)
    try:
        browser = int(input('用什么浏览器?\n，chrome请按0，🦊火狐请按1，默认用chrome:'))
    except ValueError:
        browser=0
    try:
        driver_number = int(input('输入线程数,默认为2线程:'))
    except ValueError:
        driver_number=2
    wd = 0
    if browser:
        wd = webdriver.Firefox
    else:
        wd = webdriver.Chrome
    try:
        print('processing content...                       ',end='\r')
        driver = wd()
    except WebDriverException:
        print('没有装驱动，请阅读说明书')
        sys.exit(0)

    # driver = webdriver.Firefox()
    driver.get(url)
    comic_name = driver.title.split(
        '-')[0] if len(driver.title.split('-')) > 1 else driver.title
    if not os.path.exists(comic_name):
        os.mkdir(comic_name)
    chapter_block = driver.find_element_by_id('chapter-list-1')
    chapter_list = chapter_block.find_elements_by_tag_name('li')

    # for chapter in chapter_list:
    #     chapter.click()
    # chapter1 = chapter_list[1]
    task_list = []
    for chapter in chapter_list:
        chapter_name = chapter.find_element_by_class_name('list_con_zj')
        folder_name = os.path.join(comic_name, chapter_name.text)
        chapter_url = chapter_name.find_element_by_xpath(
            '..').get_attribute('href')
        if os.path.exists(folder_name):
            if os.path.exists(os.path.join(folder_name, '.complete')):
                print(f'{folder_name} completed.')
                continue
            elif os.path.exists(os.path.join(folder_name, '.incomplete')):
                page_number = 0
                with open(os.path.join(folder_name, '.incomplete'), 'r') as f:
                    page_number = int(f.read())
                if page_number == len([x for x in os.listdir(folder_name) if 'jpg' in x]):
                    os.rename(os.path.join(folder_name, '.incomplete'),
                              os.path.join(folder_name, '.complete'))
                    continue
                download_page_list = get_download_page_list(
                    folder_name, page_number)
                for page_to_be_downloaded in download_page_list:
                    task_list.append([
                        chapter_url, page_to_be_downloaded, folder_name])
            else:
                task_list.append([chapter_url, 0, folder_name])
        else:
            task_list.append([chapter_url, 0, folder_name])
    driver.quit()
    print('content processing complete, downloading begin...       ',end='\r')
    driver_list = []
    for i in range(driver_number):
        driver_list.append(wd())
    thred_download(driver_list, task_list)
