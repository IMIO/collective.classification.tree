# -*- coding: utf-8 -*-
from collections import OrderedDict

from imio.pyutils.system import error
from imio.pyutils.system import read_csv
from imio.pyutils.system import verbose

import argparse
import re
import sys

valid_identifier = r'-?[.\d]+$'


def compare_tree_files():
    """Compares a tree file with a reference tree file"""
    parser = argparse.ArgumentParser(description='Compare a tree file with a reference one')
    parser.add_argument('-p', '--parts', dest='parts', help='Run parts: 1 (load ref), 2 (load tree), 3 (compare)',
                        default='123')
    parser.add_argument('-r', '--reference', dest='ref_file', help='Reference file (csv format)', required=True)
    parser.add_argument('-rc', '--reference_config', dest='ref_conf', required=True,
                        help='Reference file configuration: "skip lines|separator|id col|title col" (starting at 0). '
                             'Like: 1|;|0|1')
    parser.add_argument('-f', '--file', dest='tree_file', help='Tree file (csv format)', required=True)
    parser.add_argument('-fc', '--file_config', dest='tree_conf', required=True,
                        help='Tree file configuration: "skip lines|separator|id cols|title col" (starting at 0). '
                             'Like: 1|;|0,4|1')
    ns = parser.parse_args()
    verbose("Start of %s" % sys.argv[0])
    if '1' in ns.parts:
        verbose("Reading ref file '{}'".format(ns.ref_file))
        ref_confs = ns.ref_conf.split('|')
        if len(ref_confs) != 4:
            error("rc parameter not well formated: {}".format(ns.ref_conf))
            sys.exit(1)
        skip_lines, ref_id_col, ref_tit_col = int(ref_confs[0]), int(ref_confs[2]), int(ref_confs[3])
        lines = read_csv(ns.ref_file, skip_lines=skip_lines, delimiter=ref_confs[1])
        ref_dic = {}
        for i, line in enumerate(lines, start=skip_lines+1):
            k = line[ref_id_col]
            if k in ref_dic:
                error("Ref id already exists: {} : {} <=> {}".format(k, ref_dic[k]['t'], line[ref_tit_col]))
            else:
                if not re.match(valid_identifier, k):
                    error("{}, bad ref identifier value '{}', '{}'".format(i, k, line[ref_tit_col]))
                ref_dic[k] = {'u': '', 't': line[ref_tit_col]}

    if '2' in ns.parts:
        verbose("Reading tree file '{}'".format(ns.tree_file))
        tree_confs = ns.tree_conf.split('|')
        if len(tree_confs) != 4:
            error("fc parameter not well formated: {}".format(ns.tree_conf))
            sys.exit(1)
        skip_lines, tree_tit_col = int(tree_confs[0]), tree_confs[3]
        tree_id_cols = [int(c) for c in tree_confs[2].split(',')]
        lines = read_csv(ns.tree_file, skip_lines=skip_lines, delimiter=tree_confs[1])
        tree_dic = OrderedDict()
        for i, line in enumerate(lines, start=skip_lines+1):
            for j, id_col in enumerate(tree_id_cols):
                k = line[id_col]
                if not k:
                    continue
                v = tree_tit_col and j == 0 and line[int(tree_tit_col)] or ''
                if k not in tree_dic:
                    if not re.match(valid_identifier, k):
                        error("{},{}, bad tree identifier value '{}', '{}'".format(i, id_col, k, v))
                    tree_dic[k] = {'l': i, 'c': id_col, 't': v}
    if '123' == ns.parts:
        verbose("Comparing...")
        for k in tree_dic:
            tdk = tree_dic[k]
            if k in ref_dic:
                ref_dic[k]['u'] = 'd'  # direct usage
                if tdk['t'] and tdk['t'] != ref_dic[k]['t']:
                    print("{},{}, id '{}', different titles: '{}' <=> '{}'".format(tdk['l'], tdk['c'], k, tdk['t'],
                                                                                   ref_dic[k]['t']))
            else:
                com = "{},{}, id '{}', not found in ref".format(tdk['l'], tdk['c'], k)
                if tdk['t']:
                    com += " (tit='{}')".format(tdk['t'])
                print(com)
    verbose("End of %s" % sys.argv[0])
