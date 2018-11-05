#!/usr/bin/python3
import os
import datetime
import hashlib
import sqlite3

# configuring logger
LOG_PATH = os.path.join(os.path.expanduser("~"), "Documents", "WebSnap", "logs")
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

import logging
logging.basicConfig(
    filename=os.path.join(LOG_PATH, "websnap.log"),
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s"
)

'''
    Handling snaps storage
'''
class Storage:

    # database filename
    DB_FILENAME = "snapsdb.sqlite"
    # location where information will be saved.
    STORAGE_PATH = os.path.join(os.path.expanduser("~"), "Documents", "WebSnap", "db")

    # date format
    DATE_FORMAT = "%d-%m-%Y %H:%M:%S"

    def __del__(self):
        if self.__opened:
            self.__conn.close()

    def __init__(self):
        # creating storage path if not exists
        if not os.path.exists(Storage.STORAGE_PATH):
            os.makedirs(Storage.STORAGE_PATH)
            logging.info("[Storage]: Storage path '{}' created successfully.".format(Storage.STORAGE_PATH))

        # initializing sqlite tables
        self.__conn = sqlite3.connect(os.path.join(Storage.STORAGE_PATH, Storage.DB_FILENAME))
        self.__opened = True
        self.__createTables()
        logging.info("[Storage]: Storage is initialized successfully.")

    def unzipsnap(self, snaps):
        return list(map(lambda v: dict(zip(("snap_id", "name", "creation_time"), v)), snaps))

    def unziplink(self, links):
        return list(map(lambda v: dict(zip(("url_id", "snap_id", "url", "creation_time"), v)), links))

    def __createTables(self):
        try:
            # creating tables
            cur = self.__conn.cursor()
            # snaps table => stores name of snapshot and when was it created.
            cur.execute('''CREATE TABLE IF NOT EXISTS snaps (
                snap_id text PRIMARY_KEY,
                name text NOT NULL,
                creation_time text NOT NULL);'''
            )
            # links => stores information of all urls and snapshot id they refer to.
            cur.execute('''CREATE TABLE IF NOT EXISTS links (
                url_id text PRIMARY_KEY,
                snap_id text NOT NULL,
                url text NOT NULL,
                creation_time text NOT NULL);'''
            )
            # commiting changes
            self.__conn.commit()
            logging.debug("[Storage.__createTables]: Tables 'snaps', 'links' created successfully.")
        except Exception as ex:
            self.__conn.rollback()
            logging.error("[Storage.__createTables]: Table creation failed with error '{}'.".format(ex))
            raise ex

    def __findSnap(self, snap_id):
        try:
            cur = self.__conn.cursor()
            cur.execute('''SELECT * FROM snaps WHERE snap_id=?''', (snap_id,))
            snaps = self.unzipsnap(cur.fetchall())
            if len(snaps) > 0:
                return snaps[0]
        except Exception as ex:
            logging.error("[Storage.__findSnap]: Failed to find snap_id '{}' due to error '{}'."
                    .format(snap_id, ex))
        return None

    def __findSnapUrls(self, snap_id):
        try:
            cur = self.__conn.cursor()
            cur.execute('''SELECT * FROM links WHERE snap_id=?''', (snap_id,))
            return self.unziplink(cur.fetchall())
        except Exception as ex:
            logging.error("[Storage.__findSnapUrls]: Failed get snap '{}' urls due to error '{}'.".format(snap_id, ex))
        return []

    def __findUrl(self, url_id):
        try:
            cur = self.__conn.cursor()
            cur.execute('''SELECT * FROM links WHERE url_id=?''', (url_id,))
            urls = self.unziplink(cur.fetchall())
            if len(urls) > 0:
                return urls[0]
        except Exception as ex:
            logging.error("[Storage.__findUrl]: Failed to find url_id '{}' due to error '{}'.".format(url_id, ex))
        return None

    def __createSnap(self, snapname):
        try:
            snap_id = snapname.lower()
            # checking if it already exists
            if self.__findSnap(snap_id):
                return snap_id

            # query to create snap
            query = '''INSERT INTO snaps(snap_id,name,creation_time) VALUES(?,?,?)'''
            values = (snap_id, snapname, datetime.datetime.now().strftime(Storage.DATE_FORMAT))

            # executing db command
            cur = self.__conn.cursor()
            cur.execute(query, values)
            self.__conn.commit()
            logging.debug("[Storage.__createSnap]: Snap '{}' entry created to snaps table.".format(snapname))
            return snap_id
        except Exception as ex:
            self.__conn.rollback()
            logging.error("[Storage.__createSnap]: Failed to save snap '{}' due to error '{}'".format(snapname, ex))
        return None

    def generateIdForUrl(self, url, snapname):
        hasher = hashlib.md5()
        str_ = "{}{}".format(url,snapname.lower())
        hasher.update(str_.encode())
        return hasher.hexdigest()

    def deleteSnap(self, snapname):
        try:
            if not self.deleteUrls(snapname, delete_all=True):
                return False

            # running db command
            cur = self.__conn.cursor()
            cur.execute('''DELETE FROM snaps WHERE snap_id=?''', (snapname.lower(),))
            self.__conn.commit()
            logging.info("[Storage.deleteSnap]: Snap '{}' along with all urls deleted successfully.".format(snapname))
            return True
        except Exception as ex:
            self.__conn.rollback()
            logging.error("[Storage.deleteSnap]: Failed to delete snap '{}' info due to error '{}'."
                    .format(snapname, ex))
        return False

    def deleteUrls(self, snapname, url_list=None, delete_all=False):
        try:
            # creating snap id
            snap_id = snapname.lower()

            # running db command
            cur = self.__conn.cursor()
            if delete_all is True and url_list is None:
                cur.execute('''DELETE FROM links WHERE snap_id=?''', (snap_id,))

            elif isinstance(url_list, list):
                url_values = [(self.generateIdForUrl(url, snapname),) for url in url_list if isinstance(url, str)]
                cur.executemany('''DELETE FROM links WHERE url_id=?''', url_values)

            elif isinstance(url_list, str):
                cur.execute('''DELETE FROM links WHERE url_id=?''', (url_list,))

            self.__conn.commit()
            logging.info("[Storage.deleteUrls]: All urls for snap '{}' deleted successfully.".format(snapname))
            return True
        except Exception as ex:
            self.__conn.rollback()
            logging.error("[Storage.deleteUrls]: Failed to delete urls for snap '{}' due to error '{}'."
                    .format(snapname, ex))
        return False

    def allSnaps(self):
        try:
            cur = self.__conn.cursor()
            cur.execute('''SELECT * FROM snaps''')
            all_snaps = self.unzipsnap(cur.fetchall())
            logging.info("[Storage.allSnaps]: Total '{}' snaps found.".format(len(all_snaps)))
            return all_snaps
        except Exception as ex:
            logging.error("[Storage.allSnaps]: Failed to retrieve list of all snaps due to error '{}'".format(ex))
        return []

    def getSnapInfo(self, snapname):
        # creating snap id
        snap_id = snapname.lower()
        info = {}
        # getting snap details
        info["snapshot"] = self.__findSnap(snap_id)
        # getting all urls for this snap
        info["urls"] = self.__findSnapUrls(snap_id)
        logging.info("[Storage.getSnapInfo]: Total '{}' urls retrieved for snap '{}'."
                .format(len(info["urls"]), snapname))
        return info

    def saveSnap(self, snapname, url_list):
        if not isinstance(url_list, list):
            raise TypeError("Storage.saveSnap <url_list must be 'list' object>")

        if not isinstance(snapname, str):
            raise TypeError("Storage.saveSnap <snapname must be 'string' object>")

        try:
            # creating snapshot information
            snap_id = self.__createSnap(snapname)

            # creating query and cursor
            cur = self.__conn.cursor()
            query = '''INSERT INTO links(url_id,snap_id,url,creation_time) VALUES(?,?,?,?)'''
            creation_time = datetime.datetime.now().strftime(Storage.DATE_FORMAT)

            valid_urls = []
            for url in url_list:
                if not isinstance(url, str):
                    raise TypeError("Storage.saveSnap <url must be 'string' object>")

                # checking if url is already saved
                url_id = self.generateIdForUrl(url, snapname)
                if self.__findUrl(url_id):
                    continue

                valid_urls.append((url_id, snap_id, url, creation_time))

            # executing db command
            cur.executemany(query, valid_urls)
            self.__conn.commit()
            logging.info("[Storage.saveSnap]: Snap '{}' saved with all given urls successfully.".format(snapname))
            return True
        except Exception as ex:
            self.__conn.rollback()
            logging.error("[Storage.saveSnap]: Failed to save snap '{}' due to error '{}'"
                    .format(snapname, ex))
        return False

