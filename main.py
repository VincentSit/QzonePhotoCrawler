#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import os
import sys
import requests
import api

SAVEPATH = os.path.join(os.path.split(sys.argv[0])[0], 'QQphoto')


class QQphoto(api.login):

    def __init__(self):
        super(QQphoto, self).__init__()
        headers = {
            'Referer': 'http://ctc.qzs.qq.com/qzone/photo/v7/page/photo.html?init=photo.v7/module/albumList/index&navBar=1'}
        self.requesr_session.headers.update(headers)
        self.albumlist = []

    def getalbum(self, pageStart=None):
        payload = {
            'g_tk': self.g_tk,
            'format': 'jsonp',
            'hostUin': self.uin,
            'uin': self.uin,
            'pageStart': pageStart,
            'mode': 2,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8'
        }
        print u'获取相册列表'
        album_request = self.requesr_session.get(
            'http://tjalist.photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3', params=payload)
        album_request.raise_for_status()
        pattern = re.compile(r'_Callback\(([\s\S]+)\);')
        albumjson = json.loads(pattern.match(album_request.text).group(1))
        for album in albumjson['data']['albumList']:
            albumID = album['id']
            albumName = album['name']
            albumNum = album['total']
            albumDesc = album['desc']
            print "%s  %s" % (albumName, albumNum)
            self.albumlist.append({'albumID': albumID,
                                   'albumName': albumName,
                                   'albumDesc': albumDesc,
                                   'albumNum': albumNum
                                   })
        if not albumjson['data']['nextPageStart'] == albumjson['data']['albumsInUser']:
            self.getalbum(albumjson['data']['nextPageStart'])
        return self.albumlist

    def getphotolist(self, albumid, pageStart=0, pageNum=30):
        payload = {
            'g_tk': self.g_tk,
            'uin': self.uin,
            'hostUin': self.uin,
            'mode': 0,
            'topicId': albumid,
            'format': 'jsonp',
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'pageStart': pageStart,
            'pageNum': pageNum
        }
        photolist = []
        print u'获取照片列表'
        photolist_request = self.requesr_session.get(
            'http://tjplist.photo.qzone.qq.com/fcgi-bin/cgi_list_photo',
            params=payload)
        photolist_request.raise_for_status()
        pattern = re.compile(r'_Callback\(([\s\S]+)\);')
        photolistjson = json.loads(
            pattern.match(photolist_request.text).group(1))
        for photo in photolistjson['data']['photoList']:
            photoName = photo['name']
            photoDesc = photo['desc']
            photoType = photo['phototype']
            # JPG 1 5 PNG 3 GIF 2
            photoURL = photo['raw'] or photo['origin_url'] or photo['url']
            photolist.append({
                'photoName': photoName,
                'photoDesc': photoDesc,
                'photoType': photoType,
                'photoURL': photoURL
            })
        return photolist

    def iterphoto(self, albumid, total, pageNum=30):
        if total:  # 如果照片总数不为零
            for pageStart in xrange(0, total, pageNum):
                yield self.getphotolist(albumid, pageStart, pageNum)

    def download_img(self, url, savepath):
        try:
            download_request = requests.get(url, stream=True, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows Phone 8.0; Trident/6.0; IEMobile/10.0; ARM; Touch; NOKIA; Lumia 520)'}
            )
            if download_request.status_code == 200:
                with open(savepath, 'wb') as data:
                    for chunk in download_request.iter_content(chunk_size=1024):
                        data.write(chunk)
        except (KeyboardInterrupt, SystemExit), e:
            if os.path.isfile(savepath):
                os.remove(savepath)
            raise e

    def _check_path(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)

    def _check_name(self, name):
        name_re = re.compile(r'[\\/:\*\?"<>\|]')
        name = re.sub(name_re, '_', name)
        return name

    def _check_filename(self, path, name, filetype, oldname=None, i=1):
        name = self._check_name(name)
        if not oldname:
            oldname = name
        filepath = os.path.join(path, name + filetype)
        if os.path.isfile(filepath):
            name = oldname + '_' + unicode(i)
            i = i + 1
            return self._check_filename(path, name, filetype, oldname, i)
        else:
            return filepath

    def download(self, albumlist):
        for album in albumlist:
            photoList = []
            albumname = self._check_name(album['albumName'])
            albumpath = os.path.join(SAVEPATH, albumname)
            i = 1
            for photolist in self.iterphoto(album['albumID'], album['albumNum']):
                self._check_path(albumpath)
                photoList.extend(photolist)

            for photodict in photoList:
                # print photodict
                if photodict['photoType'] == 1 or photodict['photoType'] == 5:
                    imgtype = u'.jpg'
                elif photodict['photoType'] == 2:
                    imgtype = u'.gif'
                elif photodict['photoType'] == 3:
                    imgtype = u'.png'
                else:
                    imgtype = u'.pic'
                photopath = self._check_filename(
                    albumpath, photodict['photoName'], imgtype)
                print "%s / %s" % (i, album['albumNum'])
                i = i + 1
                self.download_img(photodict['photoURL'], photopath)


if __name__ == '__main__':
    login = QQphoto()
    login.run()
    login.getalbum()
    login.download(login.albumlist)
