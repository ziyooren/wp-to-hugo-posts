from xml.dom import minidom
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def convert_image_link(link):
    # 从链接中提取路径
    # 示例路径 https://www.thewindows12.com/wp-content/uploads/2024/05/image-6.png
    # 提取后路径 images/post/2024/05/image-6.png

    # Test
    # link = "https://www.thewindows12.com/wp-content/uploads/2024/05/image-6.png"

    if "/wp-content/uploads/" in link:
        relative_path = link.split('/wp-content/uploads/')[-1]
        return f'images/post/{relative_path}'
    # if link.startswith("https://www.thewindows12.com/wp-content/uploads/"):
    #     relative_path = link.replace("https://www.thewindows12.com/wp-content/uploads/", "")
    #     return f'images/post/{relative_path}'
    else:
        return "Invalid link format."

def get_featured_image_link(post_link):
    # 获取文章的featured image链接
    response = requests.get(post_link)
    soup = BeautifulSoup(response.text, 'html.parser')
    featured_image_link = soup.find('meta', property='og:image').get('content')
    return convert_image_link(featured_image_link)

def time_convert(time):
    # 源时间格式：Mon, 08 Apr 2024 06:10:56 +0000 
    # 转换后格式：2024-04-08T06:10:56+00:00
    
    # 解析源时间字符串为datetime对象
    dt = datetime.strptime(time, '%a, %d %b %Y %H:%M:%S %z')
    
    # 格式化为目标时间字符串
    return dt.strftime('%Y-%m-%dT%H:%M:%S%z')

def get_post_metadata(item):
    # 获取文章的元数据
    # 抓取文章信息
    title = item.getElementsByTagName('title')[0].firstChild.data
    post_link = item.getElementsByTagName('link')[0].firstChild.data
    file_name = post_link.split('/')[-2] + '.md'
    try:
        description = item.getElementsByTagName('excerpt:encoded')[0].firstChild.data
    except:
        description = ''
    image_link = get_featured_image_link(post_link)
    publish_date = time_convert(item.getElementsByTagName('pubDate')[0].firstChild.data)
    
    # 获取分类和标签
    categories = item.getElementsByTagName('category')
    post_tags = []
    # 遍历所有 category 元素并判断其 domain 属性
    for category in categories:
        domain = category.getAttribute('domain')
        if domain == 'category':
            # 处理 domain 为 "category" 的元素
            post_categories = category.firstChild.data
        elif domain == 'post_tag':
            # 处理 domain 为 "post_tag" 的元素
            post_tag = category.firstChild.data
            post_tags.append(post_tag)
    
    # image: "{image_link}"

    post_metadata = f"""---
title: "{title}"
description: "{description}"
image: "{image_link}"
date: "{publish_date}"
categories: ["{post_categories}"]
tags: [{', '.join(f'"{tag}"' for tag in post_tags)}]
type: "regular" # available types: [featured/regular]
draft: false
sitemapExclude: false
---"""

    # 打印文章信息
    # print(f"Title: {title}")
    # print(f"Post Link: {post_link}")
    # print(f"Description: {description}")
    # print(f"Publish Date: {publish_date}")
    # print(f"Categories: {post_categories}")
    # print(f"Tags: {post_tags}")
    # print(post_metadata)

    return post_metadata, file_name

