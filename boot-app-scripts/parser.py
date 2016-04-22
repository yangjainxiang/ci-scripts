#!/usr/bin/env python
# -*- coding: utf-8 -*-
#                      
#    E-mail    :    wu.wu@hisilicon.com 
#    Data      :    2016-03-11 14:26:46
#    Desc      :

# this file is just for the result parsing
# the input is files in the directory named ''

import string
import os
import subprocess
import fnmatch
import time
import re
import sys
import shutil

job_map = {}

parser_result = 'parser_result'
board_type_pre = 'board_type_'
summary_post = '_summary.txt'
board_pre = 'board#'
whole_summary_name = 'whole_summary.txt'
match_str = '[A-Z]+_?[A-Z]*'
ip_address = 'device_ip_type.txt'
boot_pre = 'boot#'

total_str = "Total number of test cases: "
fail_str = "Failed number of test cases: "
suc_str = "Success number of test cases: "

def summary_for_kind(result_dir):
    for root, dirs, files in os.walk(result_dir):
        for filename in files:
            if ip_address == filename:
                os.remove(os.path.join(root, filename))
                continue
            if filename.endswith(whole_summary_name):
                continue
            if 'boot' in filename or 'BOOT' in filename:
                if not re.findall(match_str, filename):
                   print filename
                continue
            if 'summary' in filename:
                test_case_name = re.findall(match_str, filename)
                if test_case_name:
                    test_kind = test_case_name[0]
                else:
                    test_kind = ''
                if test_kind:
                    board_type = filename.split(test_kind)[0][:-1]
                else:
                    board_type = filename.split(summary_post)[0]
                if test_kind and board_type:
                    board_class = os.path.join(parser_result, board_type_pre + board_type)
                    if not os.path.exists(parser_result):
                        os.mkdir(parser_result)
                    # create the directory for the special kind of board
                    if not os.path.exists(board_class):
                        os.makedirs(board_class)
                    # create the test for each kind test, each file with one file
                    test_kind_name = os.path.join(board_class, test_kind)
                    if os.path.exists(test_kind_name):
                        os.remove(test_kind_name)
                    fail_cases = []
                    total_num = 0
                    with open(test_kind_name, 'ab') as fd:
                        with open(os.path.join(root, filename), 'rb') as rfd:
                            contents = rfd.read()
                        fd.write(board_type + '_' + test_kind + '\n')
                        total_num = len(re.findall("job_id", contents))
                        fail_num = 0
                        for case in contents.split('\n\n'):
                            test_case = re.findall("=+\s*\n(.*)\s*\n=+", case, re.DOTALL)
                            job_id = re.findall("(job_id.*)", case)
                            if test_case and job_id:
                                testname = test_case[0]
                                fail_flag = re.findall('FAIL', case)
                                if fail_flag:
                                    fail_num += 1
                                    fail_cases.append(job_id[0] + '\n' + testname + '\t\t' + 'FAIL\n\n')
                        fd.write(total_str + str(total_num) + '\n')
                        fd.write(fail_str + str(fail_num) + '\n')
                        fd.write(suc_str + str(total_num - fail_num) + '\n')
                        if len(fail_cases):
                            fd.write("\n================Failed cases===============\n")
                        for i in range(0, len(fail_cases)):
                            fd.write(fail_cases[i])

def write_summary_for_app(result_dir):
    dic_app_cases = {}
    # write summary for app
    for root, dirs, files in os.walk(result_dir):
        for dirname in dirs:
            # board_type_
            if board_type_pre in dirname:
                board_type = dirname.split(board_type_pre)[-1]
                # board#d02
                board_summary_name = board_pre + board_type
                total_num_case = 0
                fail_num_case = 0
                suc_num_case = 0
                for root1, dirs, files in os.walk(root):
                    for filename in files:
                        summary_name = os.path.join(result_dir, board_summary_name)
                        with open(summary_name, 'ab') as fd:
                            with open(os.path.join(root1, filename), 'rb') as rfd:
                                lines = rfd.readlines()
                                for i in range(0, len(lines)):
                                    if re.search('FAIL', lines[i]):
                                        fd.write("Test category: " + filename + '\n')
                                        break
                                for i in range(0, len(lines)):
                                    try:
                                        if re.match(total_str, lines[i]):
                                            total_num_case += string.atoi(re.findall('(\d+)', lines[i])[0][0])
                                        elif re.match(fail_str, lines[i]):
                                            fail_num_case += string.atoi(re.findall('(\d+)', lines[i])[0][0])
                                        elif re.match(suc_str, lines[i]):
                                            suc_num_case += string.atoi(re.findall('(\d+)', lines[i])[0][0])
                                        else:
                                            if re.search('FAIL', lines[i]):
                                                job_id = re.search('job_id.*?(\d+)', lines[i-1]).group(1)
                                                fd.write('\t' + str(job_id) + '\t' + lines[i])
                                    except Exception:
                                        continue
                dic_app_cases[board_type] = [total_num_case, fail_num_case, suc_num_case]
    return dic_app_cases

