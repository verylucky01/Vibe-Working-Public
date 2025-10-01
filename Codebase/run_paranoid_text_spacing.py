"""
交互式脚本: 在中英混排时, 对英文字母、数字、标点符号与 CJK (中日韩) 字符之间添加空格
依赖: pangu (https://github.com/vinta/pangu.py and https://pypi.org/project/pangu/)
功能:
  - 使用 pangu.spacing_text() 做主处理 (在 CJK 与半角字符之间插入空格)
  - 在 pangu 的基础上做若干细微的完善 (去除 CJK 与全角标点之间多余空格、折叠连续空格等)
  - 提供交互式循环, 用户输入文本即可得到排版结果; 输入 "exit" 或 "q" 退出
"""

# 导入依赖库
from __future__ import annotations

import re
import sys
import subprocess
import importlib
from typing import Optional


# 定义完整的 CJK 字符 Unicode 范围 (用于正则表达式匹配), 确保全面覆盖。
_CJK_RANGES = (
    "\u4e00-\u9fff"  # CJK Unified Ideographs
    "\u3400-\u4dbf"  # CJK Unified Ideographs Extension A
    "\uf900-\ufaff"  # CJK Compatibility Ideographs
    "\u3040-\u309f"  # Hiragana
    "\u30a0-\u30ff"  # Katakana
    "\uac00-\ud7af"  # Hangul Syllables
    "\U00020000-\U0002a6df"  # CJK Extension B
    "\U0002a700-\U0002b73f"  # Extension C
    "\U0002b740-\U0002b81f"  # Extension D
    "\U0002b820-\U0002ceaf"  # Extension E
    "\U0002ceb0-\U0002ebef"  # Extension F
    "\U00030000-\U0003134f"  # Extension G
    "\U00031350-\U000323af"  # Extension G
    "\U0002ebf0-\U0002ee5f"  # Extension I
    "\U0002f800-\U0002fa1f"  # Compatibility Supplement
)
_CJK_CLASS = f"[{_CJK_RANGES}]"

# pip 国内镜像源
TRUSTED_HOST = "repo.huaweicloud.com"
INDEX_URL = "https://repo.huaweicloud.com/repository/pypi/simple/"

# 各种可能的空格格式都替换成 " "
_SPACE_NORMALIZATION = str.maketrans(
    {
        "\u00a0": " ",
        "\u0020": " ",
        "\u2000": " ",
        "\u2001": " ",
        "\u2002": " ",
        "\u2003": " ",
        "\u2004": " ",
        "\u2005": " ",
        "\u2006": " ",
        "\u2007": " ",
        "\u2008": " ",
        "\u2009": " ",
        "\u200a": " ",
        "\u1680": " ",
        "\u2028": " ",
        "\u202f": " ",
        "\u205f": " ",
        "\u3000": " ",
    }
)

# _FULLWIDTH_PUNCT = re.escape(",，.。!！?？、;；:：·~～—…")
# _FULLWIDTH_PUNCT = re.escape(",.!?;、:·~～———…")

# 全角标点符号和半角标点符号
_FULLWIDTH_PUNCT = re.escape("，、。？！；：·“”‘’—【】〖〗——《》「」（）〔〕〈〉……")
_HALF_PUNCT = re.escape(",.!?@#$%^&*+={}\\|;:~-`…""''[]<>()")

# 可能组成左右括号的形式
# _OPENERS = re.escape("([{（〔【《〈「『〖〘〚“‘'")
# _CLOSERS = re.escape(")]}）〕】》〉」』〗〙〛”’'")
_PAIR_OPENERS = re.escape("([{（〔【《〈「『〖〘〚“‘\"'")
_PAIR_CLOSERS = re.escape(")]}）〕】》〉」』〗〙〛”’\"'")


# 去除 CJK 与标点符号之间多余的空格
_PUNCT_TO_CJK = re.compile(
    rf"([{_FULLWIDTH_PUNCT}{_HALF_PUNCT}])([ \t]+)({_CJK_CLASS})"
)
_CJK_TO_PUNCT = re.compile(
    rf"({_CJK_CLASS})([ \t]+)([{_FULLWIDTH_PUNCT}{_HALF_PUNCT}])"
)

# 去除全角标点符号与半角标点符号之间多余的空格
_HALF_PUNCT_GAP = re.compile(
    rf"([{_HALF_PUNCT}])([ \t]+)([{_FULLWIDTH_PUNCT}{_HALF_PUNCT}])"
)
_FULLWIDTH_PUNCT_GAP = re.compile(
    rf"([{_FULLWIDTH_PUNCT}])([ \t]+)([{_FULLWIDTH_PUNCT}{_HALF_PUNCT}])"
)
# 去除英文和数字跟全角、半角标点符号之间多余的空格, 去除标点符号前后多余的空格
_AFTER_PUNCT_SPACE = re.compile(rf"([{_FULLWIDTH_PUNCT}{_HALF_PUNCT}])([ \t]+)")
_BEFORE_PUNCT_SPACE = re.compile(rf"([ \t]+)([{_FULLWIDTH_PUNCT}{_HALF_PUNCT}])")

