# SimpleSubConverter|简单的订阅转换

功能：

1. 修改节点的伪装host
2. 根据节点名过滤订阅（待开发）
3. 根据节点地址过滤订阅（待开发）

## 部署

`pip3 install flask`

`python3 app.py`

## 使用

### 简单实例

请求url:  `http://100.100.100.100:20088/sub`

例如：

```
http://100.100.100.100:20088/sub?suburl=http%3A%2F%2Fbaidu.com&newhost=www.gov.hk
```

即可修改订阅中的节点的host

### 详细参数：

| 参数    | 必要性 | 示例                      | 解释                                                         | 是否已实现                                                |
| ------- | ------ | ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| target  | 可选   | V2Ray                 | 指定要生成的配置类型，默认不改变给定的链接返回的订阅格式   | ❌    |
| suburl  | 必要   | http%3A%2F%2Fbaidu.com | 指机场所提供的订阅链接，需要经过 [URLEncode](https://www.urlencoder.org/) 处理 | ✔ |
| newhost | 可选   | www.gov.hk         | 要指定的配置节点中的Host（ws/tls等的host），默认不改变 | ✔ |
| nameinclude | 可选 | 中转 |  | ❌ |
| nameexclude | 可选 | 游戏 |  | ❌ |
| addressinclude | 可选 | 100.0.0.0/8 |  | ❌ |
| addressexclude | 可选 | 100.0.0.0/8 |  | ❌ |