'''
    Snapper site to serve web browser plugins
'''
from aiohttp import web

site = web.RouteTableDef()
site.storage = Storage()

@site.get("/snaps")
async def retrieve_snaps(request):
    all_snaps = site.storage.allSnaps()
    logging.debug("[site.get] [snaps]: List of snapshots '{}' retrieved successfully.".format(all_snaps))
    return web.json_response(all_snaps)

@site.get("/snaps/{snapname}")
async def get_snap_info(request):
    snapname = request.match_info['snapname']
    if snapname is None:
        logging.error("[site.get] [snaps/snapname]: Invalid snapshot name '{}' provided.".format(snapname))
        return web.json_response(
            {"error": "snapshot name not provided."},
            status=422
        )

    snapinfo = site.storage.getSnapInfo(snapname)
    logging.debug("[site.get] [snaps/snapname]: Snapshot '{}' information '{}' retrieved successfully."
            .format(snapname, snapinfo))
    return web.json_response(snapinfo)

@site.post("/snaps")
async def save_snaps(request):
    # decoding json data
    data = await request.json()

    # extracting elements
    snapname = data.get("snapshot")
    urls = data.get("urls")

    # validating elements
    urls = [] if urls is None else urls
    if not snapname or not isinstance(snapname, str):
        logging.error("[site.post] [snaps]: Invalid snapshot name '{}' provided.".format(snapname))
        return web.json_response(
            {"error": "'snapshot' name not provided."},
            status=422
        )

    if not isinstance(urls, list) or any(map(lambda e: not isinstance(e, str), urls)):
        logging.error("[site.post] [snaps]: Invalid urls list provided for snapshot '{}'.".format(snapname))
        return web.json_response(
            {"error": "'urls' must be list of valid urls."},
            status=422
        )

    # saving snapshot information
    logging.info("[site.post] [snaps]: Saving snapshot '{}' information.".format(snapname))
    if not site.storage.saveSnap(snapname, urls):
        logging.error("[site.post] [snaps]: Failed to save snapshot '{}' information.".format(snapname))
        return web.json_response(
            {"error": "Failed to save snapshot information."},
            status=500
        )
    return web.Response()

