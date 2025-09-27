#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
交互式脚本: 在中英混排时对英文字母、数字、符号与 CJK (中日韩) 字符之间添加空格
依赖: pangu (https://github.com/vinta/pangu.py / https://pypi.org/project/pangu/)
功能:
  - 使用 pangu.spacing_text 做主处理 (在 CJK 与半角字符之间插入空格)
  - 在 pangu 的基础上做若干细微的正则规范化 (去除 CJK 与全角标点之间多余空格、折叠连续空格等)
  - 提供交互式循环, 用户输入文本并得到排版结果; 输入 "exit" 或 "q" 退出
"""

# 导入依赖库
from __future__ import annotations

import re
import sys
import subprocess
import importlib
from typing import Optional


# 定义了完整的 CJK 字符 Unicode 范围 (用于正则), 确保全面覆盖。
_CJK_RANGES = (
    r"\u4E00-\u9FFF"  # 常用汉字
    r"\u3400-\u4DBF"  # 扩展 A
    r"\uF900-\uFAFF"  # 兼容表意文字
    r"\u3040-\u309F"  # 平假名
    r"\u30A0-\u30FF"  # 片假名
    r"\uAC00-\uD7AF"  # 韩文音节
)
_CJK_CLASS = f"[{_CJK_RANGES}]"


def ensure_pangu_module() -> Optional[object]:
    """
    依赖管理: 自动检测并安装必需的 pangu 库, 确保 pangu 模块可用:
      - 先尝试直接 import
      - 若失败, 尝试用当前 Python 解释器自动 pip 安装 `pangu` 然后再次 import
      - 若仍失败, 返回 None (调用处应友好提示用户手动安装)
    注意: 自动安装需要网络权限并且在某些环境下可能失败 (虚拟环境、无权限等) 。
    """
    try:
        import pangu  # type: ignore

        return pangu

    except Exception:
        print("检测到 pangu 未安装, 尝试通过 pip 自动安装 (需要网络) ...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", "pangu"]
            )
            # 尝试重新 import
            importlib.invalidate_caches()
            import pangu  # type: ignore

            print("✅ pangu 安装并导入成功。")
            return pangu
        except Exception as e:
            print("❌ 自动安装 pangu 失败: ", e)
            print("✅ 请手动运行: pip install -U pangu, 然后重新运行此脚本。")
            return None


def normalize_spacing(text: str) -> str:
    """
    核心排版逻辑, 在 pangu 处理后进行额外的正则规范化, 目标是 “像素级” / 强迫症级别的视觉整洁:
      1. 把非断行空格替换为普通空格
      2. 去掉 CJK 与全角 (中文) 标点之间不必要的空格, 例如 "你好 , " -> "你好, "
      3. 去掉全角括号/引号内外多余空格, 例如 " (  今天" -> " (今天", "今天 ) " -> "今天) "
      4. 去掉引号/书名号前后不必要的空格 (尽量保持中文标点与 CJK 紧贴)
      5. 折叠连续多个空格为单个空格 (除非用户刻意输入多个空格)
      6. 两端 strip
    这些规则配合 pangu 可以达到更精细的排版效果。
    """
    # 1) 统一空格字符 (将不同种类的空格统一为普通空格)
    text = text.replace("\u00a0", " ").replace("\u2007", " ").replace("\u202f", " ")

    # 2) 去掉 CJK 与中文标点之间不必要的空格 (常见中文全角标点)
    #    例如:  "你好 , " 或 "你好 。" -> "你好, " / "你好."
    #    匹配: CJK_char 任何空白 标点 -> 替换为 CJK_char + 标点
    text = re.sub(
        rf"({_CJK_CLASS})\s+([,，.。!！?？、;；:：·~～—…...])",
        r"\1\2",
        text,
    )

    # 3) 去掉标点前多余空格 (如 半角/全角右括号等) :
    text = re.sub(r"\s+([) 】》」』\]\)\}])", r"\1", text)

    # 4) 去掉标点后多余空格 (如 左括号/左引号后不应有空格)
    text = re.sub(r"([ (【《「『\[\(\{])\s+", r"\1", text)

    # 5) 对中文引号 (“” ‘’) 的前后空格做微调: 去掉引号与 CJK 之间的空格
    text = re.sub(
        rf"({_CJK_CLASS})\s+([“‘])", r"\1\2", text
    )  # CJK + 空格 + 开引号 -> 紧贴
    text = re.sub(
        rf"([”’])\s+({_CJK_CLASS})", r"\1\2", text
    )  # 关引号 + 空格 + CJK -> 紧贴

    # 6) 折叠多个连续空格 (不影响换行)
    text = re.sub(r" {2,}", " ", text)

    # 7) 清除行首行尾多余空白
    text = text.strip()

    return text


def format_text_with_pangu(pangu_module: object, raw: str) -> str:
    """
    主处理流程, 先用 pangu.spacing_text 做主处理, 然后调用 normalize_spacing 做细化清理。
      - 我们把 pangu 的结果视为 “基础规范化”, 再通过额外正则确保 CJK 与全角标点
      - 之间无多余空格等像素级调整
    """
    # pangu 提供 spacing_text 函数 (返回处理后的字符串)
    try:
        spaced = pangu_module.spacing_text(raw)
    except Exception:
        # 若 pangu 的 API 异常, 为了稳健性退回原始文本并尽量做最基本的清理
        spaced = raw

    # 进一步做细节处理
    final_text = normalize_spacing(spaced)

    return final_text


def main():
    """
    主循环: 交互式读取用户输入并输出排版后的文本, 直到输入 'exit' 或 'q'。
      - 提供易用的用户交互界面
      - 处理退出指令
      - 优雅的错误处理
    """
    pangu_module = ensure_pangu_module()
    if pangu_module is None:
        # 如果无法安装或导入 pangu, 则提示用户并继续, 但排版功能会降级 (不到位)
        print("❌ 警告: pangu 未安装, 脚本无法使用 pangu 的完整功能。")
        print("✅ 请先安装 pangu: pip install -U pangu, 然后重新运行。")
        # 仍然允许用户输入, 但我们只能做有限的正则清理
    else:
        # 简短提示 pangu 已启用
        print("✅ 已启用 pangu 排版支持。按 Ctrl + C 或输入 'exit'/'q' 退出程序。")

    try:
        while True:
            print("*" * 100)
            raw = input("📝 在这里输入要排版的文本内容 (输入 'exit' 或 'q' 退出): \n")
            if raw.strip().lower() in ("exit", "q"):
                print("👋 退出程序。。。再见！！！")
                print("*" * 100)
                break

            if pangu_module is not None:
                out = format_text_with_pangu(pangu_module, raw)
            else:
                # pangu 不可用时, 尽量做最小化清理 (去 NBSP, 折叠空格, 去两端空白)
                temp = raw.replace("\u00a0", " ")
                temp = re.sub(r" {2,}", " ", temp).strip()
                out = normalize_spacing(temp)  # 仍然应用 normalize_spacing 的规则

            print(f"\n\n📄 排版后的文本内容: \n{out}")

    except KeyboardInterrupt:
        print("\n👋 收到 KeyboardInterrupt, 程序退出。。。")
        print("*" * 100)


if __name__ == "__main__":
    main()
