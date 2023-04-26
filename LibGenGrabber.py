import requests
import os, sys
import re
import time
from time import perf_counter
import datetime
import json
import pprint
from bs4 import BeautifulSoup
import multiprocessing
import concurrent.futures

from concurrent.futures import ThreadPoolExecutor, as_completed


"""uses https://libgen.gs/index.php to search and download all search results"""

ALLOWED = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "-",
    "_",
    ".",
    "!",
    "@",
    "#",
    "$",
    "%",
    "&",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    "^",
    "~",
]


def file_namer(filename: str, ext: str, path: str):
    """returns a unique filename"""

    not_allowed = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]

    check_dir = os.listdir(path)

    filename = filename.replace(" ", "_")
    for char in not_allowed:
        filename = filename.replace(char, "_")
    filename = re.sub(r"_+", "_", filename)
    check_file = filename + ext
    counter = 0
    checked = False
    while not checked:
        if check_file not in check_dir:
            checked = True
            filename = check_file
            break
        elif check_file in check_dir:
            counter += 1
            check_file = filename + "_" + str(counter) + ext
            continue

    return filename


def print_headers(url):
    msg = requests.get(url)
    headers_dict = dict(msg.headers)
    pprint.pprint(headers_dict)
    return headers_dict


def main_search(url, save: bool = False):
    print(f"\n\tApplying query -> https://libgen.gs...")
    # print(f"\tFull URL: {url}")
    msg = requests.get(url)

    if msg.status_code == 200:
        print(f"\tConnection successful! [status code: {msg.status_code}]")

    main_soup = BeautifulSoup(msg.text, "html.parser")
    if save:
        with open("main_search.html", "w", encoding="utf-8") as file:
            file.write(str(main_soup))
    return main_soup


