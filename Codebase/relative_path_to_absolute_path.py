import os
import pathlib
from pathlib import Path
from typing import Union


class PathConversionError(Exception):
    """自定义异常类, 用于路径转换过程中发生的特定错误。"""
    pass


def get_absolute_path(
    relative_path_input: str, return_path_object: bool = True
) -> Union[Path, str]:
    """
    根据用户输入的相对路径恢复出绝对路径, 能在 Windows、Linux、macOS 平台都正确执行。

    本函数充分利用 Python 的 pathlib 模块, 特别是其 `Path.resolve(strict=False)` 方法, 
    以确保即使路径所指的文件或目录不实际存在时, 也能进行可靠的路径转换, 
    返回其理论上的绝对路径形式。

    Args:
        relative_path_input (str): 用户输入的相对路径字符串。
                                   函数会处理路径中可能包含的特殊字符、
                                   操作系统特定的路径分隔符（如 `/` 或 `\`）, 
                                   以及 `.` 和 `..` 等目录导航符。
                                   对于 Python 字符串字面量中的转义字符, 
                                   `pathlib` 会将其视为路径字符串的一部分。
                                   建议在 Python 代码中使用原始字符串（`r"..."`）
                                   来表示包含反斜杠的路径, 以避免 Python 自身的
                                   字符串转义规则造成混淆。
        return_path_object (bool): 如果为 `True`, 函数将返回一个 `pathlib.Path` 对象。
                                   如果为 `False`, 函数将返回绝对路径的字符串表示。
                                   默认为 `True`。

    Returns:
        Union[pathlib.Path, str]: 转换后的绝对路径 `Path` 对象或字符串。

    Raises:
        TypeError: 如果 `relative_path_input` 不是字符串类型。
        PathConversionError: 如果路径字符串虽然是字符串类型, 但其内容在转换为
                             `Path` 对象或在 `resolve()` 过程中遇到非常规的
                             、无法通过 `strict=False` 优雅处理的系统错误。
                             （例如, 权限问题导致无法确定当前工作目录等极少数情况）。
    """
    if not isinstance(relative_path_input, str):
        raise TypeError(
            f"输入路径必须是字符串类型（str）, 但收到了 '{type(relative_path_input).__name__}' 类型。"
        )

    try:
        # 将输入字符串转换为 pathlib.Path 对象。
        # pathlib 会自动处理不同操作系统下的路径分隔符和特殊字符。
        # 例如, 在 Windows 上, 'a/b' 会被解释为 'a\b'。
        path_obj = Path(relative_path_input)

        # 使用 .resolve(strict=False) 方法将路径解析为绝对路径。
        # resolve() 方法会: 
        #   1. 将路径转换为绝对路径（如果输入是相对路径, 则相对于当前工作目录）。
        #   2. 解析路径中的 '.' (当前目录) 和 '..' (父目录) 组件。
        #   3. 解析所有遇到的符号链接 (symlinks), 将其替换为它们指向的实际路径。
        #
        # strict=False 参数是这里的关键, 它确保: 
        #   - 即使路径或其任何组件不存在, 函数也会尽可能地解析路径。
        #   - 它会解析到路径中存在的最后一个组件, 然后将剩余的、不存在的部分
        #     以字符串形式附加到结果中, 而不会引发 FileNotFoundError。
        #     例如, '/a/b/c/d.txt', 如果 '/a/b' 存在但 '/a/b/c' 不存在, 
        #     则 resolve(strict=False) 会返回 Path('/a/b/c/d.txt')。
        #   - 这对于处理用户可能输入的、但尚未在文件系统上创建的文件或目录的路径非常重要, 
        #     满足了 “保证路径转换的完全有效、可靠” 的要求。
        absolute_path_obj = path_obj.resolve(strict=False)

        # 根据用户选择的返回类型, 返回 Path 对象或字符串。
        return absolute_path_obj if return_path_object else str(absolute_path_obj)

    except Exception as e:
        # 捕获其他可能的异常, 例如在极少数情况下, pathlib 内部可能因
        # 操作系统交互问题引发的异常（如权限问题或无法访问 CWD）。
        # 将其包装为自定义异常, 提供更清晰的错误信息。
        raise PathConversionError(
            f"处理路径 '{relative_path_input}' 时发生意外错误: {e}"
        ) from e


