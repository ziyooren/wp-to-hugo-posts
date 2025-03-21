from xml.dom import minidom
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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
    description = item.getElementsByTagName('excerpt:encoded')[0].firstChild.data
    # image_link = get_featured_image_link(post_link)
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
    content_encoded = item.getElementsByTagName('content:encoded')

    for content in content_encoded:
        print(content.firstChild.data)


def main():
    xml_file = input("Please input XML file:")
    doc = minidom.parse(xml_file)

    items = doc.getElementsByTagName('item')

    for item in items:
        item_type = item.getElementsByTagName('wp:post_type')[0].firstChild.data
        if item_type == 'post':
            post_metadata, file_name = get_post_metadata(item)
            print(post_metadata, file_name)
            content = get_content(item)


if __name__ == "__main__":
    main()
    