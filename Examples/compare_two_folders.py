import os


def get_size_and_files(path):
    """
    获取路径下所有文件的数量、总大小, 并列出所有文件路径。
    使用递归遍历路径中的文件夹和文件。
    """
    total_size = 0
    file_count = 0
    file_paths = set()
    folder_paths = set()

    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.add(file)
            file_count += 1
            total_size += os.path.getsize(file_path)

        # 添加子文件夹路径
        for dir in dirs:
            # folder_paths.add(os.path.join(root, dir))
            folder_paths.add(dir)

    return total_size, file_count, file_paths, folder_paths


def get_diff_files_and_folders(path1, path2):
    """
    获取两个路径下文件和子文件夹名称不同的部分。
    """
    size1, count1, files1, folders1 = get_size_and_files(path1)
    size2, count2, files2, folders2 = get_size_and_files(path2)

    # 获取文件差异
    diff_files1 = files1 - files2
    diff_files2 = files2 - files1

    # 获取子文件夹差异
    diff_folders1 = folders1 - folders2
    diff_folders2 = folders2 - folders1

    # 输出结果
    print(f"Path 1 ({path1}): ")
    print(f"  总文件数: {count1}, 总大小: {size1 / (1024 ** 3):.2f} GB")
    print(f"  不同的文件: {len(diff_files1)}")
    for file in diff_files1:
        print(f"    {file}")

    print(f"\nPath 2 ({path2}): ")
    print(f"  总文件数: {count2}, 总大小: {size2 / (1024 ** 3):.2f} GB")
    print(f"  不同的文件: {len(diff_files2)}")
    for file in diff_files2:
        print(f"    {file}")

    # 输出不同的文件夹
    print(f"\n不同的子文件夹: ")
    for folder in diff_folders1:
        print(f"  Path 1 独有: {folder}")
    for folder in diff_folders2:
        print(f"  Path 2 独有: {folder}")


if __name__ == "__main__":
    # 获取用户输入的两个路径
    path1 = input("请输入第一个文件夹路径 Path 1: ").strip()
    path2 = input("请输入第二个文件夹路径 Path 2: ").strip()

    # 调用函数处理
    get_diff_files_and_folders(path1, path2)