def get_content(item):
    # 获取 <content:encoded> 中的内容
    content_encoded = item.getElementsByTagName('content:encoded')[0].firstChild.data
    
    # 初始化 Markdown 内容
    markdown_content = ""

    # 定义转换规则
    block_mapping = {
        'p': lambda x: convert_inline_styles(x) + "\n\n",  # 段落，支持加粗、斜体、链接
        'h2': lambda x: f"## {convert_inline_styles(x.strip())}\n\n",  # 标题 h2
        'h3': lambda x: f"### {convert_inline_styles(x.strip())}\n\n",  # 标题 h3
        'h4': lambda x: f"#### {convert_inline_styles(x.strip())}\n\n",  # 标题 h4
        'ol': lambda x: convert_list(x, ordered=True) + "\n\n",  # 有序列表
        'ul': lambda x: convert_list(x, ordered=False) + "\n\n",  # 无序列表
        'blockquote': lambda x: re.sub(r'<p>(.*?)</p>', r"> \1", x) + "\n\n",  # 引用
        'figure': lambda x: handle_media_block(x),  # 图片和视频处理
        'table': lambda x: convert_table(x)  # 表格处理
    }

    def handle_media_block(block):
        """处理 figure 中的图片和视频转换为 Hugo Shortcode"""
        # 处理图片
        img_match = re.search(r'<img.*?src="(.*?)".*?alt="(.*?)".*?class="(.*?)".*?/>', block)
        if img_match:
            img_src = convert_image_link(img_match.group(1))  # 转换图片链接
            img_alt = img_match.group(2)
            img_class = img_match.group(3)
            return f'{{{{< image src="{img_src}" alt="{img_alt}" class="{img_class}" >}}}}\n\n'

        # 处理视频
        video_match = re.search(r'<video.*?src="(.*?)".*?></video>', block)
        if video_match:
            video_src = video_match.group(1)
            return f'{{{{< video src="{video_src}" >}}}}\n\n'

        return ""

    def convert_inline_styles(text):
        """处理段落内的加粗、斜体、链接等样式"""
        # 加粗处理 <strong> 和 <b>
        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
        text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)

        # 斜体处理 <em> 和 <i>
        text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
        text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)

        # 链接处理 <a href="URL">text</a>
        text = re.sub(r'<a href="(.*?)".*?>(.*?)</a>', r'[\2](\1)', text)

        return text

    def convert_list(list_html, ordered):
        """将有序和无序列表转换为 Markdown"""
        if ordered:
            return re.sub(r'<li>(.*?)</li>', r"1. \1", list_html)
        else:
            return re.sub(r'<li>(.*?)</li>', r"- \1", list_html)

    def convert_table(table_html):
        """将表格从 HTML 转换为 Markdown 格式"""
        rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
        table_markdown = ""
        header_row = True

        for row in rows:
            cols = re.findall(r'<t[hd]>(.*?)</t[hd]>', row)
            if header_row:
                # 表头处理
                table_markdown += "| " + " | ".join(cols) + " |\n"
                table_markdown += "| " + " | ".join(['---'] * len(cols)) + " |\n"
                header_row = False
            else:
                # 表内容处理
                table_markdown += "| " + " | ".join(cols) + " |\n"
        
        return table_markdown

    # 按顺序处理每个块
    for block_name, handler in block_mapping.items():
        tag_regex = re.compile(rf'<!-- wp:{block_name}.*?-->(.*?)<!-- /wp:{block_name} -->', re.DOTALL)
        content_encoded = tag_regex.sub(lambda m: handler(m.group(1)), content_encoded)

    # 去除多余的 HTML 注释和标签
    markdown_content = re.sub(r'<!--.*?-->', '', content_encoded)
    markdown_content = re.sub(r'<[^>]+>', '', markdown_content)

    return markdown_content


def main():
    xml_file = input("Please input XML file:")
    doc = minidom.parse(xml_file)

    items = doc.getElementsByTagName('item')

    for item in items:
        item_type = item.getElementsByTagName('wp:post_type')[0].firstChild.data
        if item_type == 'post':
            post_metadata, file_name = get_post_metadata(item)
            print(post_metadata, file_name)
            # content = get_content(item)
            
            # 用 file_name 创建 markdown 文件
            # 将 post_metadata 和 content 写入 markdown 文件
            # 文件存储在 blog 文件夹下
            with open(f"blog/{file_name}", "w", encoding="utf-8") as f:
                f.write(post_metadata)
                # f.write(content)
            

if __name__ == "__main__":
    main()
    