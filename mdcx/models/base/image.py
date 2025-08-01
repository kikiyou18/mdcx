import os
import shutil
import time
import traceback

import aiofiles.os
from PIL import Image

from mdcx.config.extend import get_movie_path_setting
from mdcx.config.manager import config
from mdcx.config.resources import resources
from mdcx.models.base.file import movie_lists
from mdcx.models.log_buffer import LogBuffer
from mdcx.signals import signal
from mdcx.utils import convert_path, get_used_time, split_path
from mdcx.utils.file import check_pic_async, move_file_async


async def extrafanart_copy2(folder_new_path: str):
    start_time = time.time()
    download_files = config.download_files
    keep_files = config.keep_files
    extrafanart_copy_folder = config.extrafanart_folder
    extrafanart_path = convert_path(os.path.join(folder_new_path, "extrafanart"))
    extrafanart_copy_path = convert_path(os.path.join(folder_new_path, extrafanart_copy_folder))

    # 如果不保留，不下载，删除返回
    if "extrafanart_copy" not in keep_files and "extrafanart_copy" not in download_files:
        if await aiofiles.os.path.exists(extrafanart_copy_path):
            shutil.rmtree(extrafanart_copy_path, ignore_errors=True)
        return

    # 如果保留，并且存在，返回
    if "extrafanart_copy" in keep_files and await aiofiles.os.path.exists(extrafanart_copy_path):
        LogBuffer.log().write(f"\n 🍀 Extrafanart_copy done! (old)({get_used_time(start_time)}s) ")
        return

    # 如果不下载，返回
    if "extrafanart_copy" not in download_files:
        return

    if not await aiofiles.os.path.exists(extrafanart_path):
        return

    if await aiofiles.os.path.exists(extrafanart_copy_path):
        shutil.rmtree(extrafanart_copy_path, ignore_errors=True)
    shutil.copytree(extrafanart_path, extrafanart_copy_path)

    filelist = await aiofiles.os.listdir(extrafanart_copy_path)
    for each in filelist:
        file_new_name = each.replace("fanart", "")
        file_path = os.path.join(extrafanart_copy_path, each)
        file_new_path = os.path.join(extrafanart_copy_path, file_new_name)
        await move_file_async(file_path, file_new_path)
    LogBuffer.log().write(f"\n 🍀 ExtraFanart_copy done! (copy extrafanart)({get_used_time(start_time)}s)")


async def extrafanart_extras_copy(folder_new_path: str):
    start_time = time.time()
    download_files = config.download_files
    keep_files = config.keep_files
    extrafanart_path = convert_path(os.path.join(folder_new_path, "extrafanart"))
    extrafanart_extra_path = convert_path(os.path.join(folder_new_path, "behind the scenes"))

    if "extrafanart_extras" not in download_files and "extrafanart_extras" not in keep_files:
        if await aiofiles.os.path.exists(extrafanart_extra_path):
            shutil.rmtree(extrafanart_extra_path, ignore_errors=True)
        return True

    if "extrafanart_extras" in keep_files and await aiofiles.os.path.exists(extrafanart_extra_path):
        LogBuffer.log().write(f"\n 🍀 Extrafanart_extras done! (old)({get_used_time(start_time)}s)")
        return True

    if "extrafanart_extras" not in download_files:
        return True

    if not await aiofiles.os.path.exists(extrafanart_path):
        return False

    if await aiofiles.os.path.exists(extrafanart_extra_path):
        shutil.rmtree(extrafanart_extra_path)
    shutil.copytree(extrafanart_path, extrafanart_extra_path)
    filelist = await aiofiles.os.listdir(extrafanart_extra_path)
    for each in filelist:
        file_new_name = each.replace("jpg", "mp4")
        file_path = os.path.join(extrafanart_extra_path, each)
        file_new_path = os.path.join(extrafanart_extra_path, file_new_name)
        await move_file_async(file_path, file_new_path)
    LogBuffer.log().write(f"\n 🍀 Extrafanart_extras done! (copy extrafanart)({get_used_time(start_time)}s)")
    return True


