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
### 交互模式
在命令行内切换到该目录，输入
```sh
python3 manhuafen.com.py
```
按照提示，依次输入
- 漫画目录url：形如 ```https://www.manhuafen.com/comic/1``` 或直接输入 ```1```
- 下载模式：下载全部章节直接按回车，下载部分章节输入1
- 下载起点和下载终点：0表示最后一章，负值 ```-n``` 表示倒数第```n+1```章。例如输入```0```，```0```表示只下载最后一章。如果上一步选择下载全部章节则没有这一步。
### 无交互模式

```sh
python3 manhuafen.com.py url chapter_start chapter_end
```
```url```：漫画目录网址

```chapter_start```：下载起点

```chapter_end ```:下载终点

下载漫画的最后5章：
```sh
python3 manhuafen.com.py https://www.manhuafen.com/comic/1 -4 0
```


运行过程中按 ```ctrl + c``` 退出。下载同一部漫画时自动断点续传。

## 2020-10-14 更新：

- 新增无交互模式；

- 兼容[漫画呗](https://www.manhuabei.com/)。