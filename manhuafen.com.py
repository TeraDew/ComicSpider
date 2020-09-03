from selenium import webdriver
import time
import urllib.request
import os


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


def download_chapter(driver, folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    else:
        return

    while driver.find_element_by_class_name('img_land_next'):
        image = driver.find_element_by_id('images')
        current_page_no = image.find_element_by_tag_name(
            'p').text.split('/')[0].strip('(')
        page_number = image.find_element_by_tag_name(
            'p').text.split('/')[1].strip(')')

        # highLightElement(driver, image)
        image_src = image.find_element_by_tag_name('img')
        highLightElement(driver, image_src)
        image_url = image_src.get_attribute('src')

        urllib.request.urlretrieve(
            image_url, os.path.join(folder_name, str(current_page_no)+'.jpg'))
        if current_page_no == page_number:
            break
        else:
            driver.find_element_by_class_name('img_land_next').click()



if __name__ == "__main__":
    url = 'https://www.manhuafen.com/comic/2252/'
    driver = webdriver.Chrome()
    driver.get(url)
    chapter_block = driver.find_element_by_id('chapter-list-1')
    chapter_list = chapter_block.find_elements_by_tag_name('li')
    # for chapter in chapter_list:
    #     chapter.click()
    chapter1 = chapter_list[1]
    for chapter in chapter_list:
        folder_name = chapter.find_element_by_class_name('list_con_zj').text
        chapter.click()
        content_window = driver.current_window_handle
        all_handles = driver.window_handles

        # 进入章节
        for handle in all_handles:
            if handle != content_window:
                driver.switch_to.window(handle)

        download_chapter(driver, folder_name)
        # print(driver.title)
        driver.close()
        driver.switch_to.window(content_window)

