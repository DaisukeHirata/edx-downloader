#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python 2/3 compatibility imports
from __future__ import print_function
from __future__ import unicode_literals

try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    from urllib.request import urlopen
    from urllib.request import build_opener
    from urllib.request import install_opener
    from urllib.request import HTTPCookieProcessor
    from urllib.request import Request
except ImportError:
    from urllib2 import urlopen
    from urllib2 import build_opener
    from urllib2 import install_opener
    from urllib2 import HTTPCookieProcessor
    from urllib2 import Request
# we alias the raw_input function for python 3 compatibility
try:
    input = raw_input
except:
    pass

import getopt
import getpass

import json
import os
import re
import sys

from bs4 import BeautifulSoup

EDX_HOMEPAGE = 'https://courses.edx.org/login_ajax'
LOGIN_API = 'https://courses.edx.org/login_ajax'
DASHBOARD = 'https://courses.edx.org/dashboard'
YOUTUBE_VIDEO_ID_LENGTH = 11


## If no download directory is specified, we use the default one
DEFAULT_DOWNLOAD_DIRECTORY = "./Downloaded/"
DOWNLOAD_DIRECTORY = DEFAULT_DOWNLOAD_DIRECTORY

## If nothing else is chosen, we chose the default user agent:

DEFAULT_USER_AGENTS = {"google-chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31",
                       "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0",
                       "default": 'edX-downloader/0.01'}

USER_AGENT = DEFAULT_USER_AGENTS["default"]

USER_EMAIL = "daisukihirata@gmail.com"
USER_PSWD = "9nvfhxre"


def get_initial_token():
    """
    Create initial connection to get authentication token for future requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    install_opener(opener)
    opener.open(EDX_HOMEPAGE)

    for cookie in cj:
        if cookie.name == 'csrftoken':
            return cookie.value

    return ''


def get_page_contents(url, headers):
    """
    Get the contents of the page at the URL given by url. While making the
    request, we use the headers given in the dictionary in headers.
    """
    result = urlopen(Request(url, None, headers))
    return result.read()

def directory_name(initial_name):
    import string
    allowed_chars = string.digits+string.ascii_letters+" _."
    result_name = ""
    for ch in initial_name:
        if allowed_chars.find(ch) != -1:
            result_name+=ch
    return result_name if result_name != "" else "course_folder"

def parse_commandline_options(argv):
    global USER_EMAIL, USER_PSWD, DOWNLOAD_DIRECTORY, USER_AGENT
    opts, args = getopt.getopt(argv,
                               "u:p:",
                               ["download-dir=", "user-agent=", "custom-user-agent="])
    for opt, arg in opts :
        if opt == "-u" :
            USER_EMAIL = arg

        elif opt == "-p" :
            USER_PSWD = arg

        elif opt == "--download-dir" :
            if arg.strip()[0] == "~" :
                arg = os.path.expanduser(arg)
            DOWNLOAD_DIRECTORY = arg

        elif opt == "--user-agent" :
            if arg in DEFAULT_USER_AGENTS.keys():
                USER_AGENT = DEFAULT_USER_AGENTS[arg]


        elif opt == "--custom-user-agent":
            USER_AGENT = arg

        elif opt == "-h":
            usage()


def usage() :
    print("command-line options:")
    print("""-u <username>: (Optional) indicate the username.
-p <password>: (Optional) indicate the password.
--download-dir=<path>: (Optional) save downloaded files in <path>
--user-agent=<chrome|firefox>: (Optional) use Google Chrome's of Firefox 24's
             default user agent as user agent
--custom-user-agent="MYUSERAGENT": (Optional) use the string "MYUSERAGENT" as
             user agent
