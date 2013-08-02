#!/usr/bin/python

import os, sys
import optparse
from xml.dom.minidom import parse, parseString
from commandwrapper import WrapCommand

description = 'repo manifest diff tool description'
usage = '%prog -m <manifest0> -s <source> [-t manifest1]'
parser = optparse.OptionParser(description=description, usage=usage, version='%prog 1.2')
parser.add_option('-m', '--manifest0', help='point to previous manifest0 file')
parser.add_option('-s', '--source', help='point to current repo source directory')
parser.add_option('-t', '--manifest1', help='point to previous manifest1 file')

opts, pargs = parser.parse_args(args=sys.argv[1:])

if __name__ == '__main__':
    if not opts.source or not opts.manifest0:
        if len(pargs) == 2:
            opts.manifest0 = pargs[0]
            opts.source = pargs[1]
        if len(pargs) == 3:
            opts.manifest0 = pargs[0]
            opts.source = pargs[1]
            opts.manifest1 = pargs[2]
        else:
            print parser.get_usage()
            sys.exit(-1)

    if not os.path.isdir(opts.source) or \
         not os.path.isfile(opts.manifest0):
        print parser.get_usage()
        print 'Please ensure manifest0 is a file and source is a repo dir!'
        sys.exit(-2)

    doc = parse(opts.manifest0)
    p_r_map = {}
    for el in doc.getElementsByTagName('project'):
        if el.getAttribute('path'):
            p_r_map[el.getAttribute('path')] = [el.getAttribute('revision'), ]

    # check whether there is a new git or a removed git first.
    def check_repo_change(doc_path, p_r_map):
        t_doc = parse(doc_path)
        t_map = {}
        for el in t_doc.getElementsByTagName('project'):
            if el.getAttribute('path'):
                t_map[el.getAttribute('path')] = [el.getAttribute('revision'), ]
        new_git = list(set(t_map.keys()) - set(p_r_map.keys()))
        removed_git = list(set(p_r_map.keys()) - set(t_map.keys()))
        return new_git, removed_git

    if opts.manifest1 == None:
        # check whether there is a new git or a removed git first.
        new_git, removed_git = check_repo_change(os.path.join(opts.source, '.repo', 'manifest.xml'), p_r_map)
        if new_git:
            print 'Warning : there have some new git bewteen two repo\n\t%s' % new_git
        if removed_git:
            print 'Warning : there have some removed git bewteen two repo\n\t%s' % removed_git

        for p in p_r_map.keys():
            apath = os.path.join(opts.source, p)
            try:
                headpath = os.path.join(apath, '.git/HEAD')
                t = 0
                valid = False
                while t < 40:
                    with open(headpath) as f:
                        head = unicode(f.read().strip())
                    if head.startswith('ref'): # ref: refs/heads/s1
                        headpath = os.path.join(apath, '.git', head.split()[1])
                        continue
                    else:
                        valid = True
                        break
                    t += 1
                if not valid:
                    raise Exception('Error, can not find HEAD tag with %s' % os.path.join(apath, '.git/HEAD'))
                #if head.startswith('ref'): # ref: refs/heads/s1
                #    headpath = os.path.join(apath, '.git', head.split()[1])
                #    with open(headpath) as f:
                #        head = unicode(f.read().strip())
            except IOError:
                print '%s Not exists, imply it is not a git reposition' % headpath
                sys.exit(-2)
            p_r_map[p].append(head)
    else:
        # check whether there is a new git or a removed git first.
        new_git, removed_git = check_repo_change(opts.manifest1, p_r_map)
        if new_git:
            print '!Warning : there have some new git bewteen two repo\n\t%s' % new_git
        if removed_git:
            print '!Warning : there have some removed git bewteen two repo\n\t%s' % removed_git

        doc1 = parse(opts.manifest1)
        for el in doc1.getElementsByTagName('project'):
            if el.getAttribute('path'):
                if p_r_map.has_key(el.getAttribute('path')):
                    p_r_map[el.getAttribute('path')].append(el.getAttribute('revision'))

    for k, (v0, v1) in p_r_map.items(): 
        if v0 != v1:
            print '#### %s\t%s..%s' % (k, v0, v1)
            cmdstr = 'git --git-dir=%s log %s..%s' % (os.path.join(opts.source, k, '.git'), v0, v1)
            cmd = WrapCommand(cmdstr)
            cmd.start()
            cmd.join()
            if cmd.returncode != 0:
                raise Exception('Error run: %s\nReturn code: %s\nError msg: %s' % (cmdstr, cmd.returncode, ''.join(cmd.results[1])))

            print cmd.results[0]

    sys.exit(0)
    cmd = WrapCommand('repo sync')
    import ipdb; ipdb.set_trace()
    
