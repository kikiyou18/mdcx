#!/usr/bin/env python3

import re
import time

from lxml import etree

from mdcx.config.manager import config
from mdcx.models.log_buffer import LogBuffer


def get_title(html):
    result = html.xpath("//h1/text()")
    return result[0] if result else ""


def get_actor(html):
    actor_result = html.xpath(
        '//div[@class="box_works01_list clearfix"]//span[text()="出演女優"]/following-sibling::p[1]/text()'
    )
    return ",".join(actor_result)


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_outline(html):
    result = html.xpath("//div[@class='box_works01_text']/p/text()")
    return result[0] if result else ""


def get_runtime(html):
    result = html.xpath('//span[contains(text(), "収録時間")]/following-sibling::*//text()')
    if result:
        result = re.findall(r"\d+", result[0])
    return result[0] if result else ""


def get_series(html):
    result = html.xpath('//span[contains(text(), "系列")]/following-sibling::*//text()')
    return "".join(result).strip() if result else ""


def get_director(html):
    result = html.xpath(
        '//span[contains(text(), "导演") or contains(text(), "導演") or contains(text(), "監督")]/following-sibling::*//text()'
    )
    return result[0] if result else ""


def get_publisher(html):
    result = html.xpath('//span[contains(text(), "メーカー")]/following-sibling::*//text()')
    return result[0] if result else "DAHLIA"


def get_release(html):
    result = html.xpath('//div[@class="view_timer"]//span[text()="配信開始日"]/following-sibling::p[1]/text()')
    return result[0].replace("/", "-") if result else ""


def get_year(release):
    result = re.findall(r"\d{4}", release)
    return result[0] if result else ""


def get_tag(html):
    result = html.xpath('//a[@class="genre"]//text()')
    tag = ""
    for each in result:
        tag += each.strip().replace("，", "") + ","
    return tag.strip(",")


def get_cover(html):
    result = html.xpath("//a[@class='pop_sample']/img/@src")
    return result[0].replace("?output-quality=60", "") if result else ""


def get_extrafanart(html):  # 获取封面链接
    extrafanart_list = html.xpath("//a[@class='pop_img']/@href")
    return extrafanart_list


def get_trailer(html):  # 获取预览片
    result = html.xpath("//a[@class='pop_sample']/@href")
    return result[0] if result else ""


async def main(
    number,
    appoint_url="",
    **kwargs,
):
    # https://faleno.jp/top/works/fsdss564/
    # https://dahlia-av.jp/works/dldss177/
    start_time = time.time()
    website_name = "dahlia"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url
    title = ""
    cover_url = ""
    poster_url = ""
    image_download = True
    image_cut = "right"
    web_info = "\n       "
    debug_info = ""
    number_lo = number.lower()
    real_url_list = []
    real_url_list = [real_url] if real_url else [f"https://dahlia-av.jp/works/{number_lo.replace('-', '')}/"]

    LogBuffer.info().write("\n    🌐 dahlia")
    mosaic = "有码"
    try:  # 捕获主动抛出的异常
        for real_url in real_url_list:
            debug_info = f"番号地址: {real_url} "
            LogBuffer.info().write(web_info + debug_info)

            html_info, error = await config.async_client.get_text(real_url)
            if html_info is None:
                debug_info = f"请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                continue

            html_detail = etree.fromstring(html_info, etree.HTMLParser())

            # ========================================================================收集信息
            title = get_title(html_detail)
            if not title:
                debug_info = "数据获取失败: 番号标题不存在！"
                LogBuffer.info().write(web_info + debug_info)
                continue
            break
        else:
            raise Exception(debug_info)

        actor = get_actor(html_detail)  # 获取actor
        actor_photo = get_actor_photo(actor)
        for each in actor_photo:
            title = title.replace(" " + each, "")
        cover_url = get_cover(html_detail)  # 获取cover
        poster_url = (
            cover_url.replace("_web_h4", "_h1").replace("_1200.jpg", "_2125.jpg").replace("_tsp.jpg", "_actor.jpg")
        )
        outline = get_outline(html_detail)
        tag = ""
        release = get_release(html_detail)
        year = get_year(release)
        runtime = get_runtime(html_detail)
        score = ""
        series = get_series(html_detail)
        director = get_director(html_detail)
        studio = get_publisher(html_detail)
        publisher = studio
        extrafanart = get_extrafanart(html_detail)
        trailer = get_trailer(html_detail)
        website = real_url
        try:
            dic = {
                "number": number,
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "outline": outline,
                "originalplot": outline,
                "tag": tag,
                "release": release,
                "year": year,
                "runtime": runtime,
                "score": score,
                "series": series,
                "director": director,
                "studio": studio,
                "publisher": publisher,
                "source": "dahlia",
                "actor_photo": actor_photo,
                "thumb": cover_url,
                "poster": poster_url,
                "extrafanart": extrafanart,
                "trailer": trailer,
                "image_download": image_download,
                "image_cut": image_cut,
                "mosaic": mosaic,
                "website": website,
                "wanted": "",
            }
            debug_info = "数据获取成功！"
            LogBuffer.info().write(web_info + debug_info)

        except Exception as e:
            debug_info = f"数据生成出错: {str(e)}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

    except Exception as e:
        # print(traceback.format_exc())
        LogBuffer.error().write(str(e))
        dic = {
            "title": "",
            "thumb": "",
            "website": "",
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return dic


if __name__ == "__main__":
    # yapf: disable
    # print(main('dhla-009'))
    print(main('dldss-177'))
