# SimpleSubConverter|简单的订阅转换

功能：

1. 修改节点的伪装host
2. 根据节点名过滤订阅（已实现排除包含关键字的节点功能）
3. 根据节点地址过滤订阅（待开发）

## 部署

本部署过程会将`/usr/local/src/`设为工作目录的上级目录，如有其他需求，可自行修改。`

```
cd /usr/local/src/ # 进入想要放置工作目录的上级目录
git clone https://github.com/imldy/SimpleSubConverter.git # 克隆仓库
cd SimpleSubConverter # 进入仓库目录（工作目录）
python3 -m venv myvenv # 创建一个虚拟环境。会在仓库目录创建一个myvenv目录
source myvenv/bin/activate # 激活虚拟环境（读取环境变量）或者“. myvenv/bin/activate”
pip3 install --upgrade pip # 升级pip
pip3 install flask gunicorn requests pyyaml # 安装所需库
gunicorn app:app -b 127.0.0.1:20088 -w 2 # 前台启动 第一个app代表app.py，-b 监听ip与端口 -w 设置进程数
```

后续不进入虚拟环境进行启动服务

```
/usr/local/src/SimpleSubConverter/myvenv/bin/gunicorn app:app -b 127.0.0.1:20088 -w 2
```

使用Systemd守护进程

`vim /etc/systemd/system/ssc.service`

放入以下内容

```
[Unit]
Description=SimpleSubConverter
Documentation=https://github.com/imldy/SimpleSubConverter
After=network.target nss-lookup.target network-online.target
[Service]
User=root
WorkingDirectory=/usr/local/src/SimpleSubConverter/
ExecStart=/usr/local/src/SimpleSubConverter/myvenv/bin/gunicorn app:app -b 127.0.0.1:20088 -w 2
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000
[Install]
WantedBy=multi-user.target
```

启动ssc： `systemctl start ssc`

设置ssc开机自启：`systemctl enable ssc`

使用nginx代理流量

```
server {
        listen       80;
        server_name  你的域名;
        return       301 https://你的域名$request_uri;
}

server {

        listen  443 ssl;
        server_name  你的域名;
        ssl_certificate       你的域名fullchain证书路径;
        ssl_certificate_key   你的域名公钥路径;

        access_log  /var/log/nginx/ssc_access.log;

        location / { # ssc 前端
            root          /var/www/ssc-web;
        }
        location /sub { # ssc 后端
            proxy_pass http://127.0.0.1:20088/sub;
            proxy_redirect     off;
    
            proxy_set_header   Host                 $host;
            proxy_set_header   X-Real-IP            $remote_addr;
            proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto    $scheme;
        }
}
```

## 使用

### 简单实例

请求url:  `http://100.100.100.100:20088/sub`

例如：

```
http://100.100.100.100:20088/sub?suburl=http%3A%2F%2Fbaidu.com&newhost=www.gov.hk
```

即可修改订阅中的节点的host

### 详细参数：

**参数全部需要进行[UrlEncode](https://tool.chinaz.com/tools/urlencode.aspx)，但此处为了方便查看示例，所以使用明文。**

| 参数    | 必要性 | 示例                      | 解释                                                         | 是否已实现                                                |
| ------- | ------ | ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| target  | 可选   | V2Ray                 | 指定要生成的配置类型，默认不改变给定的链接返回的订阅格式   | ❌    |
| suburl  | 必要   | https://baidu.com/ | 原订阅链接 | ✔ |
| newhost | 可选   | www.gov.hk         | 要指定的配置节点中的Host（ws/tls等的host），默认不改变 | ✔ |
| nameinclude | 可选 | 中转 |  | ❌ |
| nameexclude | 可选 | 游戏,测试 |  | ✔ |
| addressinclude | 可选 | 100.0.0.0/8 |  | ❌ |
| addressexclude | 可选 | 100.0.0.0/8 |  | ❌ |