def run_tests():
    print("****** 绝对路径恢复功能测试开始 ******")

    # 获取当前工作目录, 用于验证相对路径的预期结果。
    current_working_directory = Path.cwd()
    print(f"当前工作目录 (CWD): {current_working_directory}")

    # 定义一些测试路径
    test_cases = [
        # 1. 简单相对路径
        ("test_file.txt", "简单文件名"),
        ("dir_a/file_b.txt", "多级目录下的文件"),
        ("./current_dir_file.log", "以 './' 开头的当前目录文件"),
        ("../parent_dir_file.conf", "以 '../' 开头的父目录文件"),
        ("../../grandparent_dir_file.dat", "以 '../../' 开头的祖父目录文件"),
        # 2. 包含特殊字符和空格的路径
        ("dir with spaces/file name!.txt", "包含空格和特殊字符的路径"),
        ("中文目录/中文文件.csv", "包含中文的路径"),
        ("dir/file's.zip", "包含单引号的路径"),
        # 注意: Windows 文件名不允许某些字符如 < > : " / \ | ? *
        # 这里测试的 'file".txt' 在 Linux/macOS 上是合法的, 但在 Windows 上 Path.resolve()
        # 可能无法处理或在文件系统层面非法。Pathlib 在创建 Path 对象时通常不会报错, 
        # 但在与 OS 交互时（如 resolve()）可能会遇到问题。
        # 由于 strict=False, 它会尽量解析, 即使路径包含 OS 不允许的字符。
        ('dir/file".txt', "包含双引号的路径 (Linux/macOS 通常允许, Windows 不允许)"),
        (
            "dir/invalid<file>.txt",
            "包含OS非法字符的路径 (Linux/macOS 通常允许, Windows 不允许)",
        ),
        # 3. 路径中包含反斜杠 (Windows 风格分隔符), pathlib 会在非 Windows 平台进行规范化
        (
            r"dir\another_dir\file.txt",
            "包含反斜杠作为分隔符 (Windows风格)",
        ),  # 使用原始字符串确保反斜杠被解释为字面量
        # 4. 空字符串和绝对路径
        ("", "空字符串 (应解析为当前工作目录)"),
        (
            str(
                current_working_directory
                / "existing_subfolder_for_abs"
                / "existing_file.txt"
            ),
            "已存在的绝对路径 (基于 CWD)",
        ),
        (
            (
                "/tmp/test_absolute.txt"
                if os.name == "posix"
                else "C:\\Temp\\test_absolute.txt"
            ),
            "虚拟绝对路径",
        ),
        # 5. 不存在的路径 (应能通过 strict=False 得到理论上的绝对路径)
        ("non_existent_dir/non_existent_file.xyz", "不存在的路径"),
        ("non_existent_file_only.tmp", "不存在的单个文件"),
        # 6. 极端情况的路径 (pathlib 的健壮性测试)
        ("///a/b", "多余的斜杠"),
        ("/../c", "根目录上的父目录导航"),
        ("a/./b/../c", "混合 . 和 .."),
    ]

    # 创建一些用于测试的目录和文件, 确保 resolve() 能找到部分存在的路径或完全存在的路径
    # 这有助于验证 resolve(strict=False) 对实际存在的路径的处理
    setup_paths = [
        current_working_directory / "existing_subfolder_for_abs",
        current_working_directory / "existing_subfolder_for_abs" / "existing_file.txt",
        current_working_directory / "dir_a",
        current_working_directory / "dir_a" / "file_b.txt",
        current_working_directory / "dir with spaces",
        current_working_directory / "dir with spaces" / "file name!.txt",
        current_working_directory / "中文目录",
        current_working_directory / "中文目录" / "中文文件.csv",
    ]

    # 确保虚拟绝对路径的父目录存在, 以便测试其解析行为
    if os.name == "posix":
        abs_temp_dir = Path("/tmp")
        abs_temp_file = Path("/tmp/test_absolute.txt")
    else:  # Windows
        abs_temp_dir = Path("C:\\Temp")
        abs_temp_file = Path("C:\\Temp\\test_absolute.txt")
    setup_paths.extend([abs_temp_dir, abs_temp_file])

    for p in setup_paths:
        if p.suffix:  # 如果路径有后缀, 认为是文件
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
        else:  # 否则认为是目录
            p.mkdir(parents=True, exist_ok=True)
    print("\n====== 测试环境准备完成 ======")

    for i, (input_path, description) in enumerate(test_cases):
        print(f"\n--- 测试案例 {i+1}: {description} ---")
        print(f"输入相对路径: '{input_path}'")

        # 预期结果: 直接使用 Path(input_path).resolve(strict=False)
        # 因为 resolve() 会自动处理相对路径（相对于 CWD）和绝对路径。
        expected_path_obj = Path(input_path).resolve(strict=False)

        # 1. 测试返回 Path 对象
        try:
            actual_path_obj = get_absolute_path(input_path, return_path_object=True)
            print(f"返回 Path 对象 (实际): {actual_path_obj}")
            print(f"返回 Path 对象 (预期): {expected_path_obj}")
            assert (
                actual_path_obj == expected_path_obj
            ), f"错误: Path 对象不匹配! 实际: {actual_path_obj}, 预期: {expected_path_obj}"
            assert isinstance(
                actual_path_obj, Path
            ), f"错误: 返回类型不是 Path 对象! 实际: {type(actual_path_obj)}"
            print("Path 对象测试通过。")
        except PathConversionError as e:
            print(f"Path 对象测试捕获到 PathConversionError: {e}")
        except AssertionError as e:
            print(e)
        except Exception as e:
            print(f"Path 对象测试捕获到意外错误: {e}")

        # 2. 测试返回字符串
        try:
            actual_path_str = get_absolute_path(input_path, return_path_object=False)
            expected_path_str = str(
                expected_path_obj
            )  # 预期字符串就是 Path 对象的字符串表示
            print(f"返回字符串 (实际): {actual_path_str}")
            print(f"返回字符串 (预期): {expected_path_str}")
            assert (
                actual_path_str == expected_path_str
            ), f"错误: 字符串不匹配! 实际: '{actual_path_str}', 预期: '{expected_path_str}'"
            assert isinstance(
                actual_path_str, str
            ), f"错误: 返回类型不是字符串! 实际: {type(actual_path_str)}"
            print("字符串测试通过。")
        except PathConversionError as e:
            print(f"字符串测试捕获到 PathConversionError: {e}")
        except AssertionError as e:
            print(e)
        except Exception as e:
            print(f"字符串测试捕获到意外错误: {e}")

    # ====== 错误处理测试 ======
    print("\n====== 错误处理测试 ======")

    print("\n测试输入非字符串类型 (例如: int):")
    try:
        result = get_absolute_path(123, return_path_object=False)
        print(f"结果: {result} (预期引发 TypeError)")
        assert False, "错误: 未捕获到 TypeError"
    except TypeError as e:
        print(f"成功捕获 TypeError: {e}")
        assert "必须是字符串类型" in str(e)

    print("\n测试输入非字符串类型 (例如: None):")
    try:
        result = get_absolute_path(None, return_path_object=False)
        print(f"结果: {result} (预期引发 TypeError)")
        assert False, "错误: 未捕获到 TypeError"
    except TypeError as e:
        print(f"成功捕获 TypeError: {e}")
        assert "必须是字符串类型" in str(e)

    # Clean up created files and directories
    print("\n====== 清理测试环境 ======")
    # 逆序遍历, 先删除文件再删除空目录
    # 对路径进行排序以确保一致的清理顺序, 通常从最深层开始清理
    for p in reversed(sorted(setup_paths, key=lambda x: len(x.parts))):
        try:
            if p.is_file():
                p.unlink()
                print(f"已删除文件: {p}")
            elif p.is_dir():
                # 尝试删除目录, 但如果包含其他文件, os.rmdir 会失败。
                # 对于测试创建的目录, 我们假设它们是空的或会被递归删除
                # 这里我们只删除空目录。
                if not list(p.iterdir()):  # 检查目录是否为空
                    p.rmdir()
                    print(f"已删除空目录: {p}")
                else:
                    # 如果目录非空, 可能是其他测试或系统文件导致, 跳过删除
                    print(f"目录 '{p}' 非空, 跳过删除。")
        except OSError as e:
            print(f"清理路径 '{p}' 时发生错误: {e}")
    print("清理完成。")
    print("\n====== 绝对路径恢复功能测试结束 ======")


if __name__ == "__main__":
    run_tests()
