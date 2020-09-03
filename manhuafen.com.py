from selenium import webdriver
import time
import urllib.request
import os
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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
                       for x in os.listdir(folder_name)]
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

            '''
    while True:
        image = driver.find_element_by_id('images')
        current_page_no = int(image.find_element_by_tag_name(
            'p').text.split('/')[0].strip('('))
        page_number = int(image.find_element_by_tag_name(
            'p').text.split('/')[1].strip(')'))

        # highLightElement(driver, image)
        image_src = image.find_element_by_tag_name('img')
        highLightElement(driver, image_src)
        image_url = image_src.get_attribute('src')

        urllib.request.urlretrieve(
            image_url, os.path.join(folder_name, str(current_page_no)+'.jpg'))
        if current_page_no == page_number:
            break
        driver.find_element_by_class_name('img_land_next').click()
        try:
            ele = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(locator))
        except:
            print('cannot find image.')
'''


def download_page(driver, chapter_url, current_page_no, folder_name):
    url = chapter_url+'?p='+str(current_page_no)
    # print(f'downloading page {current_page_no}')
    driver.get(url)
    locator = (By.ID, 'images')
    try:
        image = WebDriverWait(driver, 10, 0.4).until(
            EC.presence_of_element_located(locator))
        # image = driver.find_element_by_id('images')
        image_src = image.find_element_by_tag_name('img')
        image_url = image_src.get_attribute('src')
        urllib.request.urlretrieve(
            image_url, os.path.join(folder_name, str(current_page_no)+'.jpg'))
    except:
        print(f'can not find image {current_page_no}')
        with open(os.path.join(folder_name, '.incomplete'), 'a') as f:
            f.write(current_page_no)


def list_lock(driver, chapter_url, download_list, folder_name, lock):
    while download_list:
        lock.acquire()
        current_page_no = download_list.pop(0)
        print(f'{download_list} downloading...',end='\r')
        # random.choice(range(len(download_list))))
        lock.release()
        download_page(driver, chapter_url, current_page_no, folder_name)
    if os.path.exists(os.path.join(folder_name,'.incomplete')) and not download_list:
        os.remove(os.path.join(folder_name,'.incomplete'))


def thred_download(driver_list, chapter_url, folder_name, page_number):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    download_list = get_download_page_list(folder_name, page_number)
    lock = threading.Lock()
    threads = []
    for driver in driver_list:
        threads.append(threading.Thread(target=list_lock, args=(
            driver, chapter_url, download_list, folder_name, lock)))
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
    # t1 = threading.Thread(target=list_lock, args=(
    #     driver1, chapter_url, download_list, folder_name, lock))
    # t2 = threading.Thread(target=list_lock, args=(
    #     driver2, chapter_url, download_list, folder_name, lock))
    # t3 = threading.Thread(target=list_lock, args=(
    #     driver3, chapter_url, download_list, folder_name, lock))
    # t4 = threading.Thread(target=list_lock, args=(
    #     driver4, chapter_url, download_list, folder_name, lock))

    # t1.start()
    # t2.start()
    # t3.start()
    # t4.start()
    # t1.join()
    # t2.join()
    # t3.join()
    # t4.join()


if __name__ == "__main__":

    # driver = webdriver.Chrome()
    # download_page(
    #     driver, 'https://www.manhuafen.com/comic/2252/457229.html', 4, '125话')

    url = 'https://www.manhuafen.com/comic/2252/'
    driver = webdriver.Chrome()
    driver1 = webdriver.Chrome()
    driver2 = webdriver.Chrome()
    driver3 = webdriver.Chrome()
    driver4 = webdriver.Chrome()
    # driver = webdriver.Firefox()
    driver.get(url)
    chapter_block = driver.find_element_by_id('chapter-list-1')
    chapter_list = chapter_block.find_elements_by_tag_name('li')

    thread_list = [driver1, driver2, driver3, driver4]

    # for chapter in chapter_list:
    #     chapter.click()
    # chapter1 = chapter_list[1]
    for chapter in chapter_list:
        folder_name = chapter.find_element_by_class_name('list_con_zj').text
        if os.path.exists(folder_name):
            if os.path.exists(os.path.join(folder_name, '.complete')):
                continue
            elif os.path.exists(os.path.join(folder_name, '.incomplete')):
                chapter_url = chapter.get_attribute('href')
                page_number = 0
                with open(os.path.join(folder_name, '.incomplete'), 'r') as f:
                    page_number = int(f.read())
                thred_download(thread_list, chapter_url,
                               folder_name, page_number)
        chapter.click()
        content_window = driver.current_window_handle
        all_handles = driver.window_handles

        # 进入章节
        for handle in all_handles:
            if handle != content_window:
                driver.switch_to.window(handle)

        locator = (By.ID, 'images')
        try:
            image = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(locator))
            page_number = int(image.find_element_by_tag_name(
                'p').text.split('/')[1].strip(')'))
            print(driver.title)
            chapter_url = driver.current_url
            thred_download(thread_list, chapter_url, folder_name, page_number)
        except:
            print('can not find images')
        # print(driver.title)
        driver.close()
        driver.switch_to.window(content_window)
