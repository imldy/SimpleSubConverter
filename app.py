from flask import Flask, request
import requests as rqs
import base64
import json
import yaml
import conf

app = Flask(__name__)


@app.route('/')
def index():
    return 'SimpleSubConverter'


def get_sub_text(sub_url: str, UA):
    """
    获取订阅信息的统一方法
    :param sub_url: 订阅地址
    :param UA: 原UA
    :return: 订阅的文本
    """
    ResponseHeaders = {}
    headers = {'User-Agent': UA}
    proxies = {"http": None, "https": None}
    resp: rqs.Response = rqs.get(url=sub_url, headers=headers, proxies=proxies)
    for head_key in resp.headers:
        if head_key.title() in conf.ResponseHeadersKeyList:
            ResponseHeaders[head_key] = resp.headers[head_key]
    sub_text = resp.text
    return sub_text, ResponseHeaders


def proxy_url_to_json(proxy_url):
    """
    （通常用于v2rayN系应用的）代理节点url转为json格式
    :param proxy_url: （通常用于v2rayN系应用的）代理节点
    :return: 代理协议和Json文本的字典对象
    """
    protocol, url = proxy_url.split("://")
    b64decode_result: bytes = base64.b64decode(url)
    conf_json: dict = json.loads(b64decode_result.decode())
    return protocol, conf_json


def json_to_proxy_url(protocol, conf_json):
    """
    json格式转为（通常用于v2rayN系应用的）代理节点url
    :param protocol: 代理协议
    :param conf_json: Json文本的字典对象
    :return:
    """
    b64encode_result: bytes = base64.b64encode(bytes(json.dumps(conf_json), encoding="utf-8"))
    return protocol + "://" + b64encode_result.decode()


def key_include_in_name(name_key_list, name):
    """
    判断节点名内是否包含关键字
    :param name_key_list: 要判断的关键字列表
    :param name: 节点名
    :return: 节点名是否包含关键字
    """
    for exclude_name_key in name_key_list:
        if exclude_name_key in name:
            return True
    else:
        return False


def decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b'=' * (4 - missing_padding)
    return base64.decodebytes(data)


def modify_format_to_V2Ray(args, sub_text):
    """
    转换订阅格式为V2RayN系应用格式
    :param args: 全局转换参数
    :param sub_text: 订阅的文本信息
    :return:
    """
    # 节点列表
    node_list = decode_base64(sub_text.strip().encode()).decode().split("\n")
    # 处理后的节点列表
    new_node_list = []
    # 挨个处理节点
    for node in node_list:
        if "vmess" == node[:5]:  # 目前只处理vmess与vless
            # 获取协议头和base64解码后的节点信息
            protocol, conf_json = proxy_url_to_json(node)
            # 处理根据节点名过滤
            if args["name_exclude_flag"]:
                # 判断关键字是否包含在节点名内
                if key_include_in_name(args["exclude_name_key_list"], conf_json["ps"]):
                    # 如果节点名包含需要排除的关键字，则跳过此节点
                    continue
            if args["name_include_flag"]:
                if not key_include_in_name(args["include_name_key_list"], conf_json["ps"]):
                    continue
            # 判断是否需要修改host
            if args["new_host"] is not None and args["new_host"] != "":
                conf_json["host"] = args["new_host"]
                if "sni" in list(conf_json.keys()):  # 如果使用了tls，则要处理增加的sni字段
                    conf_json["sni"] = args["new_host"]
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
    V2Ray_sub_text = base64.b64encode("\n".join(new_node_list).encode())
    return V2Ray_sub_text


