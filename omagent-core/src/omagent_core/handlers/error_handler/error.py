class VQLError(Exception):
    def __init__(self, code, msg=None, detail=""):
        """
        :param code: Error code
        :param msg: Error message, for system display.
        :param detail: Error detail, for debugging.
        - 500: "内部错误",
        - 501: "图片错误: 无法读取",
        - 502: "图片错误: 图片损坏",
        - 503: "图片错误: 无法获取",
        - 504: "图片错误: 无法识别",
        - 505: "图片错误: 不存在的key",
        - 506: "图片错误: 无法连接数据库",
        - 511: "请求错误: 服务处理失败",
        - 515: "请求错误: 超过重试次数，无法访问地址",
        - 516: "请求错误: 不存在的地址",
        - 517: "请求错误: 错误的请求格式",
        - 518: "请求错误: 非法的请求地址",
        - 550: "IBase错误",
        - 570: "回调错误: 处理结果回调失败"
        """

        code2msg = {
            500: "内部错误",
            501: "图片错误: 无法读取",  # 图片文件无法读取
            502: "图片错误: 图片损坏",  # 图片文件损坏
            503: "图片错误: 无法获取",  # 图片获取失败
            504: "图片错误: 无法识别",  # 图片文件不支持
            505: "图片错误: 不存在的key",  # Redis模式获取数据时key不存在
            506: "图片错误: 无法连接数据库",  # Redis模式获取数据时,无法连接Redis
            511: "请求错误: 服务处理失败",  # 不明原因的Atom报错
            515: "请求错误: 超过重试次数，无法访问地址",  # API的URL或端口错误，无法访问
            516: "请求错误: 错误的地址",  # API的路由地址错误
            517: "请求错误: 错误的请求格式",  # 入参格式错误
            518: "请求错误: 非法的请求地址",  # atom的api地址格式错误
            550: "IBase错误",  # R2Base 错误
            570: "回调错误: 处理结果回调失败",  # 算法处理结果回调时发生错误
            800: "llm错误: 非预期的返回结果",  # llm返回结果不符合预期
        }

        self.code = code
        self.detail = detail
        if msg:
            self.msg = msg
        else:
            self.msg = code2msg[code]

    def __str__(self):
        return repr(
            "Code: {} | message: {} | detail:{}".format(
                self.code, self.msg, self.detail
            )
        )
