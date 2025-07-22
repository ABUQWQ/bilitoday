import requests
import json
import time
import hashlib
import os

# WBI 签名计算函数
def get_wbi_signature(img_key, sub_key):
    mixin_key_enc_tab = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]
    mixin_key = ''.join([img_key[i] + sub_key[i] for i in mixin_key_enc_tab])[:32]
    return mixin_key

# 获取 WBI 所需键
def get_keys():
    resp = requests.get('https://api.bilibili.com/x/web-interface/nav')
    data = resp.json()
    img_url = data['data']['wbi_img']['img_url']
    sub_url = data['data']['wbi_img']['sub_url']
    img_key = img_url.split('/')[-1].split('.')[0]
    sub_key = sub_url.split('/')[-1].split('.')[0]
    return img_key, sub_key

# 生成签名
def generate_signed_params(params):
    img_key, sub_key = get_keys()
    mixin_key = get_wbi_signature(img_key, sub_key)
    params['wts'] = str(int(time.time()))
    query = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
    wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = wbi_sign
    return params

# 获取排行榜数据
def fetch_ranking():
    url = 'https://api.bilibili.com/x/web-interface/ranking/v2'
    params = {'rid': 0, 'type': 'all'}
    signed_params = generate_signed_params(params)
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, params=signed_params, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['list']
    else:
        print(f'Error: {response.status_code}')
        return None

# 生成 Markdown 内容
def generate_md(ranking_list):
    md_content = '# Bilibili 视频排行榜\n\n此文件由 GitHub Action 自动更新。\n\n## 最新排行榜\n\n| 排名 | 标题 | 作者 | 播放量 |\n| --- | --- | --- | --- |\n'
    for idx, item in enumerate(ranking_list[:10], 1):  # 只取前10个作为示例
        title = item['title']
        author = item['owner']['name']
        play = item['stat']['view']
        md_content += f'| {idx} | {title} | {author} | {play} |\n'
    return md_content

# 主函数
if __name__ == '__main__':
    ranking = fetch_ranking()
    if ranking:
        md = generate_md(ranking)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(md)
        print('README.md updated successfully.')
    else:
        print('Failed to fetch ranking.')