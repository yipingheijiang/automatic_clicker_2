import os
import sqlite3
import sys


def sqlitedb(db_name='命令集.db'):
    """建立与数据库的连接，返回游标
    :param db_name: 数据库名称
    :return: 游标，数据库连接"""
    try:
        # 取得当前文件目录
        con = sqlite3.connect(db_name)
        cursor = con.cursor()
        return cursor, con
    except sqlite3.Error:
        print("未连接到数据库！！请检查数据库路径是否异常。")
        sys.exit()


def close_database(cursor, conn):
    """关闭数据库
    :param cursor: 游标
    :param conn: 数据库连接"""
    cursor.close()
    conn.close()


def get_setting_data_from_db() -> tuple:
    """从数据库中获取设置参数
    :return: 设置参数"""
    cursor, conn = sqlitedb()
    cursor.execute('select * from 设置')
    list_setting_data = cursor.fetchall()
    close_database(cursor, conn)
    # 使用字典来存储设置参数
    setting_dict = {i[0]: i[1] for i in list_setting_data}
    return (setting_dict.get('持续时间'),
            setting_dict.get('时间间隔'),
            setting_dict.get('图像匹配精度'),
            setting_dict.get('暂停时间'))


# 全局参数的数据库操作
def global_write_to_database(resource_folder_path):
    """将全局参数写入数据库
    :param resource_folder_path: 资源文件夹路径"""
    # 连接数据库
    cursor, conn = sqlitedb()
    cursor.execute('INSERT INTO 全局参数(资源文件夹路径,分支表名) VALUES (?,?)',
                   (resource_folder_path, None))
    conn.commit()
    close_database(cursor, conn)


def extract_global_parameter(column_name: str) -> list:
    """从全局参数表中提取指定列的数据
    :param column_name: 列名（资源文件夹路径、分支表明）"""
    cursor, conn = sqlitedb()
    cursor.execute(f"select {column_name} from 全局参数")
    # 去除None并转换为列表
    result_list = [item[0] for item in cursor.fetchall() if item[0] is not None]
    close_database(cursor, conn)
    return result_list


def extract_excel_from_global_parameter():
    """从所有资源文件夹路径中提取所有的Excel文件
    :return: Excel文件列表"""
    # 从全局参数表中提取所有的资源文件夹路径
    resource_folder_path_list = extract_global_parameter('资源文件夹路径')
    excel_files = []
    for folder_path in resource_folder_path_list:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        excel_files.append(os.path.normpath(os.path.join(root, file)))
    return excel_files


def get_count_from_branch_name(branch_name: str) -> int:
    """获取分支表的数量
    :param branch_name: 分支表名
    :return: 目标分支表名中的指令数量"""
    # 连接数据库
    cursor, con = sqlitedb()
    # 获取表中数据记录的个数
    cursor.execute('SELECT count(*) FROM 命令 where 隶属分支=?', (branch_name,))
    count_record = cursor.fetchone()[0]
    # 关闭连接
    close_database(cursor, con)
    return count_record


if __name__ == '__main__':
    print(extract_excel_from_global_parameter())
