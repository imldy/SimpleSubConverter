from flask import Flask, request
import requests as rqs
import base64
import json

app = Flask(__name__)


@app.route('/')
def index():
    return 'SimpleSubConverter'


def get_sub_text(sub_url: str):
    resp = rqs.get(url=sub_url)
    sub_text = resp.text
    return sub_text


def proxy_url_to_json(proxy_url):
    protocol, url = proxy_url.split("://")
    b64decode_result: bytes = base64.b64decode(url)
    conf_json: dict = json.loads(b64decode_result.decode())
    return protocol, conf_json


def json_to_proxy_url(protocol, conf_json):
    b64encode_result: bytes = base64.b64encode(bytes(json.dumps(conf_json), encoding="utf-8"))
    return protocol + "://" + b64encode_result.decode()


def key_include_in_name(name_key_list, name):
    '''
    判断节点名内是否包含关键字
    :param name_key_list: 要判断的关键字列表
    :param name: 节点名
    :return: 节点名是否包含关键字
    '''
    for exclude_name_key in name_key_list:
        if exclude_name_key in name:
            return True
    else:
        return False


@app.route('/sub', methods=['GET', 'POST'])
def sub():
    if request.method == 'GET':  # 请求方式是get
        sub_url = request.args.get('suburl')  # args取get方式参数
        new_host = request.args.get('newhost')
        name_exclude = request.args.get('nameexclude')
        if sub_url is None or sub_url == "":
            return "订阅链接必不可少，请查阅项目文档https://github.com/imldy/SimpleSubConverter"
        try:
            sub_text = get_sub_text(sub_url=sub_url)
        except Exception:
            return "订阅链接获取失败"
        # 判断否是要进行节点名过滤
        name_exclude_flag = False
        exclude_name_key_list = []
        if name_exclude is not None and name_exclude != "":
            name_exclude_flag = True
            exclude_name_key_list = name_exclude.split(",")
        # 节点列表
        node_list = base64.b64decode(sub_text).decode().split("\n")
        # 处理后的节点列表
        new_node_list = []
        # 挨个处理节点
        for node in node_list:
            if "vmess" == node[:5]:  # 目前只处理vmess与vless
                # 获取协议头和base64解码后的节点信息
                protocol, conf_json = proxy_url_to_json(node)
                # 处理根据节点名过滤
                if name_exclude_flag:
                    # 判断关键字是否包含在节点名内
                    if key_include_in_name(exclude_name_key_list, conf_json["ps"]):
                        # 如果节点名包含需要排除的关键字，则跳过此节点
                        continue
                # 判断是否需要修改host
                if new_host is not None and new_host != "":
                    conf_json["host"] = new_host
                # 修改完成，转为V2Ray系列客户端使用的节点链接格式
                proxy_url = json_to_proxy_url(protocol, conf_json)
                new_node_list.append(proxy_url)
            elif "ssr" == node[:3]:  # 不处理ssr
                new_node_list.append(node)
            elif "ss" == node[:2]:  # 不处理ss
                new_node_list.append(node)
            else:  # 不处理其他协议的链接
                new_node_list.append(node)
        # 转为V2Ray系列客户端使用的订阅格式
        new_resp_text = base64.b64encode("\n".join(new_node_list).encode())
        return new_resp_text
    elif request.method == 'POST':
        return "The POST method is not supported"
    return 'SimpleSubConverter'


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=20088)