@site.delete("/snaps/{snapname}")
async def delete_snap_info(request):
    snapname = request.match_info['snapname']
    # validating
    if snapname is None or not isinstance(snapname, str):
        logging.error("[site.delete] [snaps/snapname]: Invalid snapshot name '{}' provided.".format(snapname))
        return web.json_response(
            {"error": "snapshot name must be string."},
            status=422
        )

    # deleting
    logging.info("[site.delete] [snaps/snapname]: Deleting snapshot '{}' complete information".format(snapname))
    if not site.storage.deleteSnap(snapname):
        logging.error("[site.delete] [snaps/snapname]: Failed to delete snapshot '{}'.".format(snapname))
        return web.json_response(
            {"error": "Failed to delete snapshot information."},
            status=500
        )
    return web.Response()

@site.delete("/snaps")
async def delete_urls_from_snap(request):
    # decoding json data
    data = await request.json()

    # extracting elements
    snapname = data.get("snapshot")
    urls = data.get("urls")

    # validating elements
    urls = [] if urls is None else urls
    if not snapname or not isinstance(snapname, str):
        logging.error("[site.delete] [snaps]: Invalid snapshot name '{}' provided.".format(snapname))
        return web.json_response(
            {"error": "'snapshot' name must be string."},
            status=422
        )

    if not isinstance(urls, list) or any(map(lambda e: not isinstance(e, str), urls)):
        logging.error("[site.delete] [snaps]: Invalid urls list provided for snapshot '{}'.".format(snapname))
        return web.json_response(
            {"error": "'urls' must be list of valid urls."},
            status=422
        )

    # saving snapshot information
    logging.info("[site.delete] [snaps]: Deleting '{}' urls from snapshot '{}'.".format(len(urls), snapname))
    if not site.storage.deleteUrls(snapname, urls):
        logging.error("[site.delete] [snaps]: Failed to delete urls form snapshot '{}'.".format(snapname))
        return web.json_response(
            {"error": "Failed to delete urls from snapshot."},
            status=500
        )
    return web.Response()

def run_snapper(site):
    app = web.Application()
    app.router.add_routes(site)
    web.run_app(app, host="localhost", port=5500)

if __name__ == "__main__":
    run_snapper(site)