""")



def main():
    global USER_EMAIL, USER_PSWD
    try:
        parse_commandline_options(sys.argv[1:])
    except getopt.GetoptError :
        usage();
        sys.exit(2)

    if USER_EMAIL == "":
        USER_EMAIL = input('Username: ')
    if  USER_PSWD == "":
        USER_PSWD = getpass.getpass()

    if USER_EMAIL == "" or USER_PSWD == "":
        print("You must supply username AND password to log-in")
        sys.exit(2)

    # Prepare Headers
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': get_initial_token(),
    }

    # Login
    post_data = urlencode({'email': USER_EMAIL, 'password': USER_PSWD,
                           'remember': False}).encode('utf-8')
    request = Request(LOGIN_API, post_data, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    if not resp.get('success', False):
        print(resp.get('value', "Wrong Email or Password."))
        exit(2)

    # Get user info/courses
    dash = get_page_contents(DASHBOARD, headers)
    soup = BeautifulSoup(dash)
    data = soup.find_all('ul')[1]
    USERNAME = data.find_all('span')[1].string
    USEREMAIL = data.find_all('span')[3].string
    COURSES = soup.find_all('article', 'course')
    courses = []
    for COURSE in COURSES:
        c_name = COURSE.h3.text.strip()
        c_link = 'https://courses.edx.org' + COURSE.a['href']
        if c_link.endswith('info') or c_link.endswith('info/'):
            state = 'Started'
        else:
            state = 'Not yet'
        courses.append((c_name, c_link, state))
    numOfCourses = len(courses)

    # Welcome and Choose Course

    print('Welcome %s' % USERNAME)
    print('You can access %d courses on edX' % numOfCourses)

    c = 0
    for course in courses:
        c += 1
        print('%d - %s -> %s' % (c, course[0], course[2]))

    c_number = int(input('Enter Course Number: '))
    while c_number > numOfCourses or courses[c_number - 1][2] != 'Started':
        print('Enter a valid Number for a Started Course ! between 1 and ',
              numOfCourses)
        c_number = int(input('Enter Course Number: '))
    selected_course = courses[c_number - 1]
    COURSEWARE = selected_course[1].replace('info', 'courseware')

    ## Getting Available Weeks
    courseware = get_page_contents(COURSEWARE, headers)
    soup = BeautifulSoup(courseware)

    data = soup.find("section",
                     {"class": "content-wrapper"}).section.div.div.nav
    WEEKS = data.find_all('div')
    weeks = [(w.h3.a.string, ['https://courses.edx.org' + a['href'] for a in
             w.ul.find_all('a')]) for w in WEEKS]
    numOfWeeks = len(weeks)

    # Choose Week or choose all
    print('%s has %d weeks so far' % (selected_course[0], numOfWeeks))
    w = 0
    for week in weeks:
        w += 1
        print('%d - Download %s videos' % (w, week[0].strip()))
    print('%d - Download them all' % (numOfWeeks + 1))

    w_number = int(input('Enter Your Choice: '))
    while w_number > numOfWeeks + 1:
        print('Enter a valid Number between 1 and %d' % (numOfWeeks + 1))
        w_number = int(input('Enter Your Choice: '))

    if w_number == numOfWeeks + 1:
        links = [link for week in weeks for link in week[1]]
    else:
        links = weeks[w_number - 1][1]

    video_id = []
    for link in links:
        print("Processing '%s'..." % link)
        page = get_page_contents(link, headers)
        splitter = re.compile(b'data-streams=(?:&#34;|").*1.0[0]*:')
        id_container = splitter.split(page)[1:]
        video_id += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                     id_container]

    video_link = ['http://youtube.com/watch?v=' + v_id.decode("utf-8")
                  for v_id in video_id]

    # Get Available Video_Fmts
    os.system('youtube-dl -F %s' % video_link[-1])
    video_fmt = int(input('Choose Format code: '))

    # Get subtitles
    subtitles = input('Download subtitles (y/n)? ') == 'y'

    # Say where it's gonna download files, just for clarity's sake.
    print("Saving videos into: " + DOWNLOAD_DIRECTORY)
    print("\n\n")

    # Download Videos
    c = 0
    for v in video_link:
        c += 1
        cmd = 'youtube-dl -o "' + DOWNLOAD_DIRECTORY + '/' + directory_name(selected_course[0]) + '/' + \
        str(c).zfill(2) + '-%(title)s.%(ext)s" -f ' + str(video_fmt)
        if subtitles:
            cmd += ' --write-auto-sub'
        cmd += ' ' + str(v)
        os.system(cmd)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt :
        print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
