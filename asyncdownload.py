import asyncio
import random
import os
import urllib.request
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException


async def initiate_bowser():
    ch_options = webdriver.ChromeOptions()
    ch_options.add_argument('-headless')
    ch_options.add_argument('blink-settings=imagesEnabled=false')
    ff_options = webdriver.FirefoxOptions()
    ff_options.add_argument('-headless')
    ff_options.set_preference('permissions.default.image', 2)
    print('initiating browser...')
    bowser = None
    try:
        bowser = webdriver.Firefox(options=ff_options)
        print('Firefox initiated.')
    except WebDriverException:
        try:
            bowser = webdriver.Chrome(options=ch_options)
            print('Chrome initiated.')
        except WebDriverException:
            print('Please install driver properly')
            os._exit(-1)
    return bowser


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


async def get_online_download_list(folder_name, chapter_url, browser):
    try:
        os.mkdir(folder_name)
    except:
        print(f'{folder_name} already exists.')
    print(f'parsing {folder_name}...')
    browser.get(chapter_url)
    locator = (By.ID, 'images')
    try:
        image = WebDriverWait(browser, 10, 0.4).until(
            EC.presence_of_element_located(locator))
        image_src = image.find_element_by_tag_name('img')
        image_url = image_src.get_attribute('src')
        image_list = browser.execute_script(
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
            return src_list
        else:
            print(f'{folder_name} download complete.')
            return

    except:
        print(f'a error occured when parsing {folder_name}.')
        os._exit(-1)

    print(f'parsing {folder_name} complete.')


async def download(page):
    folder_name, image_src, idx = page
    print(f'downloading {folder_name} page {idx}')
    try:
        urllib.request.urlretrieve(image_src, os.path.join(
            folder_name, str(idx)+'.jpg'))
    except HTTPError:
        print(f'failed to download {folder_name} page {idx}')
    except urllib.error.ContentTooShortError as err:
        print(
            f'failed to download {folder_name} page {idx} for {err}')


async def produce(chapter_queue, page_queue, browser_list):
    while True:
        chapter = await chapter_queue.get()
        chapter_url, folder_name = chapter
        page_list = []
        if os.path.exists(folder_name) and os.path.exists(os.path.join(folder_name, '.incomplete')):
            page_list = get_local_download_list(folder_name)

        else:

            browser = None
            if browser_list:
                browser = browser_list.pop()
            else:
                browser = await initiate_bowser()
            browser_list.append(browser)

            page_list = await get_online_download_list(
                folder_name, chapter_url, browser)
        if page_list:
            for page in page_list:
                await page_queue.put(page)
                print(f'add {page[0]} page {page[2]}.')
                await asyncio.sleep(0.01)

        chapter_queue.task_done()


async def consume(page_queue):
    while True:
        page = await page_queue.get()
        await download(page)
        # await asyncio.sleep(5)
        page_queue.task_done()


async def get_chapter(chapter_queue):
    await chapter_queue.put(['https://www.manhuafen.com/comic/39/18774.html', os.path.join('进击的巨人漫画', '90话')])
    await chapter_queue.put(['https://www.manhuafen.com/comic/39/18775.html', os.path.join('进击的巨人漫画', '91话')])
    await chapter_queue.put(['https://www.manhuafen.com/comic/39/18776.html', os.path.join('进击的巨人漫画', '92话')])
    await chapter_queue.put(['https://www.manhuafen.com/comic/39/18777.html', os.path.join('进击的巨人漫画', '93话')])
    await chapter_queue.put(['https://www.manhuafen.com/comic/39/18778.html', os.path.join('进击的巨人漫画', '94话')])


async def run():
    chapter_queue = asyncio.Queue()

    # await chapter_queue.put(['https://www.manhuafen.com/comic/39/18774.html', os.path.join('进击的巨人漫画', '90话')])
    # await chapter_queue.put(['https://www.manhuafen.com/comic/39/18775.html', os.path.join('进击的巨人漫画', '91话')])
    # await chapter_queue.put(['https://www.manhuafen.com/comic/39/18776.html', os.path.join('进击的巨人漫画', '92话')])
    # await chapter_queue.put(['https://www.manhuafen.com/comic/39/18777.html', os.path.join('进击的巨人漫画', '93话')])
    # await chapter_queue.put(['https://www.manhuafen.com/comic/39/18778.html', os.path.join('进击的巨人漫画', '94话')])

    page_queue = asyncio.Queue()
    driver_list = []
    # schedule the consumer
    consumer_n = 3
    consumers = []
    for i in range(consumer_n):
        consumers.append(asyncio.ensure_future(consume(page_queue)))

    # run the producer and wait for completion
    # producer = asyncio.ensure_future(
    
    producer = asyncio.ensure_future(
        produce(chapter_queue, page_queue, driver_list))
    await get_chapter(chapter_queue)
    # wait until the consumer has processed all items

    # await page_queue.join()
    await chapter_queue.join()
    # the consumer is still awaiting for an item, cancel it
    await page_queue.join()
    producer.cancel()
    for consumer in consumers:
        consumer.cancel()  # run the producer and wait for completion

    if driver_list:
        for driver in driver_list:
            driver.quit()


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
