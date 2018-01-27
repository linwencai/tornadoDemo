# coding:utf8
"""工具模块，兼容python2/3
"""
from __future__ import unicode_literals
from __future__ import print_function
import hashlib
import base64
import time
import json
import sys
import os
# try:
#     import __builtin__ as builtins  # py2.6
# except ImportError:
#     import builtins

try:
    from urllib import urlencode  # py2
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import urlencode, parse_qs   # py3

try:
    # pip install pycrypto
    from Crypto.Cipher import DES, AES
    from Crypto.PublicKey import RSA
    from Crypto.Hash import SHA
    from Crypto import Random
    from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
    from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
    # from Crypto.Cipher import PKCS1_OAEP as Cipher_pkcs1_oaep
    # from Crypto.Signature import PKCS1_PSS as Signature_pkcs1_pss
except ImportError:
    # pip install pycryptodome
    from Cryptodome.Cipher import DES, AES
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Hash import SHA
    from Cryptodome import Random
    from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
    from Cryptodome.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
    # from Cryptodome.Cipher import PKCS1_OAEP as Cipher_pkcs1_oaep
    # from Cryptodome.Signature import PKCS1_PSS as Signature_pkcs1_pss


ENCODING = "utf8"  # 字符串编码

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # 时间格式化
TIME_FORMAT = "%H:%M:%S"  # 时间格式化
DATE_FORMAT = "%Y-%m-%d"  # 日期格式化

PY_VER_MAJOR = sys.version_info.major  # python大版本号
PY_VER_MINOR = sys.version_info.minor  # python小版本号

builtins = sys.modules.get("builtins") or sys.modules.get("__builtin__")  # 内建模块，兼容py2.6-3.6
# unicode = getattr(builtins, "unicode", str)  # py3添加unicode关键字
unicode = type(u"")  # py3添加unicode关键字


def encode(msg, encoding=ENCODING):
    """str->bytes
    :param msg: bytes or str
    :param encoding: 编码
    :return bytes
    """
    # return msg.encode(encoding) if hasattr(msg, "encode") else msg
    # return msg if isinstance(msg, (bytes, bytearray)) else msg.encode(encoding)
    return msg.encode(encoding) if isinstance(msg, unicode) else msg


def decode(msg, encoding=ENCODING):
    """bytes->str
    :param msg: bytes or str
    :param encoding: 编码
    :return str
    """
    # return msg.decode(encoding) if hasattr(msg, "decode") else msg
    return msg.decode(encoding) if isinstance(msg, (bytes, bytearray)) else msg


def md5(msg):
    """
    :param msg: bytes or str
    :return: md5的16进制小写 str
    """
    msg = encode(msg)
    return hashlib.md5(msg).hexdigest()


def sha1(msg):
    """
    :param msg: bytes or str
    :return: sha1的16进制小写 str
    """
    msg = encode(msg)
    return hashlib.sha1(msg).hexdigest()


def sha256(msg):
    """
    :param msg: bytes or str
    :return: sha256的16进制小写 str
    """
    msg = encode(msg)
    return hashlib.sha256(msg).hexdigest()


class Des:
    """des算法，模式CBC，填充PAD_PKCS5"""
    def __init__(self, key, iv=b"", mode=DES.MODE_CBC):
        self.key = key
        self.iv = iv
        self.mode = mode
        return

    @staticmethod
    def pad(msg):
        """ PAD_PKCS5填充
        :param msg: bytes
        :return: bytes
        """
        num = (DES.block_size - len(msg) % DES.block_size)
        return msg + chr(num).encode() * num  # PAD_PKCS5填充
        # return msg + b"\0" * num  # PAD_NORMAL填充

    @staticmethod
    def unpad(msg):
        """ PAD_PKCS5解析
        :param msg: str or bytes
        :return: str or bytes
        """
        return msg[0:-ord(msg[-1:])]  # PAD_PKCS5填充
        # return msg.rstrip(b"\0")  # PAD_NORMAL填充

    def encrypt(self, msg):
        """加密
        :param msg: bytes or str
        :return: des加密的2进制数据
        """
        msg = encode(msg)
        cipher = DES.new(self.key, self.mode, IV=self.iv)
        return cipher.encrypt(self.pad(msg))

    def decrypt(self, msg):
        """解密
        :param msg: bytes
        :return: bytes
        """
        cipher = DES.new(self.key, self.mode, IV=self.iv)
        return self.unpad(cipher.decrypt(msg))

    def b16encrypt(self, msg):
        """base16加密
        :param msg: bytes or str
        :return: bytes
        """
        msg = self.encrypt(msg)
        return base64.b16encode(msg)

    def b16decrypt(self, msg):
        """base16解密
        :param msg: bytes or str
        :return: bytes
        """
        msg = base64.b16decode(msg)
        return self.decrypt(msg)

    def b64encrypt(self, msg):
        """base64加密
        :param msg: bytes or str
        :return: bytes
        """
        msg = self.encrypt(msg)
        return base64.b64encode(msg)

    def b64decrypt(self, msg):
        """base64解密
        :param msg: bytes or str
        :return: bytes
        """
        msg = base64.b64decode(msg)
        return self.decrypt(msg)