def modify_format_to_Clash(args, sub_text):
    """
    转换订阅格式为Clash系应用格式
    :param args: 全局转换参数
    :param sub_text: 订阅的文本信息
    :return:
    """
    sub_yaml_text = yaml.load(sub_text, Loader=yaml.FullLoader)
    proxies = sub_yaml_text["proxies"]
    new_proxies = []
    # 要保留的代理列表
    proxy_name_list = ["DIRECT", "REJECT"]
    for proxy in proxies:
        if "vmess" == proxy["type"]:
            # 过滤节点名
            if args["name_exclude_flag"]:
                # 判断关键字是否包含在节点名内
                if key_include_in_name(args["exclude_name_key_list"], proxy["name"]):
                    # 跳过此节点
                    continue
            if args["name_include_flag"]:
                if not key_include_in_name(args["include_name_key_list"], proxy["name"]):
                    continue
            # 判断是否需要修改host
            if args["change_host_flag"]:
                # 判断传输协议(network)，如果没有network，那就不处理
                if "network" in list(proxy.keys()):
                    if proxy["network"] == "ws":
                        proxy["ws-headers"] = {}
                        proxy["ws-headers"]["Host"] = args["new_host"]
                        if "tls" in list(proxy.keys()) and proxy["tls"] == True:  # 判断是否开了tls（如果使用了tls，则要处理增加的sni字段）
                            proxy["servername"] = args["new_host"]
                    else:  # 暂时只持ws
                        pass
                else:  # 暂时只持network键存在的情况
                    pass
            proxy_name_list.append(proxy["name"])
            new_proxies.append(proxy)
        elif "ss" == proxy["type"]:
            new_proxies.append(proxy)
        elif "ssr" == proxy["type"]:
            new_proxies.append(proxy)
        else:
            new_proxies.append(proxy)
    sub_yaml_text["proxies"] = new_proxies
    # 过滤proxy-groups中的节点
    proxy_groups = sub_yaml_text["proxy-groups"]

    for proxy_group in proxy_groups:
        # 群组名，需要保留
        proxy_name_list.append(proxy_group["name"])

    new_proxy_groups = []
    for proxy_group in proxy_groups:
        proxies = proxy_group["proxies"]
        new_proxies = []
        for proxy_name in proxies:
            # 保留节点名
            if proxy_name in proxy_name_list:
                new_proxies.append(proxy_name)
        # 替换为修改后的proxies
        proxy_group["proxies"] = new_proxies

        new_proxy_groups.append(proxy_group)

    # 替换为修改后的proxy-groups
    sub_yaml_text["proxy-groups"] = new_proxy_groups

    Clash_sub_text = yaml.dump(sub_yaml_text, allow_unicode=True).encode('utf-8')
    return Clash_sub_text


Clash_sub = "Clash"
V2Ray_sub = "V2Ray"


def get_sub_format(sub_text):
    """
    根据订阅文本信息，确定订阅格式
    :param sub_text:
    :return:
    """
    if "allow-lan" in sub_text:
        sub_format = Clash_sub
    else:
        sub_format = V2Ray_sub
    return sub_format


@app.route('/sub', methods=['GET', 'POST'])
def sub():
    if request.method == 'GET':  # 请求方式是get
        UA = request.headers.get('User-Agent')
        sub_url = request.args.get('suburl')  # args取get方式参数
        new_host = request.args.get('newhost')
        name_exclude = request.args.get('nameexclude')
        name_include = request.args.get('nameinclude')
        target_sub_format = request.args.get('target')
        if sub_url is None or sub_url == "":
            return "订阅链接必不可少，请查阅项目文档https://github.com/imldy/SimpleSubConverter"
        try:
            sub_text, ResponseHeaders = get_sub_text(sub_url=sub_url, UA=UA)
        except rqs.exceptions.ProxyError as e:
            return "订阅链接获取失败：{}\n{}".format("服务器请求代理错误", e)
        except rqs.exceptions.ConnectionError as e:
            return "订阅链接获取失败：{}\n{}".format("服务器请求连接错误", e)
        except Exception as e:
            return "订阅链接获取失败：{}\n{}".format("未知异常", e)
        if target_sub_format is None or sub_url == "":  # 默认目标格式为V2Ray系客户端订阅
            target_sub_format = V2Ray_sub
        # 判断订阅格式
        sub_format = get_sub_format(sub_text)
        # 判断否是要进行节点名过滤
        name_exclude_flag = False
        exclude_name_key_list = []
        if name_exclude is not None and name_exclude != "":
            name_exclude_flag = True
            exclude_name_key_list = name_exclude.split(",")
        name_include_flag = False
        include_name_key_list = []
        if name_include is not None and name_include != "":
            name_include_flag = True
            include_name_key_list = name_include.split(",")
        # 判断是否要修改host
        change_host_flag = False
        if new_host is not None and new_host != "":
            change_host_flag = True

        # 整理数据
        args = {
            "sub_url": sub_url,
            "sub_format": sub_format,
            "change_host_flag": change_host_flag,
            "new_host": new_host,
            "name_exclude_flag": name_exclude_flag,
            "name_exclude": name_exclude,
            "name_include_flag": name_include_flag,
            "name_include": name_include,
            "include_name_key_list": include_name_key_list,
            "target_sub_format": target_sub_format,
            "exclude_name_key_list": exclude_name_key_list
        }
        if sub_format == Clash_sub:
            target_sub_text = modify_format_to_Clash(args, sub_text)
        else:  # 默认修改为V2Ray系客户端格式，其他后续支持
            target_sub_text = modify_format_to_V2Ray(args, sub_text)
        return target_sub_text, 200, ResponseHeaders
    elif request.method == 'POST':
        return "The POST method is not supported"
    return 'SimpleSubConverter'


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=20088)