def get_json(main_soup: BeautifulSoup = None, save: bool = False):
    base_url = "https://libgen.gs"
    elements = main_soup.find_all("li", class_="navbar-right")
    if elements == []:
        return None
    else:
        tag = elements[0]
        tag = BeautifulSoup(str(tag), "html.parser")
        tag = tag.find_all("a", class_="nav-link")
        tag = tag[0]
        tag = tag["href"]
        url = base_url + tag
        print(f"\n\tGrabbing JSON data...")
        msg = requests.get(url)
        if msg.status_code == 200:
            print(f"\tJSON grab successful! [status code: {msg.status_code}]")
        if save:
            with open("main_search.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(msg.json(), indent=4, sort_keys=True))
        json_msg = dict(msg.json())
    return json_msg


def get_md5_list(json_msg: dict):
    md5_list = []
    for id in json_msg.keys():
        md5_list.append(json_msg[id]["md5"])
    print(f"\n\tDownloadable results returned: {len(md5_list)}")
    # print(md5_list)
    return md5_list


def download_file(url: str, filename: str, path: str):
    msg = requests.get(url)
    response = msg.status_code
    if response == 200:
        filename = f"{path}/{filename}"
        with open(filename, "wb") as f:
            f.write(msg.content)
    else:
        # print(f"\nError: {response},\n{url}\nTrying again in 5 seconds...\n")
        time.sleep(1)
        download_file(url, filename, path)


def grab_download_data(md5: str, save: bool = False):
    data = {"title": None, "year": None, "download-link": None}
    base_url = "https://libgen.rocks/get.php?md5="
    url = base_url + md5
    msg = requests.get(url)
    first_soup = BeautifulSoup(msg.text, "html.parser")
    if save:
        with open("download_page.html", "w", encoding="utf-8") as file:
            file.write(str(first_soup))

    def _get_year(first_soup: BeautifulSoup):
        look = first_soup.find_all("textarea", attrs={"id": "bibtext"})
        look = BeautifulSoup(str(look), "html.parser").text
        year = look.split("year")[1]
        year = year.split("{")[1]
        year = year.split("}")[0]
        return year

    def _get_title(first_soup: BeautifulSoup):
        look = first_soup.find_all("textarea", attrs={"id": "bibtext"})
        look = BeautifulSoup(str(look), "html.parser").text
        title = look.split("title")[1]
        title = title.split("{")[1]
        title = title.split("}")[0]

        for char in title:
            if char not in ALLOWED:
                title = title.replace(char, "_")

        title = title.strip("\n")
        title = title.strip("")
        title = title.strip(" ")
        title = title.rstrip("\n")
        title = title.rstrip("")
        title = title.rstrip(" ")
        title = title.replace("\r", "")
        title = title.replace("\n", "")
        title = title.replace(".", "_")

        list_chars = [char for char in title]

        return title

    def _get_link(first_soup: BeautifulSoup):
        look = first_soup.find_all("table", attrs={"id": "main"})
        look = BeautifulSoup(str(look), "html.parser")
        look = look.find_all("a")
        try:
            look = look[0]
            look = look.get("href")
            base_url = "https://libgen.rocks/"
            download_link = base_url + look
            return download_link
        except Exception as e:
            # print("Error: ", e)
            # print(first_soup)
            return None

    data["download-link"] = _get_link(first_soup)
    data["title"] = _get_title(first_soup)
    data["year"] = _get_year(first_soup)

    return data


def search_help():
    print(
        """
By default, the search searches for a set of marked fields containing all the words specified in the query in no particular order
Advanced search mode (Google mode), allows you to set more precise search terms:

- Quotes: "" - search exactly for the phrase as it is written in the database
- Mask: * (min 3 chars)- search by part of a word
- Excluding words: - (minus) - does not display records containing this word, also, these conditions can be combined.

    Example:
    "Physics and Chemistry" Basi * -technology

    ... means the title of the book contains the exact phrase "Physics and Chemistry", 
        contains the word starting with Basi,
        and does not contain the word technology.

You can also search for a specific field or view mode that is not displayed for selection in the interface, 

    syntax: 
        field_name:value

List of additional fields:

    For the Files tab:
        md5
        tth
        sha1
        sha256
        crc32
        edonkey
        doi

    View modes:
        mode:last - last added entries (for a given object - series, authors, editions, etc.)
        fmode:last - last added files (for the given repository)

    Additional fields for object "editions" and "files":
        issuevolume - periodical volume
        issuesid - serial ID of the periodical
        issuenumber - the number (within the volume) of the periodical
        issuetnumber is the gross number of the periodical
        issueynumber - intra-annual issue of the periodical
        year - year
        publisherid - Publisher ID
        authorid - Author's ID
        lang - three-letter language code (ISO 639)
        fsize - filesize (MBytes), for example: fsize>10, fsize<20, fsize=15
        ext - File extenstion

    Additional fields for object "series"
        comtopicid - ID of the classifier for comics
        smtopicid - ID of the classifier for scientific journals
        magtopicid - ID of the classifier for magazines
        issn - ISSN
"""
    )


def start_prompt():
    print(
        f"""\n{'='*64} 
    ╔╗     ╔╗  ╔═══╗            ╔═══╗        ╔╗  ╔╗         
    ║║     ║║  ║╔═╗║            ║╔═╗║        ║║  ║║         
    ║║   ╔╗║╚═╗║║ ╚╝╔══╗╔═╗     ║║ ╚╝╔═╗╔══╗ ║╚═╗║╚═╗╔══╗╔═╗
    ║║ ╔╗╠╣║╔╗║║║╔═╗║╔╗║║╔╗╗    ║║╔═╗║╔╝╚ ╗║ ║╔╗║║╔╗║║╔╗║║╔╝
    ║╚═╝║║║║╚╝║║╚╩═║║║═╣║║║║    ║╚╩═║║║ ║╚╝╚╗║╚╝║║╚╝║║║═╣║║ 
    ╚═══╝╚╝╚══╝╚═══╝╚══╝╚╝╚╝    ╚═══╝╚╝ ╚═══╝╚══╝╚══╝╚══╝╚╝
        created by: ∞herbling 
{'='*64}                         
                                                        """
    )
    print(
        f"\t-Queries https://libgen.gs/ for scientific articles\n\t-Downloads all resulting files\n\t-Enter 'ctrl-c' at any time to exit\n\t-If downloadable results returned is 1000\n\t\t...query is too broad, try being more specific\n\t-Type 'help' to show tips for advanced searching\n"
    )


class LibGenGrabber:
    def __init__(self):
        self.initial_query = None
        self.search = None
        self.folder = None
        self.folder_path = None
        self.hold_md5_list = None
        start_prompt()

    def create_search_term(self, search: str):
        for s in search:
            if s == " ":
                folder = search.replace(" ", "_")
                search = search.replace(" ", "+")
                break
            else:
                folder = search

        self.search = search
        self.folder = folder

    def mk_query_folder(self):

        not_allowed = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]

        folder = f"LibGenGrab-{self.folder}_{datetime.datetime.now().date()}"

        for n in not_allowed:
            if n in folder:
                folder = folder.replace(n, "'")

        cwd = os.getcwd()
        # cwd = sys.argv[-1]
        check_dir = os.listdir(cwd)

        checked = False
        check_count = None
        counter = 0
        while not checked:
            if check_count is None:
                if folder in check_dir:
                    counter += 1
                    check_count = folder + f"_{counter}"
                    continue
                elif folder not in check_dir:
                    checked = True
                    break
            elif check_count is not None:
                if check_count in check_dir:
                    counter += 1
                    check_count = folder + f"_{counter}"
                    continue
                elif check_count not in check_dir:
                    checked = True
                    break

        if check_count is not None:
            folder = check_count

        folder_path = os.path.join(cwd, folder)
        print(f"\tCreating folder -> {folder_path}")
        os.mkdir(folder_path)

        return folder, folder_path

    def _get_md5_list(self):
        search_url = "https://libgen.gs/index.php?req="
        add_end = "&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=a&res=100&gmode=on&filesuns=all&curtab=f&order=year&ordermode=desc"
        combined_url = search_url + self.search + add_end
        soup = main_search(combined_url)
        json_msg = get_json(soup)

        if json_msg == None:
            print(
                f"\n\t:(\t...sorry, 0 results returned for this query: [ {self.initial_query} ]"
            )
            retry = self.new_query()
            confirm_retry = False
            while not confirm_retry:
                if retry.lower() == "y" or retry.lower() == "yes":
                    confirm_retry = True
                    self.cli()
                elif retry.lower() == "n" or retry.lower() == "no":
                    print("\nExiting...\n")
                    sys.exit(0)
                else:
                    print("\n\tInvalid input, please enter 'y' or 'n'")
                    retry = self.new_query()
        else:

            md5_list = get_md5_list(json_msg)
            return md5_list

    def first_user_query(self):
        print("." * 64, "\n")
        query = input("Enter Search for https://libgen.gs/ below: \n\n")
        query = query.strip(" ")
        self.initial_query = query
        return query

    def confirm_first_query(self, query: str = None):
        print(f"\n\tYou wish to search for:\n\n\t[ {query} ]\n")
        check = input("Is this correct? ( y / n ): \n\n")
        return check

    def confirm_md5_list(self, md5_list: list = None):
        print(
            f"\n*Type 'thread' to attempt a multi-threaded download*\n\t...may cause instability, use with caution\n\tKeyBoard interrupt currently does not work when using multi-threading\n\t...to exit during operation, you must close the window\n{'-'*40}\nYou wish to download [{len(md5_list)}] files\n{'-'*40}"
        )
        check = input("\n\nIs this correct? ( y / n / thread ): \n\n")
        return check

    def new_query(self):
        check = input("\n\tWould you like to start a new query? ( y / n )\n\n")
        return check

    def confirm_new_query(self):
        confirm_new = False
        check = self.new_query()
        while confirm_new is False:
            if check == "y":
                confirm_new = True
                self.cli()
                break
            elif check == "n":
                confirm_new = True
                print("\nExiting...\n")
                sys.exit(0)
            else:
                print("\n\tInvalid input, please enter 'y' or 'n'")
                check = self.new_query()

    def _get_file_data(self, md5: str):
        download_data = grab_download_data(md5)
        return download_data

    def _downloader(self, data: dict):

        filename = f"({data['year']})_{data['title']}"
        filename = file_namer(filename, ".pdf", self.folder_path)

        print(f"\n\t...Downloading {filename}\n")

        url = data["download-link"]
        # print(f"\tDownload Link -> {url}")

        segt_start = perf_counter()

        download_file(url, filename, self.folder_path)

        segt_stop = perf_counter()
        time_elapsed = round(segt_stop - segt_start, 2)
        link = data["download-link"]
        return time_elapsed, link

    def _get_dir_size(self, time_elapsed: float):

        time_elapsed = float(time_elapsed)

        GB = 1024**3
        MB = 1024**2
        KB = 1024

        total_size_bytes = 0
        for filename in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    file_bytes = file.read()
                    total_size_bytes += len(file_bytes)

        total_size_bytes = float(total_size_bytes)
        dl_speed = round(total_size_bytes / MB / time_elapsed, 2)
        if total_size_bytes >= GB:
            total_size = f"{round(total_size_bytes / GB, 2)}-GB @ {dl_speed}-MB/s"
            return total_size
        elif total_size_bytes >= MB and total_size_bytes < GB:
            total_size = f"{round(total_size_bytes / MB, 2)}-MB @ {dl_speed}-MB/s"
            return total_size
        elif total_size_bytes >= KB and total_size_bytes < MB:
            total_size = f"{round(total_size_bytes / KB, 2)}-KB @ {dl_speed}-MB/s"
            return total_size
        else:
            total_size = f"{total_size_bytes}-Bytes @ {dl_speed}-MB/s"
            return total_size

    def thread_grab(self, md5_list: list):

        self.folder, self.folder_path = self.mk_query_folder()

        num_cores = multiprocessing.cpu_count()

        print(f"\nCPU Cores available: {num_cores}\n")

        if self.hold_md5_list == None:
            self.hold_md5_list = md5_list

        def _target_worker(md5: str):
            data = self._get_file_data(md5)
            return data, md5

        def _thread_targets(
            md5_list: list, num_workers: int = 4, target_list: list = None
        ):

            target_start = perf_counter()
            print("\nAcquiring Download Targets...\n")
            if target_list is None:
                target_list = []
            else:
                target_list = target_list

            counter = 0
            temp_workers = num_workers

            fail_list = []
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                thread_targets = [
                    executor.submit(_target_worker, md5_list[md5])
                    for md5 in range(len(md5_list))
                ]

                for future in as_completed(thread_targets):
                    try:
                        data, md5 = future.result()
                        print(f"\t...Data Harvested -> {data['title']}")
                        counter += 1
                        print(f"({counter} / {len(md5_list)}) Targets Aquired")
                        target_list.append(data)

                    except KeyboardInterrupt:
                        print("\n\nUser Interrupt Detected, Restarting...\n")
                        executor.shutdown(wait=False, cancel_futures=True)
                        self.cli()

                    except Exception as e:
                        print(f"\nError,\n{e}")
                        print(
                            f"\nTarget ->{md5_list[thread_targets.index(future)]} Failed to Acquire,\nWill Retry...\n"
                        )
                        fail_list.append(md5_list[thread_targets.index(future)])

            if len(target_list) == len(self.hold_md5_list):
                target_stop = perf_counter()
                target_time = round(target_stop - target_start, 2)
                print(f"\n\tTarget Acquisition Took: {target_time} seconds\n")
                _thread_downloader(target_list)
                return

            if fail_list != []:
                print(f"\nRetrying [{len(fail_list)}] failed targets...\n")
                _thread_targets(
                    fail_list, num_workers=num_workers, target_list=target_list
                )
            else:
                if target_list != []:
                    if len(target_list) < len(self.hold_md5_list):
                        temp_workers += -1
                        if temp_workers == 0:
                            print(
                                f"\nUnhandled Error, {len(md5_list)-len(target_list)} targets failed to acquire\n\treturning to interface..."
                            )
                            self.cli()
                            return
                        elif temp_workers > 0:
                            print(f"\nStarting over with [{temp_workers}]...\n")
                            _thread_targets(md5_list, num_workers=temp_workers)

        def _download_worker(data: dict):
            time_elapsed = self._downloader(data)
            time.sleep(0.5)
            return time_elapsed

        def _thread_downloader(target_list: list):
            max_workers = num_cores
            # if num_cores > 4:
            #     max_workers = 4
            download_start = perf_counter()
            print(f"\nThreadPool Downloading [{len(target_list)}] files...\n")
            time_averages = []
            counter = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                thread_downloads = [
                    executor.submit(_download_worker, target_list[target])
                    for target in range(len(target_list))
                ]

                for future in as_completed(thread_downloads):
                    try:
                        time_elapsed, link = future.result()
                        counter += 1
                        time_averages.append(time_elapsed)
                        average = round(sum(time_averages) / len(time_averages), 2)
                        files_remaining = len(target_list) - counter
                        eta = round(average * files_remaining, 2)
                        if eta > 60:
                            eta_min = eta // 60
                            eta_sec = round(eta % 60, 2)
                            eta = f"{eta_min} minutes, {eta_sec}"
                        print(
                            f"file(s): ({counter} / {len(md5_list)}) Downloaded! [Time Elapsed: {time_elapsed} seconds] [ETA: {eta} seconds] [TOTAL Time Elapsed: {round(sum(time_averages),2)} seconds]"
                        )

                    except KeyboardInterrupt:
                        print("\n\nUser Interrupt Detected, Restarting...\n")
                        executor.shutdown(wait=False, cancel_futures=True)
                        self.cli()

                    except Exception as e:
                        print(f"\nError: \n{e}\n{link}{'*'*30}\n")

            download_stop = perf_counter()
            download_time = round(download_stop - download_start, 2)
            speed_increase = round(sum(time_averages), 2) // download_time
            speed_stamp = self._get_dir_size(download_time)

            if download_time > 60:
                dl_min = download_time // 60
                dl_sec = round(download_time % 60, 2)
                download_time = f"{dl_min} minutes, {dl_sec}"

            print(
                f"\n[{len(os.listdir(self.folder_path))}] Files, [{speed_stamp}] Downloaded -> {self.folder_path}\nTotal Time Elapsed: {download_time} seconds\nRoughly [{speed_increase}x] increase in speed from MultiThreading\n"
            )

        _thread_targets(md5_list)

        self.confirm_new_query()

    def cli(self):

        query = self.first_user_query()
        if query == "help":
            search_help()
            self.cli()

        confirmed_query = False
        check = self.confirm_first_query(query)
        while not confirmed_query:
            if check.lower() == "y" or check.lower() == "yes":
                confirmed_query = True
                break
            elif check == "n" or check.lower() == "no":
                self.cli()
                break
            else:
                print("\n\tInvalid input, please enter 'y' or 'n'")
                check = self.confirm_first_query(query)

        if confirmed_query:

            self.create_search_term(query)

            md5_list = self._get_md5_list()

            check = self.confirm_md5_list(md5_list)
            confirm_list = False
            while not confirm_list:
                if check.lower() == "y" or check.lower() == "yes":
                    confirm_list = True
                    break
                elif check.lower() == "n" or check.lower() == "no":
                    self.cli()
                    break
                elif check.lower() == "thread":
                    self.thread_grab(md5_list)
                    break
                else:
                    print("\n\tInvalid input, please enter 'y' or 'n' or 'thread'")
                    check = self.confirm_md5_list(query)

            if confirm_list:

                self.folder, self.folder_path = self.mk_query_folder()

                counter = 0
                target_list = []
                target_start = perf_counter()
                print("\nAcquiring Download Targets...\n")
                for md5 in md5_list:
                    print("\t...Grabbing Data -> ", end="")
                    data = grab_download_data(md5)
                    counter += 1
                    print(f"{data['title']}")
                    print(f"({counter} / {len(md5_list)}) Targets Aquired")
                    target_list.append(data)
                target_stop = perf_counter()
                target_time = round(target_stop - target_start, 2)
                print(f"\n\tTarget Acquisition Took: {target_time} seconds\n")

                t1_start = perf_counter()

                print(
                    f"\n\tDownloading [{len(md5_list)}] files, for query: [{self.initial_query}] -> {self.folder}\n"
                )

                counter = 1
                time_averages = []
                for data in target_list:

                    time_elapsed, link = self._downloader(data)

                    time_averages.append(time_elapsed)
                    average = round(sum(time_averages) / len(time_averages), 2)
                    files_remaining = len(md5_list) - counter
                    eta = round(average * files_remaining, 2)
                    if eta > 60:
                        eta_min = eta // 60
                        eta_sec = round(eta % 60, 2)
                        eta = f"{eta_min} minutes, {eta_sec}"

                    print(
                        f"file(s): ({counter} / {len(md5_list)}) Downloaded! [Time Elapsed: {time_elapsed} seconds] [ETA: {eta} seconds] [TOTAL Time Elapsed: {round(sum(time_averages),2)} seconds]"
                    )
                    counter += 1

                t1_stop = perf_counter()
                download_time = round(t1_stop - t1_start, 2)
                speed_stamp = self._get_dir_size(download_time)
                print(
                    f"\n[{len(os.listdir(self.folder_path))}] Files, [{speed_stamp}] Downloaded -> {self.folder_path}\nTotal Time Elapsed: {download_time} seconds\n"
                )

                self.confirm_new_query()


if __name__ == "__main__":

    def main_loop():
        main = LibGenGrabber()
        start = False
        while True:
            try:
                if not start:
                    main.cli()
                    start = True
            except KeyboardInterrupt:
                print("\nExiting...\n")
                break
            except Exception as e:
                print(f"\nError: \n{e}\n")
                print(e.with_traceback())
                print("Restarting...\n")
                main.cli()

    main_loop()