class Rsa:
    """rsa算法，填充PKCS1_V1_5
    目前推荐使用PKCS1_OAEP加密，PKCS1_V1_5可用于兼容老代码，但已不推荐使用；
    根据RFC 3447描述，若使用PKCS1_OAEP加密，单段数据最大长度为mlen <= k - 2hlen - 2。
    例如，若使用RSA 2048，则k = 2048 / 8 = 256，hLen为使用的hash算法所输出的字节数，若未指定，则默认为SHA1，占用20个字节。
    因此，最终所能够加密的明文的最大长度mLen <= 256 - 2*20 - 2 = 214.
    若采用RSA 1024，则该长度为 128 - 42 = 86.
    """
    def __init__(self, pubKey, priKey, Cipher=Cipher_pkcs1_v1_5, Signature=Signature_pkcs1_v1_5):
        self.pubKey = RSA.importKey(pubKey) if pubKey else None
        self.priKey = RSA.importKey(priKey) if priKey else None
        # self.Cipher = Cipher
        # self.Signature = Signature
        self.pubCipher = Cipher.new(self.pubKey) if self.pubKey else None
        self.pubSignature = Signature.new(self.pubKey) if self.pubKey else None
        self.priCipher = Cipher.new(self.priKey) if self.priKey else None
        self.priSignature = Signature.new(self.priKey) if self.priKey else None

    def encrypt(self, msg):
        """ 加密
        :param msg: bytes or str
        :return: bytes
        """
        msg = encode(msg)
        # cipher = Cipher_pkcs1_v1_5.new(self.pubKey)
        # return cipher.encrypt(msg)
        return self.pubCipher.encrypt(msg)

    def decrypt(self, msg):
        """ 解密
        :param msg: bytes
        :return: bytes
        """
        # cipher = Cipher_pkcs1_v1_5.new(self.priKey)
        # return cipher.decrypt(msg, os.urandom)
        return self.priCipher.decrypt(msg, os.urandom)

    def sign(self, msg):
        """ 签名
        :param msg: bytes or str
        :return: bytes
        """
        msg = encode(msg)
        # signer = Signature_pkcs1_v1_5.new(self.priKey)
        # digest = SHA.new()
        # digest.update(msg)
        # return signer.sign(digest)
        return self.priSignature.sign(SHA.new(msg))

    def verify(self, msg, sign):
        """ 验证签名
        :param msg: bytes or str
        :param sign: bytes or str
        :return: bool
        """
        msg = encode(msg)
        # verifier = Signature_pkcs1_v1_5.new(self.pubKey)
        # digest = SHA.new()
        # digest.update(msg)
        # return verifier.verify(digest, sign)
        return self.pubSignature.verify(SHA.new(msg), sign)

    def b64encrypt(self, msg):
        """ 加密
        :param msg: bytes or str
        :return: bytes
        """
        msg = self.encrypt(msg)
        return base64.b64encode(msg)

    def b64decrypt(self, msg):
        """ 解密
        :param msg: bytes
        :return: bytes
        """
        msg = base64.b64decode(msg)
        return self.decrypt(msg)

    def b64sign(self, msg):
        """ 签名
        :param msg: bytes or str
        :return: bytes
        """
        msg = self.sign(msg)
        return base64.b64encode(msg)

    def b64verify(self, msg, b64sign):
        """ 验证base64签名
        :param msg: bytes or str
        :param b64sign: bytes or str
        :return: bool
        """
        sign = base64.b64decode(b64sign)
        return self.verify(msg, sign)


