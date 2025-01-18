import httpx
import requests

from .error import VQLError
from .logger import logging


def request(
    json: dict,
    url: str,
    headers: dict | None = None,
) -> dict:
    try:
        res = requests.post(url=url, json=json, headers=headers)
    except Exception as error:
        logging.error(
            "Request URL: {} | Request body: {} | Error: {}".format(url, json, error)
        )
        raise VQLError(511, detail=str(error))
    if res.status_code < 299:
        return res.json()
    elif res.status_code == 404:
        logging.error("Request URL: {} | Error[404]: 请求错误: 错误的地址".format(url))
        raise VQLError(516)
    elif res.status_code == 422:
        logging.error(
            "Request URL: {} | Request body: {} | Error[422]: 请求错误: 错误的请求格式".format(
                url, json
            )
        )
        raise VQLError(517)
    else:
        info = res.json()
        logging.error(
            "Request URL: {} | Request body: {} | Error: {}".format(url, json, info)
        )
        raise VQLError(511, detail=info)


async def arequest(url: str, json: dict, headers: dict | None = None) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url=url, json=json, headers=headers, timeout=30)
    except Exception as error:
        logging.error(
            "Request URL: {} | Request body: {} | Error: {}".format(url, json, error)
        )
        raise VQLError(511, detail=str(error))

    if res.status_code < 299:
        return res.json()
    elif res.status_code == 404:
        logging.error("Request URL: {} | Error[404]: 请求错误: 错误的地址".format(url))
        raise VQLError(516)
    elif res.status_code == 422:
        logging.error(
            "Request URL: {} | Request body: {} | Error[422]: 请求错误: 错误的请求格式".format(
                url, json
            )
        )
        raise VQLError(517)
    else:
        info = res.json()
        logging.error(
            "Request URL: {} | Request body: {} | Error: {}".format(url, json, info)
        )
        raise VQLError(511, detail=info)
