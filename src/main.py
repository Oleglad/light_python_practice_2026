import os
import hashlib
from datetime import datetime
from collections import defaultdict

folder_path = input("Введите путь к папке: ").strip()
folder_path = folder_path.strip('"\'')

hash_to_paths = defaultdict(list)


def calculate_file_hash(file_path, chunk_size=8192):
    """Вычисляет SHA-256 хэш файла по частям"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (OSError, PermissionError, IOError) as e:
        print(f"Не удалось вычислить хэш для файла: {file_path} - {e}")
        return None


def scan_directory_recursive(current_path, folder_path, hash_to_paths, max_size_gb=1):
    """Рекурсивно сканирует папку и возвращает метаданные файлов"""
    files_metadata = []
    total_size = 0
    total_files = 0
    total_hashed = 0
    hash_errors = 0

    try:
        items = os.listdir(current_path)
    except (OSError, PermissionError) as e:
        print(f"Не удалось прочитать папку: {current_path} - {e}")
        return [], 0, 0, 0, 0

    for item in items:
        item_path = os.path.join(current_path, item)

        if os.path.isdir(item_path):
            sub_metadata, sub_size, sub_files, sub_hashed, sub_errors = scan_directory_recursive(
                item_path, folder_path, hash_to_paths, max_size_gb
            )
            files_metadata.extend(sub_metadata)
            total_size += sub_size
            total_files += sub_files
            total_hashed += sub_hashed
            hash_errors += sub_errors

        elif os.path.isfile(item_path):
            try:
                stat_info = os.stat(item_path)

                if stat_info.st_size > max_size_gb * 1024 * 1024 * 1024:
                    print(
                        f"Пропускаем хэширование большого файла: {item_path} ({stat_info.st_size / (1024 ** 3):.2f} ГБ)")
                    file_hash = "SKIPPED_LARGE_FILE"
                else:
                    file_hash = calculate_file_hash(item_path)
                    if file_hash:
                        hash_to_paths[file_hash].append(item_path)
                        total_hashed += 1
                    else:
                        hash_errors += 1
                        file_hash = "HASH_ERROR"

                rel_path = os.path.relpath(item_path, folder_path)

                metadata = {
                    'path': item_path,
                    'rel_path': rel_path,
                    'size': stat_info.st_size,
                    'size_mb': stat_info.st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(stat_info.st_mtime),
                    'created': datetime.fromtimestamp(stat_info.st_ctime),
                    'accessed': datetime.fromtimestamp(stat_info.st_atime),
                    'hash': file_hash
                }

                files_metadata.append(metadata)
                total_size += stat_info.st_size
                total_files += 1

            except (OSError, PermissionError) as e:
                print(f"Не удалось получить доступ к файлу: {item_path} - {e}")

    return files_metadata, total_size, total_files, total_hashed, hash_errors


def scan_folder(folder_path, hash_to_paths, max_size_gb=1):
    """Сканирует папку и возвращает метаданные файлов"""
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует!")
        return None, 0, 0, 0, 0

    print(f"Сканирую папку: {folder_path}")
    print("=" * 80)

    return scan_directory_recursive(folder_path, folder_path, hash_to_paths, max_size_gb)


def find_duplicates(hash_to_paths):
    """Находит дубликаты файлов"""
    duplicates = {
        hash_val: paths
        for hash_val, paths in hash_to_paths.items()
        if len(paths) > 1 and hash_val not in ["SKIPPED_LARGE_FILE", "HASH_ERROR"]
    }
    return duplicates


if os.path.exists(folder_path):
    print(f"Принимаю папку: {folder_path}")
    print("\n" + "=" * 80)

    files_metadata, total_size, total_files, total_hashed, hash_errors = scan_folder(
        folder_path, hash_to_paths
    )

    if files_metadata is None:
        print("Не удалось просканировать папку")
    else:
        print(f"\nСТАТИСТИКА:")
        print(f"Всего файлов: {total_files}")
        print(f"Общий размер: {total_size:,} байт ({total_size / (1024 * 1024):.2f} МБ)")
        if total_size > 1024 ** 3:
            print(f"Размер папки: {total_size / (1024 * 1024 * 1024):.2f} ГБ")
        print(f"Файлов с вычисленным хэшем: {total_hashed}")
        if hash_errors > 0:
            print(f"Ошибок при вычислении хэша: {hash_errors}")
        print("\n" + "=" * 80)

        duplicates = find_duplicates(hash_to_paths)

        if duplicates:
            print(f"\nНАЙДЕНЫ ДУБЛИКАТЫ ФАЙЛОВ:")
            print("-" * 80)
            for hash_val, paths in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
                try:
                    first_file_size = os.path.getsize(paths[0])
                    size_mb = first_file_size / (1024 * 1024)
                    print(f"\nХэш: {hash_val[:16]}... (размер: {size_mb:.2f} МБ)")
                    print(f"   Найдено {len(paths)} копий:")
                    for idx, path in enumerate(paths, 1):
                        print(f"      {idx}. {path}")
                except OSError:
                    print(f"\nХэш: {hash_val[:16]}... (размер: неизвестен)")
                    print(f"   Найдено {len(paths)} копий:")
                    for idx, path in enumerate(paths, 1):
                        print(f"      {idx}. {path}")
        else:
            print("\nДубликатов не найдено.")

        print(f"\nПОЛНЫЙ СПИСОК ФАЙЛОВ ({total_files} шт.):")
        print("-" * 80)

        for i, meta in enumerate(files_metadata, 1):
            print(f"\n{i}. {os.path.basename(meta['path'])}")
            print(f"   Путь: {meta['path']}")
            print(f"   Размер: {meta['size']:,} байт ({meta['size_mb']:.2f} МБ)")
            print(f"   Изменён: {meta['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Создан: {meta['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Открыт: {meta['accessed'].strftime('%Y-%m-%d %H:%M:%S')}")
            if meta['hash']:
                hash_display = meta['hash'][:16] + "..." if len(meta['hash']) > 16 else meta['hash']
                print(f"   Хэш (SHA-256): {hash_display}")
            print("-" * 40)

        print("\nГРУППИРОВКА ПО РАСШИРЕНИЯМ:")
        extensions = {}
        for meta in files_metadata:
            ext = os.path.splitext(meta['path'])[1].lower() or 'без расширения'
            extensions[ext] = extensions.get(ext, 0) + 1

        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext}: {count} файлов")

        save = input("\nСохранить отчёт в файл? (y/n): ").strip().lower()
        if save == 'y':
            report_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_name, 'w', encoding='utf-8') as f:
                f.write(f"Отчёт по папке: {folder_path}\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                if duplicates:
                    f.write("НАЙДЕНЫ ДУБЛИКАТЫ:\n")
                    f.write("-" * 40 + "\n")
                    for hash_val, paths in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
                        f.write(f"\nХэш: {hash_val}\n")
                        f.write(f"Найдено {len(paths)} копий:\n")
                        for idx, path in enumerate(paths, 1):
                            f.write(f"  {idx}. {path}\n")
                    f.write("\n" + "=" * 80 + "\n\n")

                for meta in files_metadata:
                    f.write(f"Файл: {os.path.basename(meta['path'])}\n")
                    f.write(f"Путь: {meta['path']}\n")
                    f.write(f"Размер: {meta['size']:,} байт\n")
                    f.write(f"Изменён: {meta['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    if meta['hash']:
                        f.write(f"Хэш (SHA-256): {meta['hash']}\n")
                    f.write("-" * 40 + "\n")
            print(f"Отчёт сохранён в файл: {report_name}")
else:
    print("Такой папки нет, попробуйте снова")