# 去除括号左右两边多余的空格
_SPACE_BEFORE_CLOSER = re.compile(rf"([ \t]+)([{_PAIR_CLOSERS}])")
_SPACE_AFTER_OPENER = re.compile(rf"([{_PAIR_OPENERS}])([ \t]+)")

_MULTI_SPACE = re.compile(r"[ \t]{2,}")

_CJK_GAP = re.compile(rf"({_CJK_CLASS})([ \t]+)({_CJK_CLASS})")


def ensure_pangu_module() -> Optional[object]:
    """
    依赖管理: 自动检测并安装必需的 pangu 库, 确保 pangu 模块可用
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
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-U",
                    "pangu",
                    "--index-url",
                    INDEX_URL,
                    "--trusted-host",
                    TRUSTED_HOST,
                ]
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


def normalize_spacing(text: str, pangu_spacing: object) -> str:
    if not text:
        return text

    text = text.translate(_SPACE_NORMALIZATION)

    text = _AFTER_PUNCT_SPACE.sub(r"\1", text)
    text = _BEFORE_PUNCT_SPACE.sub(r"\2", text)

    text = _CJK_GAP.sub(r"\1\3", text)

    text = _SPACE_BEFORE_CLOSER.sub(r"\2", text)
    text = _SPACE_AFTER_OPENER.sub(r"\1", text)

    text = _CJK_TO_PUNCT.sub(r"\1\3", text)
    text = _PUNCT_TO_CJK.sub(r"\1\3", text)

    text = _HALF_PUNCT_GAP.sub(r"\1\3", text)
    text = _FULLWIDTH_PUNCT_GAP.sub(r"\1\3", text)

    text = _MULTI_SPACE.sub(" ", text)

    return pangu_spacing.spacing_text(text.strip())


def format_text_with_pangu(pangu_module: object, raw: str) -> str:
    """
    主处理流程, 先用 pangu.spacing_text 做主处理, 然后调用 normalize_spacing 做细化清理。
      - 我们把 pangu 的结果视为 “基础规范化”, 再通过额外正则确保 CJK 与全角标点
      - 之间无多余空格等像素级调整
    """
    # pangu 提供 spacing_text 函数 (返回处理后的字符串)
    try:
        spaced = pangu_module.spacing_text(raw)
        # 进一步做细节处理
        final_text = normalize_spacing(spaced, pangu_module)
        return final_text
    except Exception:
        # 若 pangu 的 API 异常, 为了稳健性退回原始文本并尽量做最基本的清理。
        temp = raw.replace("\u00a0", " ")
        out = re.sub(r" {2,}", " ", temp).strip()
        return out


def main():
    """
    主循环: 交互式读取用户输入并输出排版后的文本, 直到输入 'exit' 或 'q' 退出
      - 提供易用的用户交互界面
      - 处理退出指令
      - 优雅的错误处理
    """
    pangu_module = ensure_pangu_module()

    if pangu_module is None:
        # 如果无法安装或导入 pangu, 则提示用户并继续, 但排版功能会降级 (不到位)。
        print("❌ 警告: pangu 未安装, 脚本无法使用 pangu 的完整功能。")
        print("✅ 请先安装 pangu: pip install -U pangu, 然后重新运行。")
    else:
        # 简短提示 pangu 已启用
        print("✅ 已启用 pangu 排版支持。按 Ctrl + C 或输入 'exit'/'q' 退出程序。")

    try:
        while True:
            print("*" * 88)
            raw = input("📝 在这里输入要排版的文本内容 (输入 'exit' 或 'q' 退出): \n")
            if raw.strip().lower() in ("exit", "q"):
                print("👋 退出程序。。。再见！！！")
                print("*" * 88)
                break

            if pangu_module is not None:
                out = format_text_with_pangu(pangu_module, raw)
            else:
                # pangu 不可用时, 尽量做最小化清理 (去 NBSP, 折叠空格, 去两端空白)
                temp = raw.replace("\u00a0", " ")
                out = re.sub(r" {2,}", " ", temp).strip()

            print(f"\n\n📄 排版后的文本内容: \n{out}")

    except KeyboardInterrupt:
        print("\n👋 收到 KeyboardInterrupt, 程序退出。。。")
        print("*" * 88)


if __name__ == "__main__":
    main()
