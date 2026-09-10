import os
from datetime import datetime

folder_path = input("Введите путь к папке: ").strip()
folder_path = folder_path.strip('"\'')


def scan_directory_recursive(current_path, folder_path):
    """Рекурсивно сканирует папку и возвращает метаданные файлов"""
    files_metadata = []
    total_size = 0
    total_files = 0

    try:
        items = os.listdir(current_path)
    except (OSError, PermissionError) as e:
        print(f"Не удалось прочитать папку: {current_path} - {e}")
        return [], 0, 0

    for item in items:
        item_path = os.path.join(current_path, item)

        if os.path.isdir(item_path):
            sub_metadata, sub_size, sub_files = scan_directory_recursive(
                item_path, folder_path
            )
            files_metadata.extend(sub_metadata)
            total_size += sub_size
            total_files += sub_files

        elif os.path.isfile(item_path):
            try:
                stat_info = os.stat(item_path)

                rel_path = os.path.relpath(item_path, folder_path)

                metadata = {
                    'path': item_path,
                    'rel_path': rel_path,
                    'size': stat_info.st_size,
                    'size_mb': stat_info.st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(stat_info.st_mtime),
                    'created': datetime.fromtimestamp(stat_info.st_ctime),
                    'accessed': datetime.fromtimestamp(stat_info.st_atime),
                }

                files_metadata.append(metadata)
                total_size += stat_info.st_size
                total_files += 1

            except (OSError, PermissionError) as e:
                print(f"Не удалось получить доступ к файлу: {item_path} - {e}")

    return files_metadata, total_size, total_files


def scan_folder(folder_path):
    """Сканирует папку и возвращает метаданные файлов"""
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует!")
        return None, 0, 0

    print(f"Сканирую папку: {folder_path}")
    print("=" * 80)

    return scan_directory_recursive(folder_path, folder_path)


if os.path.exists(folder_path):
    print(f"Принимаю папку: {folder_path}")
    print("\n" + "=" * 80)

    files_metadata, total_size, total_files = scan_folder(folder_path)

    if files_metadata is None:
        print("Не удалось просканировать папку")
    else:
        print(f"\nСТАТИСТИКА:")
        print(f"Всего файлов: {total_files}")
        print(f"Общий размер: {total_size:,} байт ({total_size / (1024 * 1024):.2f} МБ)")
        if total_size > 1024 ** 3:
            print(f"Размер папки: {total_size / (1024 * 1024 * 1024):.2f} ГБ")
        print("\n" + "=" * 80)

        print(f"\nПОЛНЫЙ СПИСОК ФАЙЛОВ ({total_files} шт.):")
        print("-" * 80)

        for i, meta in enumerate(files_metadata, 1):
            print(f"\n{i}. {os.path.basename(meta['path'])}")
            print(f"   Путь: {meta['path']}")
            print(f"   Размер: {meta['size']:,} байт ({meta['size_mb']:.2f} МБ)")
            print(f"   Изменён: {meta['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Создан: {meta['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Открыт: {meta['accessed'].strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 40)
else:
    print("Такой папки нет, попробуйте снова")