def write_summary_for_boot(boot_dir, dic_app_case):
    # write summary for boot
    dic_boot_num = {}
    for root, dirs, files in os.walk(boot_dir):
        for filename in files:
            # for the boot of ramdisk
            if 'boot' in filename and not filename.startswith('boot'):
                continue
            if 'BOOT' in filename and not filename.startswith('boot'):
                with open(os.path.join(root, filename), 'rb') as rfd:
                    content = rfd.read()
                if re.findall('Full Boot Report', content):
                    boot_name = re.findall(match_str, filename)[0]
                    with open(os.path.join(root, filename), 'rb') as rfd:
                        lines = rfd.readlines()
                    flag = len(lines) - 1
                    for i in range(len(lines)):
                        if re.findall('Full Boot Report', lines[i]):
                            flag = i
                            break
                    total_num = 0
                    fail_num = 0
                    suc_num = 0
                    for i in range(flag+1, len(lines)):
                        try:
                            if len(lines[i]) <= 1:
                                continue
                            board_type = lines[i].split()[2].split('_')[0]
                            boot_result = lines[i].split()[-1]
                            job_id = lines[i].split()[0]
                            boot_summary_name = boot_pre + 'summary'
                            dic_boot_num[board_type] = []
                            with open(os.path.join(boot_dir, boot_summary_name), 'ab') as fd:
                                if re.findall('FAIL', lines[i]):
                                    total_num += 1
                                    fail_num += 1
                                    fd.write('\t' + job_id + '\t' + board_type + '\t' + boot_name + '\t' + 'FAIL\n')
                                else:
                                    total_num += 1
                                    suc_num += 1
                                    fd.write('\t' + job_id + '\t' + board_type + '\t' + boot_name + '\t' + 'PASS\n')
                        except IndexError:
                            continue
                        dic_boot_num[board_type] = [total_num, fail_num, suc_num]
    return dic_boot_num

def sum_of_dic(dic1, dic2):
    dic_sum = {}
    for key in dic1.keys():
        if key in dic2.keys():
            if key not in dic_sum.keys():
                dic_sum[key] = [0, 0, 0]
            dic_sum[key][0] = dic1[key][0] + dic2[key][0]
            dic_sum[key][1] = dic1[key][1] + dic2[key][1]
            dic_sum[key][2] = dic1[key][2] + dic2[key][2]
        else:
            dic_sum[key] = dic1[key]
    for key in dic2.keys():
        if key not in dic1.keys():
            dic_sum[key] = dic2[key]
    return dic_sum

def summary_for_board(boot_dir, result_dir):
    dic_app_case = write_summary_for_app(result_dir)
    dic_boot_case = write_summary_for_boot(boot_dir, dic_app_case)
    dic_sum = sum_of_dic(dic_app_case, dic_boot_case)
    for board in dic_app_case.keys():
        board_summary_name = board_pre + board
        with open(os.path.join(result_dir, board_summary_name), 'ab') as fd:
            fd.write("\n" + total_str + str(dic_app_case[board][0]))
            fd.write("\n" + fail_str + str(dic_app_case[board][1]))
            fd.write("\n" + suc_str + str(dic_app_case[board][2]) + '\n')
    #if len(dic_app_case.keys()) > len(dic_boot_case.keys()):

def parser_all_files(result_dir):
    summary_path = os.path.join(result_dir, whole_summary_name)
    if os.path.exists(summary_path):
        os.remove(summary_path)
    # get the each kind tests in each file
    true_parser_path = os.path.join(result_dir, parser_result)
    if os.path.exists(true_parser_path):
        shutil.rmtree(true_parser_path)
    if os.path.exists(parser_result):
        shutil.rmtree(parser_result)
    summary_for_kind(result_dir)
    # summary each file for each kind of board
    if os.path.exists(parser_result):
        summary_for_board(result_dir, parser_result)
        shutil.move(parser_result, result_dir)

if __name__ == '__main__':
    try:
        result_dir = sys.argv[1]
    except IndexError:
        print "Need to point out where the outputs store"
        raise
    #print result_dir
    if result_dir:
        parser_all_files(result_dir)