def jsonDump(obj, ensure_ascii=True, default=decode):
    """obj->json unicode
    :param obj: dict or list
    :param ensure_ascii: 保留编码
    :param default: 特殊对象处理方式
    :return json字符串(unicode)
    """
    if PY_VER_MAJOR == 3:
        return json.dumps(obj, ensure_ascii=ensure_ascii, default=default)
    else:
        # py27下ensure_ascii=False，不能同时有str和bytes
        # return json.dumps(obj, ensure_ascii=ensure_ascii, default=default)

        # decode("unicode_escape")，所有的"\\"会转成"\"，导致报错
        # return json.dumps(obj, default=default).decode(ENCODING if ensure_ascii else "unicode_escape")
        return json.dumps(obj, default=default).decode(ENCODING if ensure_ascii else "raw_unicode_escape")


def jsonLoad(string):
    """json->obj unicode
    :param string: json字符串 bytes or str
    :return dict or list
    """
    if PY_VER_MAJOR == 3:  # py3.4只支持str
        string = decode(string)
    return json.loads(string)


def ts(isSecond=True):
    """ timestamp 当前时间戳
    :param isSecond: true为秒，否则为毫秒
    :return: 时间戳 int
    """
    return int(time.time() if isSecond else time.time()*1000)


def ts2str(timestamp=None, timeFormat=DATE_TIME_FORMAT, isSecond=True):
    """ timestamp->str 时间戳格式化为字符串
    :param timestamp: 时间戳
    :param timeFormat: 时间格式
    :param isSecond: true为秒时间戳，否则为毫秒
    :return: 时间字符串 str
    """
    if timestamp is None:
        timestamp = ts(isSecond=isSecond)
    if isSecond is False:
        timestamp //= 1000
    timeTuple = time.localtime(timestamp)
    if isinstance(timeFormat, bytes):
        timeFormat = timeFormat.decode("utf8")
    return time.strftime(timeFormat, timeTuple)


def ts2dateStr(timestamp=None, isSecond=True):
    """ timestamp->date str 时间戳格式化为日期字符串
    :param timestamp: 时间戳
    :param isSecond: true为秒时间戳，否则为毫秒
    :return: 日期字符串 str
    """
    return ts2str(timestamp, DATE_FORMAT, isSecond)


def ts2timeStr(timestamp=None, isSecond=True):
    """ timestamp->date str 时间戳格式化为小时分字符串
    :param timestamp: 时间戳
    :param isSecond: true为秒时间戳，否则为毫秒
    :return: 小时分字符串 str
    """
    return ts2str(timestamp, TIME_FORMAT, isSecond)


def str2ts(string, timeFormat=DATE_TIME_FORMAT, isSecond=True):
    """ str->timestamp 字符串转为时间戳
    :param string: 字符串
    :param timeFormat: 时间格式
    :param isSecond: true为秒时间戳，否则为毫秒
    :return: 时间戳 int
    """
    if isinstance(timeFormat, bytes):
        timeFormat = timeFormat.decode("utf8")
    timeTuple = time.strptime(string, timeFormat)
    timestamp = time.mktime(timeTuple)
    if isSecond is False:
        timestamp *= 1000
    return int(timestamp)


def urlEncode(query):
    """ dict->url encode 转为url编码
    :param query: dict list tuple
    :return: str
    """
    # 解决py2下unicode报错
    # if PY_VER_MAJOR == 2 and sys.getdefaultencoding().lower().replace("-", "") != "utf8":
    if PY_VER_MAJOR == 2:
        if isinstance(query, dict):
            query = query.items()
        query = [(encode(k), encode(v)) for k, v in query]
    return urlencode(query)


def urlDecode(query):
    """ url encode->dict 解析url编码
    :param query: str
    :return: dict
    """
    return parse_qs(query)


