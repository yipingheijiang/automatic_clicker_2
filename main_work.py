# coding: utf-8
# Copyright (c) [2022] [federalsadler@sohu.com]
# [Clicker] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
# http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import datetime
import random
import re
import sqlite3
import subprocess
import sys
import threading
import time
import traceback

import keyboard
import mouse
import openpyxl
import pandas as pd
import pyautogui
import pyperclip
import selenium
import winsound
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

event = threading.Event()

COMMAND_TYPE_SIMULATE_CLICK = "模拟点击"
COMMAND_TYPE_CUSTOM = "自定义"


def exit_main_work():
    sys.exit()


class MainWork:
    """主要工作类"""

    def __init__(self, main_window, navigation):
        # 终止和暂停标志
        self.start_state = True
        self.suspended = False
        # 主窗体
        self.main_window = main_window
        # 导航窗体
        self.navigation = navigation
        # 网页操作类
        self.web_option = WebOption(self.main_window, self.navigation)
        # 读取配置文件
        self.settings = SettingsData()
        self.settings.init()
        # 在窗体中显示循环次数
        self.number = 1
        # 全部指令的循环次数，无限循环为标志
        self.infinite_cycle = self.main_window.radioButton.isChecked()
        self.number_cycles = self.main_window.spinBox.value()
        # 从数据库中读取全局参数
        self.image_folder_path, self.excel_folder_path, \
            self.branch_table_name, self.extenders = self.extracted_data_global_parameter()

    @staticmethod
    def sqlitedb():
        """建立与数据库的连接，返回游标"""
        try:
            # 取得当前文件目录
            con = sqlite3.connect('命令集.db')
            cursor = con.cursor()
            # self.main_window_.plainTextEdit.appendPlainText('成功连接数据库！')
            print('成功连接数据库！')
            return cursor, con
        except sqlite3.Error:
            x = input("未连接到数据库！！请检查数据库路径是否异常。")
            print(x)
            sys.exit()

    def reset_loop_count_and_infinite_loop_judgment(self):
        """重置循环次数和无限循环标志"""
        self.number = 1
        self.infinite_cycle = self.main_window.radioButton.isChecked()
        self.number_cycles = self.main_window.spinBox.value()

    @staticmethod
    def close_database(cursor, conn):
        """关闭数据库"""
        cursor.close()
        conn.close()

    def test(self):
        print('test')
        all_list_instructions = self.extracted_data_all_list()
        print(all_list_instructions)
        print(len(all_list_instructions))

    def extracted_data_all_list(self, only_current_instructions=False):
        """提取指令集中的数据,返回主表和分支表的汇总数据"""
        all_list_instructions = []
        # 从主表中提取数据
        cursor, conn = self.sqlitedb()
        # 从分支表中提取数据
        try:
            if not only_current_instructions:
                if len(self.branch_table_name) != 0:
                    for i in self.branch_table_name:
                        cursor.execute("select * from 命令 where 隶属分支 = ?", (i,))
                        branch_list_instructions = cursor.fetchall()
                        all_list_instructions.append(branch_list_instructions)
            if only_current_instructions:
                cursor.execute("select * from 命令 where 隶属分支 = ?", (self.main_window.comboBox.currentText(),))
                branch_list_instructions = cursor.fetchall()
                all_list_instructions.append(branch_list_instructions)
            self.close_database(cursor, conn)
            return all_list_instructions
        except sqlite3.OperationalError:
            QMessageBox.critical(self.main_window, "警告", "找不到分支！请检查分支表名是否正确！", QMessageBox.Yes)

    # 编写一个函数用于去除列表中的none

    def extracted_data_global_parameter(self):
        """从全局参数表中提取数据"""

        def remove_none(list_):
            """去除列表中的none"""
            list_x = []
            for i in list_:
                if i[0] is not None:
                    list_x.append(i[0].replace('"', ''))
            return list_x

        cursor, conn = self.sqlitedb()
        cursor.execute("select 图像文件夹路径 from 全局参数")
        image_folder_path = remove_none(cursor.fetchall())
        cursor.execute("select 工作簿路径 from 全局参数")
        excel_folder_path = remove_none(cursor.fetchall())
        cursor.execute("select 分支表名 from 全局参数")
        branch_table_name = remove_none(cursor.fetchall())
        cursor.execute("select 扩展程序 from 全局参数")
        extenders = remove_none(cursor.fetchall())
        self.close_database(cursor, conn)
        print("全局参数读取成功！")
        return image_folder_path, excel_folder_path, branch_table_name, extenders

    def start_work(self, only_current_instructions=False):
        """主要工作"""
        self.start_state = True
        self.suspended = False
        # 打印循环次数
        self.reset_loop_count_and_infinite_loop_judgment()
        # 读取数据库中的数据
        list_instructions = self.extracted_data_all_list(only_current_instructions)
        # 开始执行主要操作
        try:
            if len(list_instructions) != 0:
                keyboard.hook(self.abc)
                # # 如果状态为True执行无限循环
                if self.infinite_cycle:
                    self.number = 1
                    while self.start_state:
                        self.execute_instructions(0, 0, list_instructions)
                        if not self.start_state:
                            self.main_window.plainTextEdit.appendPlainText('结束任务')
                            break
                        if self.suspended:
                            event.clear()
                            event.wait(86400)
                        self.number += 1
                        time.sleep(self.settings.time_sleep)
                # 如果状态为有限次循环
                elif not self.infinite_cycle and self.number_cycles > 0:
                    self.number = 1
                    repeat_number = self.number_cycles
                    while self.number <= repeat_number and self.start_state:
                        self.execute_instructions(0, 0, list_instructions)
                        if not self.start_state:
                            self.main_window.plainTextEdit.appendPlainText('结束任务')
                            break
                        if self.suspended:
                            event.clear()
                            event.wait(86400)
                        # print('第', self.number, '次循环')
                        self.main_window.plainTextEdit.appendPlainText('完成第' + str(self.number) + '次循环')
                        self.number += 1
                        time.sleep(self.settings.time_sleep)
                    self.main_window.plainTextEdit.appendPlainText('结束任务')
                elif not self.infinite_cycle and self.number_cycles <= 0:
                    print("请设置执行循环次数！")
        finally:
            self.web_option.close_browser()

    def execute_instructions(self, current_list_index, current_index, list_instructions):
        """执行接受到的操作指令"""
        # 读取指令
        while current_index < len(list_instructions[current_list_index]):
            try:
                elem = list_instructions[current_list_index][current_index]
                # print(elem)
                # 【指令集合【指令分支（指令元素[元素索引]）】】
                # print('执行当前指令：', elem)
                dic = {
                    'ID': elem[0],
                    '图像路径': elem[1],
                    '指令类型': elem[2],
                    '参数1（键鼠指令）': elem[3],
                    '参数2': elem[4],
                    '参数3': elem[5],
                    '参数4': elem[6],
                    '重复次数': elem[7],
                    '异常处理': elem[8]
                }
                # 读取指令类型
                cmd_type = dict(dic)['指令类型']
                re_try = dict(dic)['重复次数']
                exception_handling = dict(dic)['异常处理']
                # 设置一个容器，用于存储参数
                list_ins = []
                try:
                    # 图像识别点击的事件
                    if cmd_type == "图像点击":
                        # 读取图像名称
                        img = dict(dic)['图像路径']
                        # 取重复次数
                        re_try = dict(dic)['重复次数']
                        # 是否跳过参数
                        skip = dict(dic)['参数2']
                        if dict(dic)['参数1（键鼠指令）'] == '左键单击':
                            list_ins = [1, 'left', img, skip]
                        elif dict(dic)['参数1（键鼠指令）'] == '左键双击':
                            list_ins = [2, 'left', img, skip]
                        elif dict(dic)['参数1（键鼠指令）'] == '右键单击':
                            list_ins = [1, 'right', img, skip]
                        elif dict(dic)['参数1（键鼠指令）'] == '右键双击':
                            list_ins = [2, 'right', img, skip]
                        # 执行鼠标点击事件
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 屏幕坐标点击事件
                    elif cmd_type == '坐标点击':
                        # 取x,y坐标的值
                        x = int(dict(dic)['参数2'].split('-')[0])
                        y = int(dict(dic)['参数2'].split('-')[1])
                        z = int(dict(dic)['参数2'].split('-')[1])
                        self.main_window.plainTextEdit.appendPlainText('x,y坐标：' + str(x) + ',' + str(y))
                        # print('x,y坐标：', x, y)
                        # 调用鼠标点击事件（点击次数，按钮类型，图像名称）
                        if dict(dic)['参数1（键鼠指令）'] == '左键单击':
                            list_ins = [1, 'left', x, y]
                        elif dict(dic)['参数1（键鼠指令）'] == '左键双击':
                            list_ins = [2, 'left', x, y]
                        elif dict(dic)['参数1（键鼠指令）'] == '右键单击':
                            list_ins = [1, 'right', x, y]
                        elif dict(dic)['参数1（键鼠指令）'] == '右键双击':
                            list_ins = [2, 'right', x, y]
                        elif dict(dic)['参数1（键鼠指令）'] == '左键（自定义次数）':
                            list_ins = [z, 'left', x, y]
                        # 执行鼠标点击事件
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 等待的事件
                    elif cmd_type == '等待':
                        wait_type = dict(dic)['参数1（键鼠指令）']
                        if wait_type == '等待':
                            wait_time = dict(dic)['参数2']
                            self.main_window.plainTextEdit.appendPlainText('等待时长' + str(wait_time) + '秒')
                            QApplication.processEvents()
                            self.stop_time(int(wait_time))
                        elif wait_type == '等待到指定时间':
                            target_time = dict(dic)['参数2'].split('+')[0].replace('-', '/')
                            interval_time = dict(dic)['参数2'].split('+')[1]
                            now_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                            # 将now_time转换为时间格式
                            now_time = datetime.datetime.strptime(now_time, '%Y/%m/%d %H:%M:%S')
                            # 将target_time转换为时间格式
                            t_time = datetime.datetime.strptime(target_time, '%Y/%m/%d %H:%M:%S')
                            if t_time > now_time:
                                year_target = int(t_time.strftime('%Y'))
                                month_target = int(t_time.strftime('%m'))
                                day_target = int(t_time.strftime('%d'))
                                hour_target = int(t_time.strftime('%H'))
                                minute_target = int(t_time.strftime('%M'))
                                second_target = int(t_time.strftime('%S'))
                                self.check_time(year_target, month_target, day_target,
                                                hour_target, minute_target, second_target, interval_time)
                        elif wait_type == '等待到指定图片':
                            wait_img = dict(dic)['图像路径']
                            wait_instruction_type = dict(dic)['参数2']
                            timeout_period = dict(dic)['参数3']
                            self.wait_to_the_specified_image(wait_img, wait_instruction_type, timeout_period)

                    # 滚轮滑动的事件
                    elif cmd_type == '滚轮滑动':
                        scroll_direction = dict(dic)['参数1（键鼠指令）']
                        scroll_distance = int(dict(dic)['参数2'])
                        if scroll_direction == '↑':
                            scroll_distance = scroll_distance
                        elif scroll_direction == '↓':
                            scroll_distance = -scroll_distance
                        list_ins = [scroll_direction, scroll_distance]
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 文本输入的事件
                    elif cmd_type == '文本输入':
                        input_value = str(dict(dic)['参数1（键鼠指令）'])
                        special_control_judgment = dict(dic)['参数2']
                        list_ins = [input_value, special_control_judgment]
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 鼠标移动的事件
                    elif cmd_type == '鼠标移动':
                        try:
                            direction = dict(dic)['参数1（键鼠指令）']
                            distance = dict(dic)['参数2']
                            list_ins = [direction, distance]
                            self.execution_repeats(cmd_type, list_ins, re_try)
                        except IndexError:
                            print('鼠标移动参数格式错误！')

                    # 键盘按键的事件
                    elif cmd_type == '按下键盘':
                        key = dict(dic)['参数1（键鼠指令）']
                        list_ins = [key]
                        self.execution_repeats(cmd_type, list_ins, re_try)
                    # 中键激活的事件
                    elif cmd_type == '中键激活':
                        command_type = dict(dic)['参数1（键鼠指令）']
                        click_count = dict(dic)['参数2']
                        list_ins = [command_type, click_count]
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 鼠标事件
                    elif cmd_type == '鼠标事件':
                        if dict(dic)['参数1（键鼠指令）'] == '左键单击':
                            list_ins = [1, 'left']
                        elif dict(dic)['参数1（键鼠指令）'] == '左键双击':
                            list_ins = [2, 'left']
                        elif dict(dic)['参数1（键鼠指令）'] == '右键单击':
                            list_ins = [1, 'right']
                        elif dict(dic)['参数1（键鼠指令）'] == '右键双击':
                            list_ins = [2, 'right']
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 图片信息录取
                    elif cmd_type == 'excel信息录入':
                        excel_path = dict(dic)['参数1（键鼠指令）'].split('-')[0]
                        sheet_name = dict(dic)['参数1（键鼠指令）'].split('-')[1]
                        img = dict(dic)['图像路径']
                        cell_position = dict(dic)['参数2']
                        line_number_increment = dict(dic)['参数3'].split('-')[0]
                        special_control_input = dict(dic)['参数3'].split('-')[1]
                        time_out_error = dict(dic)['参数4']
                        exception_type = dict(dic)['异常处理']
                        list_dic = {
                            '点击次数': 3,
                            '按钮类型': 'left',
                            '工作簿路径': excel_path,
                            '工作表名称': sheet_name,
                            '图像路径': img,
                            '单元格位置': cell_position,
                            '行号递增': line_number_increment,
                            '特殊控件输入': special_control_input,
                            '超时报错': time_out_error,
                            '异常处理': exception_type
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 网页操作
                    elif cmd_type == '网页操作':
                        url = dict(dic)['图像路径']  # 网址
                        element_type = dict(dic)['参数1（键鼠指令）']  # 元素类型
                        element_value = dict(dic)['参数2']  # 元素值
                        operation_type = dict(dic)['参数3'].split('-')[0]  # 操作类型
                        text_input = dict(dic)['参数3'].split('-')[1]  # 文本内容
                        timeout_type = dict(dic)['参数4']  # 超时类型
                        list_dic = {
                            '网址': url,
                            '元素类型': element_type,
                            '元素值': element_value,
                            '操作类型': operation_type,
                            '文本内容': text_input,
                            '超时类型': timeout_type
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 网页录入
                    elif cmd_type == '网页录入':
                        excel_path = dict(dic)['参数1（键鼠指令）'].split('-')[0]
                        sheet_name = dict(dic)['参数1（键鼠指令）'].split('-')[1]
                        element_type = dict(dic)['图像路径'].split('-')[0]
                        element_value = dict(dic)['图像路径'].split('-')[1]
                        cell_position = dict(dic)['参数2']
                        line_number_increment = dict(dic)['参数3']
                        timeout_type = dict(dic)['参数4']
                        list_dic = {
                            '工作簿路径': excel_path,
                            '工作表名称': sheet_name,
                            '元素类型': element_type,
                            '元素值': element_value,
                            '单元格位置': cell_position,
                            '行号递增': line_number_increment,
                            '超时类型': timeout_type
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 鼠标拖拽
                    elif cmd_type == '鼠标拖拽':
                        x_start = int(dict(dic)['参数1（键鼠指令）'].split(',')[0])
                        y_start = int(dict(dic)['参数1（键鼠指令）'].split(',')[1])
                        x_end = int(dict(dic)['参数2'].split(',')[0])
                        y_end = int(dict(dic)['参数2'].split(',')[1])
                        start_position = (x_start, y_start)
                        end_position = (x_end, y_end)
                        list_ins = [start_position, end_position]
                        self.execution_repeats(cmd_type, list_ins, re_try)

                    # 切换frame
                    elif cmd_type == '切换frame':
                        switch_type = dict(dic)['参数1（键鼠指令）']
                        frame_type = dict(dic)['参数2']
                        frame_value = dict(dic)['参数3']
                        list_dic = {
                            '切换类型': switch_type,
                            'frame类型': frame_type,
                            'frame值': frame_value
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 切换窗口
                    elif cmd_type == '切换窗口':
                        switch_type = dict(dic)['参数1（键鼠指令）']
                        window_value = dict(dic)['参数2']
                        list_dic = {
                            '切换类型': switch_type,
                            '窗口值': window_value
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 读取网页数据到excel
                    elif cmd_type == '读取网页数据到Excel表格':
                        element_type = dict(dic)['图像路径'].split('-')[0]
                        element_value = dict(dic)['图像路径'].split('-')[1]
                        excel_path = dict(dic)['参数1（键鼠指令）'].split('-')[0]
                        sheet_name = dict(dic)['参数1（键鼠指令）'].split('-')[1]
                        timeout_type = dict(dic)['参数2']
                        list_dic = {
                            '元素类型': element_type,
                            '元素值': element_value,
                            '工作簿路径': excel_path,
                            '工作表名称': sheet_name,
                            '超时类型': timeout_type
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 拖动网页元素
                    elif cmd_type == '拖动元素':
                        element_type = dict(dic)['图像路径'].split('-')[0]
                        element_value = dict(dic)['图像路径'].split('-')[1]
                        x = int(dict(dic)['参数1（键鼠指令）'].split('-')[0])
                        y = int(dict(dic)['参数1（键鼠指令）'].split('-')[1])
                        timeout_type = dict(dic)['参数2']
                        list_dic = {
                            '元素类型': element_type,
                            '元素值': element_value,
                            'x': x,
                            'y': y,
                            '超时类型': timeout_type
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    # 全屏截图
                    elif cmd_type == '全屏截图':
                        image_path = dict(dic)['图像路径']
                        list_dic = {
                            '图像路径': image_path
                        }
                        self.execution_repeats(cmd_type, list_dic, re_try)

                    current_index += 1
                except Exception as e:
                    # 打印错误堆栈信息
                    # traceback.print_exc()
                    print(e)
                    # 跳转分支的指定指令
                    print('分支指令:' + exception_handling)
                    if exception_handling == '自动跳过':
                        current_index += 1
                    elif exception_handling == '抛出异常并暂停':
                        winsound.Beep(1000, 1000)
                        # 弹出提示框
                        reply = QMessageBox.question(self.main_window, '提示',
                                                     'ID为{}的指令抛出异常！\n是否继续执行？'.format(dict(dic)['ID']),
                                                     QMessageBox.Yes | QMessageBox.No,
                                                     QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            current_index += 1
                        else:
                            self.start_state = False
                            current_index += 1
                            break
                    elif exception_handling == '抛出异常并停止':
                        winsound.Beep(1000, 1000)
                        # 弹出提示框
                        QMessageBox.warning(self.main_window, '提示',
                                            'ID为{}的指令抛出异常！\n已停止执行！'.format(dict(dic)['ID']))
                        current_index += 1
                        self.start_state = False
                        break
                    elif exception_handling.endswith('.py') or exception_handling.endswith('.exe'):
                        self.start_state = False
                        self.main_window.plainTextEdit.appendPlainText('执行扩展程序')
                        if '.exe' in exception_handling:
                            subprocess.run('calc.exe')
                        elif '.py' in exception_handling:
                            subprocess.run('python {}'.format(exception_handling))
                        break
                    elif '分支' in exception_handling:  # 跳转分支
                        self.main_window.plainTextEdit.appendPlainText('转到分支')
                        branch_name_index = exception_handling.split('-')[1]
                        branch_index = exception_handling.split('-')[2]
                        x = int(branch_name_index)
                        y = int(branch_index)
                        print('x:', x, 'y:', y)
                        self.execute_instructions(x, y, list_instructions)
                        break
            except IndexError:
                self.main_window.plainTextEdit.appendPlainText('分支执行异常！')
                QMessageBox.warning(self.main_window, '提示', '分支执行异常！')
                exit_main_work()

    def execution_repeats(self, cmd_type, list_ins, reTry):
        """执行重复次数"""

        def determine_execution_type(cmd_type_, list_ins_):
            """执行判断命令类型并调用对应函数"""
            # 图像点击的操作事件
            if cmd_type_ == '图像点击':
                click_times = list_ins_[0]
                lOrR = list_ins_[1]
                img = list_ins_[2]
                skip = list_ins_[3]
                self.execute_click(click_times, lOrR, img, skip)
            elif cmd_type_ == '坐标点击':
                x = list_ins_[2]
                y = list_ins_[3]
                click_times = list_ins_[0]
                lOrR = list_ins_[1]
                pyautogui.click(x, y, click_times, interval=self.settings.interval, duration=self.settings.duration,
                                button=lOrR)
                # print('执行坐标%s:%s点击' % (x, y) + str(self.number))
                self.main_window.plainTextEdit.appendPlainText('执行坐标%s:%s点击' % (x, y) + str(self.number))
            elif cmd_type_ == '鼠标移动':
                direction = list_ins_[0]
                distance = list_ins_[1]
                self.mouse_moves(direction, distance)
            elif cmd_type_ == '滚轮滑动':
                scroll_distance = list_ins_[1]
                scroll_direction = list_ins_[0]
                self.wheel_slip(scroll_direction, scroll_distance)
            elif cmd_type_ == '文本输入':
                input_value = list_ins_[0]
                special_control_judgment = list_ins_[1]
                self.text_input(input_value, special_control_judgment)
            elif cmd_type_ == '按下键盘':
                # 获取键盘按键
                keys = list_ins_[0].split('+')
                # 按下键盘
                if len(keys) == 1:
                    pyautogui.press(keys[0])  # 如果只有一个键,直接按下
                else:
                    # 否则,组合多个键为热键
                    hotkey = '+'.join(keys)
                    pyautogui.hotkey(hotkey)
                time.sleep(self.settings.time_sleep)
                self.main_window.plainTextEdit.appendPlainText('已经按下按键' + list_ins_[0])
                # print('已经按下按键' + list_ins_[0])
            elif cmd_type_ == '中键激活':
                command_type = list_ins_[0]
                click_count = list_ins_[1]
                self.middle_mouse_button(command_type, click_count)
            elif cmd_type_ == '鼠标事件':
                click_times = list_ins_[0]
                lOrR = list_ins_[1]
                position = pyautogui.position()
                pyautogui.click(position[0], position[1], click_times, interval=self.settings.interval,
                                duration=self.settings.duration,
                                button=lOrR)
                self.main_window.plainTextEdit.appendPlainText('执行鼠标事件')
                # print('执行鼠标事件')
            elif cmd_type_ == 'excel信息录入':
                excel_path = dict(list_ins_)['工作簿路径']
                sheet_name = dict(list_ins_)['工作表名称']
                cell_position = dict(list_ins_)['单元格位置']
                click_times = dict(list_ins_)['点击次数']
                lOrR = dict(list_ins_)['按钮类型']
                img = dict(list_ins_)['图像路径']
                line_number_increment = dict(list_ins_)['行号递增']
                special_control_input = dict(list_ins_)['特殊控件输入']
                time_out_error = dict(list_ins_)['超时报错']
                # 获取excel表格中的值
                cell_value = self.extra_excel_cell_value(excel_path, sheet_name, cell_position, line_number_increment)
                self.execute_click(click_times, lOrR, img, time_out_error)
                self.text_input(cell_value, special_control_input)
                self.main_window.plainTextEdit.appendPlainText('已执行信息录入')
                # print('已执行信息录入')
            elif cmd_type_ == '网页操作':
                url = dict(list_ins_)['网址']
                element_type = dict(list_ins_)['元素类型']
                element_value = dict(list_ins_)['元素值']
                operation_type = dict(list_ins_)['操作类型']
                text_input = dict(list_ins_)['文本内容']
                timeout_type = dict(list_ins_)['超时类型']
                # 执行网页操作
                self.web_option.text = text_input
                self.web_option.single_shot_operation(url=url,
                                                      action=operation_type,
                                                      element_value_=element_value,
                                                      element_type_=element_type,
                                                      timeout_type_=timeout_type)
            elif cmd_type_ == '网页录入':
                excel_path = dict(list_ins_)['工作簿路径']
                sheet_name = dict(list_ins_)['工作表名称']
                cell_position = dict(list_ins_)['单元格位置']
                element_type = dict(list_ins_)['元素类型']
                element_value = dict(list_ins_)['元素值']
                timeout_type = dict(list_ins_)['超时类型']
                line_number_increment = dict(list_ins_)['行号递增']
                # 获取excel表格中的值
                cell_value = self.extra_excel_cell_value(excel_path, sheet_name, cell_position, line_number_increment)
                # 执行网页操作
                self.web_option.text = cell_value
                self.web_option.single_shot_operation(url='',
                                                      action='输入内容',
                                                      element_value_=element_value,
                                                      element_type_=element_type,
                                                      timeout_type_=timeout_type)

            elif cmd_type_ == '鼠标拖拽':
                start_position = list_ins_[0]
                end_position = list_ins_[1]
                # 执行鼠标拖拽
                self.mouse_drag(start_position, end_position)

            elif cmd_type_ == '切换frame':
                switch_type = dict(list_ins_)['切换类型']
                element_type = dict(list_ins_)['frame类型']
                element_value = dict(list_ins_)['frame值']
                # 执行切换frame
                self.web_option.switch_to_frame(switch_type=switch_type,
                                                iframe_type=element_type,
                                                iframe_value=element_value)

            elif cmd_type_ == '切换窗口':
                switch_type = dict(list_ins_)['切换类型']
                window_value = dict(list_ins_)['窗口值']
                # 执行切换窗口
                self.web_option.switch_to_window(window_type=switch_type,
                                                 window_value=window_value)

            elif cmd_type_ == '读取网页数据到Excel表格':
                element_type = dict(list_ins_)['元素类型']
                element_value = dict(list_ins_)['元素值']
                excel_path = dict(list_ins_)['工作簿路径']
                sheet_name = dict(list_ins_)['工作表名称']
                timeout_type = dict(list_ins_)['超时类型']
                # 执行读取网页数据到Excel表格
                self.web_option.excel_path = excel_path
                self.web_option.sheet_name = sheet_name
                self.web_option.single_shot_operation(url='',
                                                      action='读取网页表格',
                                                      element_value_=element_value,
                                                      element_type_=element_type,
                                                      timeout_type_=timeout_type)

            elif cmd_type_ == '拖动元素':
                element_type = dict(list_ins_)['元素类型']
                element_value = dict(list_ins_)['元素值']
                self.web_option.distance_x = int(dict(list_ins_)['x'])
                self.web_option.distance_y = int(dict(list_ins_)['y'])
                timeout_type = dict(list_ins_)['超时类型']
                # 执行拖动元素
                self.web_option.single_shot_operation(url='',
                                                      action='拖动元素',
                                                      element_value_=element_value,
                                                      element_type_=element_type,
                                                      timeout_type_=timeout_type)

            elif cmd_type_ == '全屏截图':
                image_path = dict(list_ins_)['图像路径']
                # 如果image_path，没有后缀名，则添加后缀名
                if '.' not in image_path:
                    image_path = image_path + '.png'
                # 执行截图
                screenshot = pyautogui.screenshot()
                # 将图片保存到指定文件夹
                screenshot.save(image_path)
                self.main_window.plainTextEdit.appendPlainText('已执行全屏截图')
                
            QApplication.processEvents()

        if reTry == 1:
            # 参数：图片和查找精度，返回目标图像在屏幕的位置
            determine_execution_type(cmd_type, list_ins)
        elif reTry > 1:
            # 有限次重复
            i = 1
            while i < reTry + 1:
                determine_execution_type(cmd_type, list_ins)
                i += 1
                time.sleep(self.settings.time_sleep)
        else:
            pass

    def extra_excel_cell_value(self, excel_path, sheet_name, cell_position, line_number_increment):
        """获取excel表格中的值"""
        print('正在获取单元格值')
        cell_value = None
        # print('line_number_increment:', line_number_increment)
        try:
            # 打开excel表格
            wb = openpyxl.load_workbook(excel_path)
            # 选择表格
            sheet = wb[str(sheet_name)]
            if line_number_increment == 'False':
                # 获取单元格的值
                cell_value = sheet[cell_position].value
                self.main_window.plainTextEdit.appendPlainText('获取到的单元格值为：' + str(cell_value))
            elif line_number_increment == 'True':
                # 获取行号递增的单元格的值
                column_number = re.findall(r"[a-zA-Z]+", cell_position)[0]
                line_number = int(re.findall(r"\d+\.?\d*", cell_position)[0]) + self.number - 1
                new_cell_position = column_number + str(line_number)
                cell_value = sheet[new_cell_position].value
                self.main_window.plainTextEdit.appendPlainText('获取到的单元格值为：' + str(cell_value))
            return cell_value
        except FileNotFoundError:
            x = input('没有找到工作簿')
            print(x)
            exit_main_work()
        except KeyError:
            x = input('没有找到表格')
            print(x)
            exit_main_work()
        except AttributeError:
            x = input('单元格格式错误')
            print(x)
            exit_main_work()

    def check_time(self, year_target, month_target, day_target, hour_target,
                   minute_target, second_target, interval):
        """检查时间，指定时间则执行操作
        :param year_target: 目标年份
        :param month_target: 目标月份
        :param day_target: 目标日期
        :param hour_target: 目标小时
        :param minute_target: 目标分钟
        :param second_target: 目标秒钟
        :param interval: 时间间隔"""
        show_times = 1
        sleep_time = int(interval) / 1000
        while True:
            now = time.localtime()
            if show_times == 1:
                self.main_window.plainTextEdit.appendPlainText(
                    "当前时间为：%s/%s/%s %s:%s:%s" % (
                        now.tm_year, now.tm_mon, now.tm_mday,
                        now.tm_hour, now.tm_min, now.tm_sec))
                QApplication.processEvents()
                print("当前时间为：%s/%s/%s %s:%s:%s" % (now.tm_year, now.tm_mon,
                                                        now.tm_mday, now.tm_hour,
                                                        now.tm_min, now.tm_sec))
                show_times = sleep_time
            if now.tm_year == year_target and now.tm_mon == month_target and \
                    now.tm_mday == day_target and now.tm_hour == hour_target and \
                    now.tm_min == minute_target and now.tm_sec == second_target:
                self.main_window.plainTextEdit.appendPlainText("退出等待")
                print("退出等待")
                break
            # 时间暂停
            time.sleep(sleep_time)
            show_times += sleep_time

    def wait_to_the_specified_image(self, image, wait_instruction_type, timeout_period):
        """执行图片等待"""
        repeat = True
        stat_time = time.time()

        def event_in_waiting(text, start_time, timeout_period_):
            """等待中的事件"""
            difference_time = int(time.time() - start_time)
            if difference_time > int(timeout_period_):
                self.main_window.plainTextEdit.appendPlainText('等待超时，已等待' + str(difference_time) + '秒')
                raise pyautogui.ImageNotFoundException
            self.main_window.plainTextEdit.appendPlainText(
                '等待至图像' + text + ',已等待' + str(difference_time) + '秒')
            QApplication.processEvents()

        while repeat and self.start_state:
            location = pyautogui.locateCenterOnScreen(image, confidence=self.settings.confidence)
            if wait_instruction_type == '等待到指定图像出现':
                if location is not None:
                    self.main_window.plainTextEdit.appendPlainText('目标图像已经出现，等待结束')
                    QApplication.processEvents()
                    repeat = False
                else:
                    event_in_waiting('出现', stat_time, timeout_period)
            elif wait_instruction_type == '等待到指定图像消失':
                if location is None:
                    self.main_window.plainTextEdit.appendPlainText('目标图像已经消失，等待结束')
                    QApplication.processEvents()
                    repeat = False
                else:
                    event_in_waiting('消失', stat_time, timeout_period)
            time.sleep(0.1)

    def middle_mouse_button(self, command_type, click_times):
        """中键点击事件"""
        self.main_window.plainTextEdit.appendPlainText('等待按下鼠标中键中...按下esc键退出')
        QApplication.processEvents()
        # print('等待按下鼠标中键中...按下esc键退出')
        # 如果按下esc键则退出
        mouse.wait(button='middle')
        try:
            if command_type == COMMAND_TYPE_SIMULATE_CLICK:
                # print('执行鼠标点击'+click_times+'次')
                pyautogui.click(clicks=int(click_times), button='left')
                self.main_window.plainTextEdit.appendPlainText('执行鼠标点击' + click_times + '次')
                # print('执行鼠标点击' + click_times + '次')
            elif command_type == COMMAND_TYPE_CUSTOM:
                pass
        except OSError:
            # 弹出提示框。提示检查鼠标是否连接
            self.main_window.plainTextEdit.appendPlainText('连接失败，请检查鼠标是否连接正确。')
            # print('连接失败，请检查鼠标是否连接正确。')
            pass

    def execute_click(self, click_times, lOrR, img, skip):
        """执行鼠标点击事件"""

        # 4个参数：鼠标点击时间，按钮类型（左键右键中键），图片名称，重复次数
        repeat = True
        number_1 = 1

        def image_match_click(skip_, start_time_=None):
            nonlocal repeat, number_1
            if location is not None:
                # 参数：位置X，位置Y，点击次数，时间间隔，持续时间，按键
                self.main_window.plainTextEdit.appendPlainText('找到匹配图片' + str(self.number))
                pyautogui.click(location.x, location.y,
                                clicks=click_times, interval=self.settings.interval, duration=self.settings.duration,
                                button=lOrR)
                # self.real_time_display_status()
                repeat = False
            else:
                if skip_ != "自动略过":
                    # 计算如果时间差的秒数大于skip则退出
                    # 获取当前时间，计算时间差
                    end_time = time.time()
                    time_difference = end_time - start_time_
                    # 显示剩余等待时间
                    self.main_window.plainTextEdit.appendPlainText(
                        '未找到匹配图片' + str(self.number) + '正在重试第' + str(number_1) + '次')
                    self.main_window.plainTextEdit.appendPlainText(
                        '剩余等待' + str(round(int(skip_) - time_difference, 0)) + '秒')
                    number_1 += 1
                    QApplication.processEvents()
                    # 终止条件
                    if time_difference > int(skip_):
                        repeat = False
                        raise pyautogui.ImageNotFoundException
                    time.sleep(0.1)
                elif skip_ == "自动略过":
                    self.main_window.plainTextEdit.appendPlainText('未找到匹配图片' + str(self.number))
                # self.real_time_display_status()

        try:
            # 获取当前时间
            start_time = time.time()
            if skip == "自动略过":
                location = pyautogui.locateCenterOnScreen(img, confidence=self.settings.confidence)
                image_match_click(skip)
            else:
                while self.start_state and repeat:
                    location = pyautogui.locateCenterOnScreen(img, confidence=self.settings.confidence)
                    image_match_click(skip, start_time)
        except OSError:
            QMessageBox.critical(self.main_window, '错误', '文件下未找到.png图像文件，请检查文件是否存在！')

    def mouse_moves(self, direction, distance):
        """鼠标移动事件"""
        # 显示鼠标当前位置
        x, y = pyautogui.position()
        print('x:' + str(x) + ',y:' + str(y))
        # 相对于当前位置移动鼠标
        if direction == '↑':
            pyautogui.moveRel(0, -abs(int(distance)), duration=self.settings.duration)
        elif direction == '↓':
            pyautogui.moveRel(0, int(distance), duration=self.settings.duration)
        elif direction == '←':
            pyautogui.moveRel(-abs(int(distance)), 0, duration=self.settings.duration)
        elif direction == '→':
            pyautogui.moveRel(int(distance), 0, duration=self.settings.duration)
        self.main_window.plainTextEdit.appendPlainText('移动鼠标' + direction + distance + '像素距离')

    def wheel_slip(self, scroll_direction, scroll_distance):
        """滚轮滑动事件"""
        pyautogui.scroll(scroll_distance)
        self.main_window.plainTextEdit.appendPlainText(
            '滚轮滑动' + str(scroll_direction) + str(abs(scroll_distance)) + '距离')

    def mouse_drag(self, start_position, end_position):
        """鼠标拖拽事件"""
        pyautogui.moveTo(start_position[0], start_position[1], duration=0.3)
        pyautogui.dragTo(end_position[0], end_position[1], duration=0.3)
        self.main_window.plainTextEdit.appendPlainText('鼠标拖拽' + str(start_position) + '到' + str(end_position))

    def text_input(self, input_value, special_control_judgment):
        """文本输入事件"""
        print('special_control_judgment:' + str(special_control_judgment))
        print(type(special_control_judgment))
        if special_control_judgment == 'False':
            pyperclip.copy(input_value)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.settings.time_sleep)
            self.main_window.plainTextEdit.appendPlainText('执行文本输入' + str(input_value))
        elif special_control_judgment == 'True':
            pyautogui.typewrite(input_value, interval=self.settings.interval)
            self.main_window.plainTextEdit.appendPlainText('执行特殊控件的文本输入' + str(input_value))
            time.sleep(self.settings.time_sleep)

    def stop_time(self, seconds):
        """暂停时间"""
        for i in range(seconds):
            keyboard.hook(self.abc)
            # 显示剩下等待时间
            self.main_window.plainTextEdit.appendPlainText('等待中...剩余' + str(seconds - i) + '秒')
            # print('等待中...剩余' + str(seconds - i) + '秒')
            QApplication.processEvents()
            if self.start_state is False:
                break
            time.sleep(1)

    def abc(self, x):
        """键盘事件，退出任务、开始任务、暂停恢复任务"""
        a = keyboard.KeyboardEvent('down', 1, 'esc')
        s = keyboard.KeyboardEvent('down', 31, 's')
        r = keyboard.KeyboardEvent('down', 19, 'r')
        # var = x.scan_code
        # print(var)
        if x.event_type == 'down' and x.name == a.name:
            self.main_window.plainTextEdit.appendPlainText('你按下了退出键')
            print("你按下了退出键")
            self.start_state = False
        if x.event_type == 'down' and x.name == s.name:
            self.main_window.plainTextEdit.appendPlainText('你按下了暂停键')
            print("你按下了暂停键")
            self.suspended = True
        if x.event_type == 'down' and x.name == r.name:
            self.main_window.plainTextEdit.appendPlainText('你按下了恢复键')
            print('你按下了恢复键')
            self.suspended = False


class SettingsData:
    def __init__(self):
        self.duration = 0
        self.interval = 0
        self.confidence = 0
        self.time_sleep = 0

    def init(self):
        """设置初始化"""
        # 从数据库加载设置
        # 取得当前文件目录
        cursor, conn = self.sqlitedb()
        # 从数据库中取出全部数据
        cursor.execute('select * from 设置')
        # 读取全部数据
        list_setting_data = cursor.fetchall()
        # 关闭连接
        self.close_database(cursor, conn)

        for i in range(len(list_setting_data)):
            if list_setting_data[i][0] == '图像匹配精度':
                self.confidence = list_setting_data[i][1]
            elif list_setting_data[i][0] == '时间间隔':
                self.interval = list_setting_data[i][1]
            elif list_setting_data[i][0] == '持续时间':
                self.duration = list_setting_data[i][1]
            elif list_setting_data[i][0] == '暂停时间':
                self.time_sleep = list_setting_data[i][1]

    @staticmethod
    def sqlitedb():
        """建立与数据库的连接，返回游标"""
        try:
            # # 取得当前文件目录
            con = sqlite3.connect('命令集.db')
            cursor = con.cursor()
            print('成功连接数据库！')
            return cursor, con
        except sqlite3.Error:
            x = input("未连接到数据库！！请检查数据库路径是否异常。")
            print(x)
            sys.exit()

    @staticmethod
    def close_database(cursor, conn):
        """关闭数据库"""
        cursor.close()
        conn.close()


class WebOption:
    def __init__(self, main_window=None, navigation=None):
        self.main_window = main_window
        self.navigation = navigation
        self.driver = None
        # 保存的表格数据
        self.excel_path = None
        self.sheet_name = None
        # 拖动元素的距离
        self.distance_x = 0
        self.distance_y = 0
        # 输入的文本
        self.text = None

    def web_open_test(self, url):
        """打开网页"""
        if url == '':
            url = 'https://www.cn.bing.com/'
        else:
            if url[:7] != 'http://' and url[:8] != 'https://':
                url = 'http://' + url

        self.driver = webdriver.Chrome()
        try:
            self.driver.get(url)
            time.sleep(1)
            self.driver.quit()
            QMessageBox.information(self.navigation, '提示', '连接成功。', QMessageBox.Yes)
        except Exception as e:
            # 弹出错误提示
            print(e)
            QMessageBox.warning(self.navigation, '警告', '连接失败，请重试。系统故障、网络故障或网址错误。',
                                QMessageBox.Yes)

    def install_browser_driver(self):
        """安装谷歌浏览器的驱动"""
        try:
            service = ChromeService(executable_path=ChromeDriverManager().install())
            driver_ = webdriver.Chrome(service=service)
            driver_.quit()
        except ConnectionError:
            QMessageBox.warning(self.navigation, '警告', '驱动安装失败，请重试。', QMessageBox.Yes)

    def close_browser(self):
        """关闭浏览器驱动"""
        print('关闭浏览器驱动。')
        if self.driver is not None:
            self.driver.quit()

    def lookup_element(self, element_value_, element_type_, timeout_type_):
        """查找元素
        :param element_value_: 未开始查找的元素值
        :param element_type_: 元素类型
        :param timeout_type_: 超时错误"""
        # 查找元素(元素类型、超时错误)
        # 等待到指定元素出现
        try:
            print('正在查找元素' + element_value_)
            target_ele = None
            if element_type_ == 'xpath定位':
                target_ele = WebDriverWait(self.driver, timeout_type_).until(
                    EC.presence_of_element_located((By.XPATH, element_value_)))
            elif element_type_ == '元素名称':
                target_ele = WebDriverWait(self.driver, timeout_type_).until(
                    EC.presence_of_element_located((By.NAME, element_value_)))
            elif element_type_ == '元素ID':
                target_ele = WebDriverWait(self.driver, timeout_type_).until(
                    EC.presence_of_element_located((By.ID, element_value_)))
            return target_ele
        except TimeoutException:
            return None
        except NoSuchElementException:
            return None

    def switch_to_frame(self, iframe_type, iframe_value, switch_type):
        """切换frame
        :param iframe_type: iframe类型（id或名称：、xpath定位：）
        :param iframe_value: iframe值
        :param switch_type: 切换类型（切换到指定frame，切换到上一级或切换到主文档）"""
        if switch_type == '切换到指定frame':
            if iframe_type == 'frame名称或ID：':
                self.driver.switch_to.frame(iframe_value)
            elif iframe_type == 'Xpath定位：':
                self.driver.switch_to.frame(self.driver.find_element(By.XPATH, iframe_value))
        elif switch_type == '切换到上一级文档':
            self.driver.switch_to.parent_frame()
        elif switch_type == '切换回主文档':
            self.driver.switch_to.default_content()

    def switch_to_window(self, window_type, window_value):
        """切换窗口
        :param window_type: 窗口类型（窗口名称或ID：、窗口标题：）
        :param window_value: 窗口值"""
        if window_type == '窗口ID：':
            self.driver.switch_to.window(self.driver.window_handles[int(window_value)])
        elif window_type == '窗口标题：':
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if self.driver.title in window_value:
                    break

    def perform_mouse_action(self, element_value_, element_type_, timeout_type_, action):
        """鼠标操作
        :param element_value_: 未开始查找的元素值
        :param action: 鼠标操作
        :param element_type_: 元素类型
        :param timeout_type_: 超时错误"""
        # 查找元素(元素类型、超时错误)
        target_ele = self.lookup_element(element_value_, element_type_, timeout_type_)
        if target_ele is not None:
            print('找到网页元素，执行鼠标操作。')
            # self.main_window_.plainTextEdit.appendPlainText('找到网页元素，执行鼠标操作。')
            # QApplication.processEvents()
            if action == '左键单击':
                ActionChains(self.driver).click(target_ele).perform()
            elif action == '左键双击':
                ActionChains(self.driver).double_click(target_ele).perform()
            elif action == '右键单击':
                ActionChains(self.driver).context_click(target_ele).perform()
            elif action == '输入内容':
                target_ele.send_keys(self.text)
            elif action == '读取网页表格':
                table_html = target_ele.get_attribute('outerHTML')
                df = pd.read_html(table_html)
                df1 = pd.DataFrame(df[0])
                df1.to_excel(self.excel_path, index=False, sheet_name=self.sheet_name)
                # with pd.ExcelWriter(self.excel_path, engine='openpyxl', mode='a') as writer:
                #     df[0].to_excel(writer, index=False, sheet_name=self.sheet_name)
            elif action == '拖动元素':
                ActionChains(self.driver).click_and_hold(target_ele).perform()
                ActionChains(self.driver).move_by_offset(self.distance_x, self.distance_y +
                                                         random.randint(-5, 5)).perform()
                ActionChains(self.driver).release().perform()
        elif target_ele is None:
            raise TimeoutException

    def single_shot_operation(self, url, action, element_type_, element_value_, timeout_type_):
        """单步骤操作
        :param url: 网址
        :param action: 鼠标操作（左键单击、左键双击、右键单击、输入内容、读取网页表格、拖动元素）
        :param element_type_: 元素类型（元素ID、元素名称、xpath定位）
        :param element_value_: 元素值
        :param timeout_type_: 超时错误（找不到元素自动跳过、秒数）"""

        def open_url(url_):
            """打开网页或者直接跳过"""
            if url_ == '' or url_ is None:
                pass
            else:
                if url_[:7] != 'http://' and url_[:8] != 'https://':
                    url_ = 'http://' + url_

                chrome_options = webdriver.ChromeOptions()
                # 添加选项配置：  # 但是用程序打开的网页的window.navigator.webdriver仍然是true。
                chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
                chrome_options.add_experimental_option("detach", True)
                # # 去掉window.navigator.webdriver的特性
                # chrome_options.add_argument("disable-blink-features=AutomationControlled")
                # 设置为无头浏览器：不会显示出操作浏览器的过程
                # chrome_options.add_argument('--headless')
                # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
                chrome_options.add_argument('--start-maximized')
                # 初始化浏览器并打开网页
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.get(url_)
                # 窗口最大化
                # self.driver.maximize_window()

                time.sleep(1)

        open_url(url)
        if action == '' or action is None:
            print('没有鼠标操作。')
            pass
        else:
            print('执行鼠标操作。')
            # 执行鼠标操作
            self.perform_mouse_action(action=action,
                                      element_type_=element_type_,
                                      timeout_type_=timeout_type_,
                                      element_value_=element_value_)


if __name__ == '__main__':
    # 初始化功能类
    web = WebOption()

    web.text = 'python'
    web.single_shot_operation(
        url='https://www.baidu.com/',
        action='输入内容',
        element_value_='//*[@id="k"]',
        element_type_='xpath定位',
        timeout_type_=3)

    time.sleep(5)
    web.close_browser()
