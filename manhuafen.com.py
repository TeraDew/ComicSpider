from selenium import webdriver
import time
import urllib.request
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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


if __name__ == "__main__":

    url = 'https://www.manhuafen.com/comic/2252/'
    driver = webdriver.Chrome()
    # driver = webdriver.Firefox()
    driver.get(url)
    chapter_block = driver.find_element_by_id('chapter-list-1')
    chapter_list = chapter_block.find_elements_by_tag_name('li')
    # for chapter in chapter_list:
    #     chapter.click()
    # chapter1 = chapter_list[1]
    for chapter in chapter_list:
        folder_name = chapter.find_element_by_class_name('list_con_zj').text
        chapter.click()
        content_window = driver.current_window_handle
        all_handles = driver.window_handles

        # 进入章节
        for handle in all_handles:
            if handle != content_window:
                driver.switch_to.window(handle)

        locator = (By.ID, 'images')
        try:
            ele = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(locator))
            print(driver.title)
            download_chapter(driver, folder_name)
        except:
            print('can not find images')
        # print(driver.title)
        driver.close()
        driver.switch_to.window(content_window)
