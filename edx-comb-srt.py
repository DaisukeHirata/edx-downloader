#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import commands

DEFAULT_DOWNLOAD_DIRECTORY = './Downloaded'

if __name__ == '__main__':

    courses = os.listdir(DEFAULT_DOWNLOAD_DIRECTORY)

    for i, course in enumerate(courses):
        print(str(i+1) + ' : ' + course)

    c_number = int(input('Enter Course Number: '))

    course_dir = DEFAULT_DOWNLOAD_DIRECTORY + '/' + courses[c_number-1]

    mp4_list = glob.glob(course_dir + '/*.mp4')

    for mp4 in mp4_list:
        filename, ext = os.path.splitext(mp4)
        srt = filename + '.en.srt'
        outfile = filename + '.srt.mp4'
        cmd = 'MP4Box -add "%s" -add "%s":hdlr=sbtl:lang=eng -new "%s"' % (mp4, srt, outfile)
        status, cmdoutput = commands.getstatusoutput(cmd)
        if status == 0:
            print(outfile)
        else:
            print(cmdoutput)


