"""Domains that should resolve via domestic DNS for best China-side latency.

These are NRPT-compatible *namespaces*. ``.qq.com`` matches anything ending in
``.qq.com`` (e.g. ``im.qq.com``, ``connect.qq.com``).

Targeted at the user's pain points:
- QQ / WeChat 快捷登录 (Tencent ecosystem domains must resolve to CN IPs)
- Taobao / Alipay / 阿里云
- B站 / 知乎 / 微博 / 抖音
- 国内银行 / 运营商 / 政务
"""
from __future__ import annotations

TENCENT = [
    "qq.com", "tencent.com", "qq.com.cn",
    "weixin.qq.com", "wx.qq.com",
    "tenpay.com", "qpic.cn", "qlogo.cn",
    "gtimg.com", "gtimg.cn", "myqcloud.com",
    "qcloud.com", "qcloudimg.com",
]

ALIBABA = [
    "alibaba.com", "alibaba-inc.com",
    "taobao.com", "tmall.com", "1688.com",
    "alipay.com", "alipayobjects.com",
    "alicdn.com", "aliyun.com", "aliyuncs.com",
    "aliexpress.com", "alimama.com",
    "cainiao.com",
]

BAIDU = [
    "baidu.com", "bdstatic.com", "bdimg.com",
    "baidustatic.com", "baidupcs.com",
    "bcebos.com",
]

BYTEDANCE = [
    "bytedance.com", "douyin.com",
    "toutiao.com", "ixigua.com",
    "bytecdn.com", "byteimg.com",
    "feishu.cn", "lark.io",
]

NETEASE = [
    "163.com", "126.com", "netease.com",
    "ydstatic.com", "youdao.com",
    "lofter.com", "yeah.net",
]

OTHERS_CN = [
    "bilibili.com", "hdslb.com", "biliapi.net",
    "zhihu.com", "zhimg.com",
    "weibo.com", "weibo.cn", "sina.com.cn", "sinaimg.cn",
    "sogou.com", "sohu.com",
    "jd.com", "360buyimg.com",
    "meituan.com", "meituan.net", "dianping.com",
    "didiglobal.com", "didichuxing.com",
    "mi.com", "xiaomi.com", "xiaomicp.com",
    "huawei.com", "hicloud.com",
    "iqiyi.com", "iqiyipic.com",
    "youku.com", "ykimg.com",
    "douban.com", "doubanio.com",
    "ctrip.com", "trip.com",
    "12306.cn",
    "ccb.com", "icbc.com.cn", "boc.cn", "abchina.com", "cmbchina.com",
    "10086.cn", "189.cn", "10010.com",
    "xunlei.com",
    "qiniu.com", "qiniucdn.com",
    "upyun.com",
    "gov.cn", "edu.cn", "org.cn",
]

CN_NAMESPACES: list[str] = sorted(set(
    TENCENT + ALIBABA + BAIDU + BYTEDANCE + NETEASE + OTHERS_CN
))
