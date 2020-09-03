## ComicSpider 简介
适用于[漫画粉](https://www.manhuafen.com/)的爬虫。
## 运行环境
- python >= 3.6
- selenium
- 浏览器驱动
### selenium 安装
```sh
pip3 install selenium
```
### 浏览器驱动安装
驱动要和浏览器版本对应，下载解压后放到 python3 的安装目录，或者将其所在目录添加到环境变量中。
#### Chrome

```
 https://sites.google.com/a/chromium.org/chromedriver/downloads
```
或
```
http://npm.taobao.org/mirrors/chromedriver/
```

#### Firefox
```
https://github.com/mozilla/geckodriver/releases
```
## 使用方式
在命令行内切换到该目录，输入
```sh
python3 manhuafen.com.py
```
按照提示，依次输入
- 漫画目录url：形如 ```https://www.manhuafen.com/comic/1```
- 浏览器：Chrome 或 Firefox
- 线程数：推荐值为 ```RAM(gb)×2``` 。资源主要消耗于浏览器渲染，一个线程大致等同于一个标签页

运行过程中按 ```ctrl + c``` 退出。下载同一部漫画时自动断点续传。