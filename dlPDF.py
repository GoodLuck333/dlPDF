import sys
import os
import requests
import re
import json
import time
from contextlib import closing
from PIL import Image
from reportlab.lib.pagesizes import portrait
from reportlab.pdfgen import canvas

class DownLoadImage:
    # header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36'
    }
    # url
    url = 'https://openapi.xxxxxxx.com/getPreview.html?&project_id=1&aid=105373805&view_token=GFoXhBNZy1L6tdKuJDIfx2v61ZC2ens@&callback=jQuery17107788866445399045_1563865966839&_='

    def __init__(self, file_name, remove_pages):
        # 路径
        self.path = 'temp_images'
        # 生成文件名
        self.file_name = file_name
        # 删除页
        self.remove_pages = [int(i) for i in remove_pages.split(',')]
        # 图片总页数
        self.total_pages = -1
        # 图片页数计数器
        self.count = 1

    # 流程信息
    def process_info(self, i, n, info):
        print()
        print('-' * 80)
        print(f'[{i}/{n}]{info}...')
        print('-' * 80 + '\r\n')

    # 创建文件夹
    def create_folder(self, folder):
        if not os.path.exists(folder):
            # 判断文件夹不存在，创建文件夹
            os.mkdir(folder)

    # 获取PDF图片地址
    def get_image_urls(self, url, place):
        # 请求文本数据
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            # JSONP数据处理
            data = json.loads(re.findall('\((.*)\);', r.text)[0])
            # PDF图片地址
            urls = data['data']
            if self.total_pages == -1:
                # 总页数
                self.total_pages = int(data['pages']['actual'])
        if int(len(urls)) != 0:
            for k,i in urls.items():
                yield i
        return False

    # 检查图片地址是否存在
    def check_url(self, urls):
        r = True
        for url in urls:
            if url == '':
                r = False
        return r

    # 下载图片
    def down_load_img(self, urls, path):
        for i in range(0, len(urls)):
            count = self.count
            if not (count in self.remove_pages):
                # 非过滤图
                if not self.check_img(path, str(count) + '.jpg'):
                    # 文件未下载
                    self.save_file(f'https:{urls[i]}', self.headers, f'{path}/{count}.jpg') # 进行下载
            else:
                # 过滤不需要的图
                self.remove_pages.remove(self.count)
                self.count -= 1
            self.count += 1

    # 检查文件是否已下载
    def check_img(self, filePath, fileName):
        files = os.listdir(filePath)
        return fileName in files

    # 保存文件（图片、视频）
    def save_file(self, url, headers, path):
        with closing(requests.get(url, headers = headers, stream = True)) as response:
            content_size = int(response.headers['content-length'])  # 内容体总大小
            chunk_size = content_size  # 单次请求最大值
            data_count = 0 # 数据统计
            with open(f'{path}', "wb") as f:
                for data in response.iter_content(chunk_size = chunk_size):
                    f.write(data)
                    data_count = data_count + len(data)
                    self.progress_bar(data_count, content_size, 30, path)
        print()

    # 进度条
    def progress_bar(self, current, total, len, text):
        # 已进行进度调整
        current += 1
        # 已运行进度值
        pro_num = int((current / total) * len)
        # 已运行百分比
        precent = (current / total) * 100
        print('\r' + '>' * pro_num + '.' * (len - pro_num) + f' {precent:.2f}%（{current}/{total}) - {text}', end = '')

    # 生成PDF
    def generat_PDF(self, path, file_name):
        file_names = os.listdir(f'./{path}') # 获取图片名列表
        img_names = [] # 下载的图片名组
        for name in file_names:
            # 过滤其它文件类型的文件
            if "jpg" in name:
                img_names.append(name)
        img_names.sort(key = self.sort_key) # 根据字符串中数字排序
        (w, h) = Image.open(os.path.join(path, img_names[0])).size # 获取第一张图宽高
        # 生成PDF
        c = canvas.Canvas(file_name, pagesize = portrait((w, h)))
        for name in img_names:
            c.drawImage(os.path.join(path, name), 0, 0, w, h)
            c.showPage()
        c.save()

    # 排序关键字匹配
    def sort_key(self, s):
        if s:
            try:
                r = re.findall('^\d+', s)[0] # 匹配开头数字序号
            except:
                r = -1
            return int(r)

    def run(self):
        """
        > 运行流程：
            1、创建文件（图片文件）
            2、获取图片地址
            3、下载图片
            4、生成PDF
        """

        # 创建文件路径
        self.process_info(1, 3, '正在创建文件路径')
        self.create_folder(self.path)
        print('The image diameter is created.')

        # 获取图片地址、下载图片
        self.process_info(2, 3, '正在获取图片地址、下载图片')
        i = 1
        n = -1
        while True:
            # 获取PDF图片组地址
            urls = list(self.get_image_urls(f'{self.url}{int(time.time())}&page={1 + (i - 1) * 6}', f'./{self.path}/'))
            if not urls:
                break
            if self.total_pages != -1 and i == 1:
                n =  self.total_pages / 6
                n = int(n) + 1 if int(n) != n else n
            if i > n:
                break;
            if self.check_url(urls):
                # 下载图片
                print(f'正在下载第{i}页数据...')
                self.down_load_img(urls, self.path)
                i += 1
            # 接口时间戳有时间间隔处理，短时间内快速请求将无数据
            time.sleep(2)
        print('\nImage download completed.')

        # 生成PDF
        self.process_info(3, 3, '正在生成PDF')
        self.generat_PDF(self.path, self.file_name)
        print('Generated PDF.\n')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        DownLoadImage(sys.argv[1], '').run()
    elif len(sys.argv) == 3:
        DownLoadImage(sys.argv[1], sys.argv[2]).run()
    else:
        print(
        '''
    参数错误，请参考(python3 脚本 [文件名] [剔除页码]（英文逗号分隔）例:
        python3 downLoadPDF pdf_file
        python3 downLoadPDF pdf_file 3,7
        '''
        )