async def _add_to_pic(pic_path: str, img_pic: Image.Image, mark_size: int, count: int, mark_name: str):
    # 获取水印图片，生成水印
    mark_fixed = config.mark_fixed
    mark_pos_corner = config.mark_pos_corner
    mark_pic_path = ""
    if mark_name == "4K":
        mark_pic_path = resources.icon_4k_path
    elif mark_name == "8K":
        mark_pic_path = resources.icon_8k_path
    elif mark_name == "字幕":
        mark_pic_path = resources.icon_sub_path
    elif mark_name == "有码":
        mark_pic_path = resources.icon_youma_path
    elif mark_name == "破解":
        mark_pic_path = resources.icon_umr_path
    elif mark_name == "流出":
        mark_pic_path = resources.icon_leak_path
    elif mark_name == "无码":
        mark_pic_path = resources.icon_wuma_path

    if mark_pic_path:
        try:
            img_subt = Image.open(mark_pic_path)
            img_subt = img_subt.convert("RGBA")
            scroll_high = int(img_pic.height * mark_size / 40)
            scroll_width = int(scroll_high * img_subt.width / img_subt.height)
            img_subt = img_subt.resize((scroll_width, scroll_high), resample=Image.Resampling.LANCZOS)
        except Exception:
            signal.show_log_text(f"{traceback.format_exc()}\n Open Pic: {mark_pic_path}")
            print(traceback.format_exc())
            return
        r, g, b, a = img_subt.split()  # 获取颜色通道, 保持png的透明性

        # 固定一个位置
        if mark_fixed == "corner":
            corner_top_left = [(0, 0), (scroll_width, 0), (scroll_width * 2, 0)]
            corner_bottom_left = [
                (0, img_pic.height - scroll_high),
                (scroll_width, img_pic.height - scroll_high),
                (scroll_width * 2, img_pic.height - scroll_high),
            ]
            corner_top_right = [
                (img_pic.width - scroll_width * 4, 0),
                (img_pic.width - scroll_width * 2, 0),
                (img_pic.width - scroll_width, 0),
            ]
            corner_bottom_right = [
                (img_pic.width - scroll_width * 4, img_pic.height - scroll_high),
                (img_pic.width - scroll_width * 2, img_pic.height - scroll_high),
                (img_pic.width - scroll_width, img_pic.height - scroll_high),
            ]
            corner_dic = {
                "top_left": corner_top_left,
                "bottom_left": corner_bottom_left,
                "top_right": corner_top_right,
                "bottom_right": corner_bottom_right,
            }
            mark_postion = corner_dic[mark_pos_corner][count]

        # 封面四个角的位置
        else:
            pos = [
                {"x": 0, "y": 0},
                {"x": img_pic.width - scroll_width, "y": 0},
                {"x": img_pic.width - scroll_width, "y": img_pic.height - scroll_high},
                {"x": 0, "y": img_pic.height - scroll_high},
            ]
            mark_postion = (pos[count]["x"], pos[count]["y"])
        try:  # 图片如果下载不完整时，这里会崩溃，跳过
            img_pic.paste(img_subt, mark_postion, mask=a)
        except Exception:
            signal.show_log_text(traceback.format_exc())
        img_pic = img_pic.convert("RGB")
        temp_pic_path = pic_path + ".[MARK].jpg"
        try:
            img_pic.load()
            img_pic.save(temp_pic_path, quality=95, subsampling=0)
        except Exception:
            signal.show_log_text(traceback.format_exc())
        img_subt.close()
        if await check_pic_async(temp_pic_path):
            await move_file_async(temp_pic_path, pic_path)