if __name__ == "__main__":
    # print(type(encode(b'\xe4\xb8\xad\xe6\x96\x87')), type(encode(u"中文")))
    # print(type(decode(b'\xe4\xb8\xad\xe6\x96\x87')), type(decode(u"中文")))

    # s = "123"
    # print(type(s))
    # print(md5(s))
    # print(sha1(s))
    # print(sha256(s))

    # ### des ###
    # des = Des(key=b"!~btusd.", iv=b"!~btusd.")
    # r = des.b16encrypt("1234567890")  # 55182D82282638D9DD36C98A081EE9D4
    # print(r, r == b'55182D82282638D9DD36C98A081EE9D4')
    # print(des.b16decrypt('55182D82282638D9DD36C98A081EE9D4'))

    # ### rsa ###
    # # 私钥文件 解密、生成签名
    # privateKey = '''-----BEGIN RSA PRIVATE KEY-----
    # MIICXQIBAAKBgQDKoeRzRVf8WoRSDYYqUzThpYCr90jfdFwTSXHJ526K8C6TEwdT
    # UA+CFPQPRUg9jrYgFcown+J2myzO8BRLynD+XHb9ilLb49Mqk2CvDt/yK32lgHv3
    # QVx14Dpb6h8isjncSF965fxBxlHGbvPwnHkJ9etRIYdYV3QpYohFszH3wQIDAQAB
    # AoGAFhKqkw/ztK6biWClw8iKkyX3LURjsMu5F/TBK3BFb2cYe7bv7lhjSBVGPL+c
    # TfBU0IvvGXrhLXBb4jLu0w67Xhggwwfc86vlZ8eLcrmYVat7N6amiBmYsw20GViU
    # UFmePbo1G2BXqMA43JxqbIQwOLZ03zdw6GHj6EVlx369IAECQQD4K2R3K8ah50Yz
    # LhF7zbYPIPGbHw+crP13THiYIYkHKJWsQDr8SXoNQ96TQsInTXUAmF2gzs/AwdQg
    # gjIJ/dmBAkEA0QarqdWXZYbse1XIrQgBYTdVH9fNyLs1e1sBmNxlo4QMm/Le5a5L
    # XenorEjnpjw5YpEJFDS4ijUI3dSzylC+QQJARqcD6TGbUUioobWB4L9GD7SPVFxZ
    # c3+EgcxRoO4bNuCFDA8VO/InP1ONMFuXLt1MbCj0ru1yFCyamc63NEUDAQJBALt7
    # PjGgsKCRuj6NnOcGDSbDWIitKZhnwfqYkAApfsiBQkYGO0LLaDIeAWG2KoCB9/6e
    # lAQZnYPpOcCubWyDq4ECQQCrRDf0gVjPtipnPPS/sGN8m1Ds4znDDChhRlw74MI5
    # FydvHFumChPe1Dj2I/BWeG1gA4ymXV1tE9phskV3XZfq
    # -----END RSA PRIVATE KEY-----'''
    #
    # # 公钥文件 加密数据、校验签名
    # publicKey = '''-----BEGIN PUBLIC KEY-----
    # MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKoeRzRVf8WoRSDYYqUzThpYCr
    # 90jfdFwTSXHJ526K8C6TEwdTUA+CFPQPRUg9jrYgFcown+J2myzO8BRLynD+XHb9
    # ilLb49Mqk2CvDt/yK32lgHv3QVx14Dpb6h8isjncSF965fxBxlHGbvPwnHkJ9etR
    # IYdYV3QpYohFszH3wQIDAQAB
    # -----END PUBLIC KEY-----'''
    #
    # rsa = Rsa(publicKey, privateKey)
    # raw_data = '测试数据'
    # sign_data_base64 = 'aNPEwi4yDWejNfDfvptwJGHFqJouXMy40xJfN9G7AfOgJV96SDeUXyQJzuaAhZzRCLpRHVQpVT1BNYpItA2ER/' \
    #                    'N0Mj0resAjRncR6IZSYA7dNY+efy9UScZNzLJzLR7xixNmkfTnSOOZEtwwzVlTfLGRxONAl/jbpuSiuXo+pSw='
    # data = rsa.b64encrypt(raw_data)
    # print("RSA加密:", data)
    # print("RSA解密:", rsa.b64decrypt(data).decode("utf8"))
    # sign_data = rsa.b64sign(raw_data)
    # print("RSA签名:", sign_data == encode(sign_data_base64), sign_data)
    # print("RSA验证:", rsa.b64verify(raw_data, sign_data_base64))
    #
    # # rsa google
    # googlePublicKey = '''-----BEGIN PUBLIC KEY-----
    # MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAigKEjNHLimI/33bqrFvrrUTNoebakQQiVyhsFAQhbGujuEL7VNYpDdemasYJLrbwn
    # Ff6rxuIr7gA/+Fz3bAuYGXg7L5ixadz6CUXOw21bvIArS7xnkaN6TOwxNLY/Jp3wFpD0Ecg2Rhloubu/aBJ80xjVQpag0IcK8H8ycuYSwHsta
    # bA/ajCoz1WScpyQC4Ixv03GlDuh4C7h/GdwLRoJwM2LfI/HhR3POB7de1bcsLqUoNVMDWgR2DYsBp/bHhp4yLn/ExVJOSS8PYi5aOxICL0BzP
    # kbozGIzhuxwsVtu2xDbSS3/jCc7EsubDBjeYI7IpSJVYam2Yo9hJiCwuwjwIDAQAB
    # -----END PUBLIC KEY-----'''
    # signatureData = '{"packageName":"com.qzgametw.mzcsgpl","productId":"mzcs_qzgametw_03",' \
    #                 '"purchaseTime":1492004899726,"purchaseState":0,"developerPayload":" ",' \
    #                 '"purchaseToken":"efmfkidinakmihlmcaflapoi.AO-J1OyXrygC0nQfwka_1TR8U5n8' \
    #                 'X1yrvb-z8lWY65gkjwNbPd06n4Z6RcjRmg98LASxn3WzBgvnFT832DJgFgydenfh8Iv9X4' \
    #                 'OO_-m2rZgn_47mPHSnHFZT_dENCIbqfjp6rGBw7qkm"}'
    # signature = 'CLCap/+qEx7i86ouSHX7KVYGWJ4DNorgsI0M/0AFIL2Sv9US2QUZDRs4mK0vsg1su05Eu0BHv7Vvv' \
    #             'BPgFjdb1/Oq1nLE5cF3FQ5g49b3T731wb3cNdaPqjoQ8DfQZx+C6M3y0tcpMsi/TF6agoWTLxNW71' \
    #             'sTnRVUFC4moTliFeiP+6cM1TNWWUJ9jYNw4mMzkEeX6qH5OS6vpQyE9isoHViv2+Us6skoQM8DX9d' \
    #             'LRVU38gEYZRlZPTRkeb9wbZKa6p1cggZEiXOboCHPFtjuQCbp0GyXboyJX8Nk9pc3PQKN4Mpz94pB' \
    #             'EJJ7xSViMLfbi4pw/jwKr5GA18S8o2oevw=='
    # rsa = Rsa(googlePublicKey, None)
    # print("Google订单验证:", rsa.b64verify(signatureData, signature))

    # ### json ###
    # j = jsonDump({"bytes": b"b",
    #               "str": u"d",
    #               "float": 123.456,
    #               "cn_str": u"中文",
    #               "cn_bytes": b'\xe4\xb8\xad\xe6\x96\x87',
    #               "win_path": "C:\Python27\python.exe",
    #               "linux_path": "/home/site/main.py"
    #               }, ensure_ascii=1)
    # print(type(j))
    # print("%r" % j)
    # print(j)
    # print(jsonLoad(j.encode("utf8")))
    # print(jsonLoad(j))

    # ### 时间 ###
    # print("当前时间戳 秒: %s 毫秒:%s" % (ts(), ts(False)))
    # print("时间戳转字符串", ts2str(ts(), "%Y-%m-%d %H:%M:%S"), ts2dateStr(), ts2timeStr())
    # print("字符串转时间戳", str2ts(ts2str()))

    # ### url编码 ###
    urlData = {123: 123, "b": b'\xe4\xb8\xad\xe6\x96\x87', u"c": u"中文"}
    urlCode = urlEncode(urlData)
    print(type(urlCode), urlCode)
    print(urlDecode(urlCode))

    # ### 性能测试 ###
    import timeit

    def f1():
        pass

    def f2():
        pass
    assert f1() == f2(), "%r != %r" % (f1(), f2())
    print(timeit.Timer("f1()", "from __main__ import f1").repeat(3, 100))
    print(timeit.Timer("f2()", "from __main__ import f2").repeat(3, 100))
    # print(timeit.timeit("rsa.b64verify(signatureData, signature)",
    #                     setup="from __main__ import rsa, signatureData, signature",
    #                     number=100))
    # print(timeit.Timer("rsa.b64verify(signatureData, signature)",
    #                    "from __main__ import rsa, signatureData, signature"
    #                    ).repeat(3, 100))

    input("end")
