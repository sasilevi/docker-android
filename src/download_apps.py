from bs4 import BeautifulSoup
import pandas as pd
from urllib.request import urlopen
import shutil
import requests
import logging
import argparse

log_format = ' %(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)'
log_level = logging.INFO
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger(__name__)


class APKPureDownload():
    def __init__(self, app_url, apk_name):
        """download app from pureapk

        Arguments:
            app_url {string} -- url of the download version page i.e /facebook/com.facebook.katana/versions
            apk_name {[type]} -- name to save the apk file i.e facebook.apk
        """
        self._apk_name = apk_name
        self._base_url = "https://apkpure.com"
        self._app_url = self._base_url + app_url.replace(self._base_url, '')
        self._versions = {}
        self._variants = {}
        self._get_versions()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _get_versions(self):
        response = requests.get(self._app_url)
        soup = BeautifulSoup(response.text, "html.parser")
        vers = soup.find('ul', attrs={'class': 'ver-wrap'})

        for a in vers.findAll('li'):
            download_link = a.find('a', href=True)
            v = a.find('div', attrs={'class': 'ver-item'})
            ver = v.find('span', attrs={'class': 'ver-item-n'})
            apk = v.find('span', attrs={'class': 'ver-item-t ver-apk'})
            variants_count = v.find('span', attrs={'class': 'ver-n'})
            self._versions[ver.text] = download_link['href']
            if variants_count != None:
                self._variants[ver.text] = variants_count.text

    def print_versions(self):
        for k, v in self._versions.items():
            if k in self._variants:
                log.info(f"{k} - {self._base_url+v} ({self._variants[k]})")
            else:
                log.info(f"{k} - {self._base_url+v}")

    def _save_apk(self, version, href):
        try:
            download_page = requests.get(href, stream=True)
            soup = BeautifulSoup(download_page.text, "html.parser")
            download_div = soup.find(
                'div', attrs={'class': 'fast-download-box fast-bottom'})
            download_link = download_div.find('a',
                                              href=True,
                                              attrs={'class': 'ga'})

            r = requests.get(download_link['href'], stream=True)
            if r.status_code == 200:
                with open(self._apk_name, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
        except Exception as e:
            log.error(f"Failed to download apk {e}")
            raise e
        log.info(f"apk was save successfuly to {self._apk_name}")

    def _download_version(self, version, arc='x86'):
        url = self._base_url + self._versions[version]
        response = requests.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        for r in soup.findAll('div', attrs={'class': 'table-row'}):
            for c in r.findAll('div', attrs={'class': 'table-cell dowrap'}):
                if arc.lower() == str(c.text).lower():
                    download = r.find('div',
                                      attrs={'class': 'table-cell down'})
                    download_link = download.find('a', href=True)
                    log.info(self._base_url + download_link['href'])
                    self._save_apk(version,
                                   self._base_url + download_link['href'])

    def download_version(self, version):
        return self._download_version(version=version)


def parse_args():
    parser = argparse.ArgumentParser(description="""Download app from apkpure
                        example: python3 download_apps.py --app-url=https://apkpure.com/facebook/com.facebook.katana/versions --apk-name=facebook.apk --app-version=V267.1.0.46.120"""
                                     )
    parser.add_argument('--app-url',
                        dest='app_url',
                        action='store',
                        help='/facebook/com.facebook.katana/versions')
    parser.add_argument('--apk-name',
                        dest='apk_name',
                        action='store',
                        help='name of apk to save i.e facebook.apk')
    parser.add_argument('--app-version',
                        dest='app_version',
                        action='store',
                        help='Version to download. i.e V267.1.0.46.120')

    return parser.parse_args()


def main():
    args = parse_args()
    # with APKPureDownload(
    #         app_url="https://apkpure.com/facebook/com.facebook.katana/versions",
    #         apk_name="facebook.apk") as download:
    #     download.print_versions()
    #     download.download_version(version='V267.1.0.46.120')
    with APKPureDownload(app_url=args.app_url,
                         apk_name=args.apk_name) as download:
        download.print_versions()
        download.download_version(version=args.app_version)


if __name__ == '__main__':
    main()