async def add_mark_thread(pic_path: str, mark_list: list[str]):
    mark_size = config.mark_size
    mark_fixed = config.mark_fixed
    mark_pos = config.mark_pos
    mark_pos_hd = config.mark_pos_hd
    mark_pos_sub = config.mark_pos_sub
    mark_pos_mosaic = config.mark_pos_mosaic
    mark_pos_corner = config.mark_pos_corner
    try:
        img_pic = Image.open(pic_path)
    except Exception:
        signal.show_log_text(f"{traceback.format_exc()}\n Open Pic: {pic_path}")
        return

    if mark_fixed == "corner":
        count = 0
        if "left" not in mark_pos_corner:
            count = 3 - len(mark_list)
        for mark_name in mark_list:
            await _add_to_pic(pic_path, img_pic, mark_size, count, mark_name)
            count += 1
    else:
        pos = {
            "top_left": 0,
            "top_right": 1,
            "bottom_right": 2,
            "bottom_left": 3,
        }
        mark_pos_count = pos.get(mark_pos, 0)  # 获取自定义位置, 取余配合pos达到顺时针添加的效果
        count_hd = 0
        for mark_name in mark_list:
            if mark_name == "4K" or mark_name == "8K":  # 4K/8K使用固定位置
                count_hd = pos.get(mark_pos_hd, 0)
                await _add_to_pic(pic_path, img_pic, mark_size, count_hd, mark_name)
            elif mark_fixed == "fixed":  # 固定位置
                count = pos.get(mark_pos_sub, 0) if mark_name == "字幕" else pos.get(mark_pos_mosaic, 0)
                await _add_to_pic(pic_path, img_pic, mark_size, count, mark_name)
            else:  # 不固定位置
                if mark_pos_count % 4 == count_hd:
                    mark_pos_count += 1
                if mark_name == "字幕":
                    await _add_to_pic(pic_path, img_pic, mark_size, mark_pos_count % 4, mark_name)  # 添加字幕
                    mark_pos_count += 1
                else:
                    await _add_to_pic(pic_path, img_pic, mark_size, mark_pos_count % 4, mark_name)
    img_pic.close()


async def add_del_extrafanart_copy(mode: str) -> None:
    signal.show_log_text(f"Start {mode} extrafanart copy! \n")

    movie_path, *_, extrafanart_folder, _ = get_movie_path_setting()
    signal.show_log_text(f" 🖥 Movie path: {movie_path} \n 🔎 Checking all videos, Please wait...")
    movie_type = config.media_type
    movie_list = await movie_lists([], movie_type, movie_path)  # 获取所有需要刮削的影片列表

    extrafanart_folder_path_list = []
    for movie in movie_list:
        movie_file_folder_path = split_path(movie)[0]
        extrafanart_folder_path = os.path.join(movie_file_folder_path, "extrafanart")
        if await aiofiles.os.path.exists(extrafanart_folder_path):
            extrafanart_folder_path_list.append(movie_file_folder_path)
    extrafanart_folder_path_list = list(set(extrafanart_folder_path_list))
    extrafanart_folder_path_list.sort()
    total_count = len(extrafanart_folder_path_list)
    new_count = 0
    count = 0
    for each in extrafanart_folder_path_list:
        extrafanart_folder_path = os.path.join(each, "extrafanart")
        extrafanart_copy_folder_path = os.path.join(each, extrafanart_folder)
        count += 1
        if mode == "add":
            if not await aiofiles.os.path.exists(extrafanart_copy_folder_path):
                shutil.copytree(extrafanart_folder_path, extrafanart_copy_folder_path)
                signal.show_log_text(f" {count} new copy: \n  {extrafanart_copy_folder_path}")
                new_count += 1
            else:
                signal.show_log_text(f" {count} old copy: \n  {extrafanart_copy_folder_path}")
        else:
            if await aiofiles.os.path.exists(extrafanart_copy_folder_path):
                shutil.rmtree(extrafanart_copy_folder_path, ignore_errors=True)
                signal.show_log_text(f" {count} del copy: \n  {extrafanart_copy_folder_path}")
                new_count += 1

    signal.show_log_text(f"\nDone! \n Total: {total_count}  {mode} copy: {new_count} ")
    signal.show_log_text("================================================================================")
