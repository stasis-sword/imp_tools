"""Functionality for reading a thread and parsing out new posts for use"""

import re
import time

from bs4 import BeautifulSoup


class ThreadNotFoundError(Exception):
    pass


def scrape_redirect_url(response, pattern):
    url = response.headers["Location"]
    return int(re.findall(pattern, url)[0])


def scrape_page_number(response):
    return scrape_redirect_url(response, r"pagenumber=(\d+)")


class Thread:
    def __init__(self, *, dispatcher, thread_id):
        self.dispatcher = dispatcher
        self.thread = thread_id
        self.last_read_index = self.get_last_read_index()
        self.page_number = 1
        self.last_post = 0
        self.name = self.get_thread_name()
        self.set_last_read()

    def load_previous_stopping_point(self):
        try:
            thread_attrs = self.dispatcher.config[self.thread]
            self.page_number = int(thread_attrs["page"])
            self.last_post = int(thread_attrs["last_post"])
        except KeyError:
            print("No previous endpoint of thread in config. Saving new end.")
            self.load_end_of_thread()
            self.update_config_values()

    def load_end_of_thread(self):
        self.page_number = self.get_last_page_number()
        self.last_post = self.get_last_post()
        self.set_last_read()

    def get_posts_left_til_snipe(self):
        self.load_end_of_thread()
        posts_left_til_snipe = 40 - self.last_post
        return posts_left_til_snipe

    def get_thread_name(self):
        raw_page = self.get_raw_page(1)
        self.check_thread_is_valid(raw_page)
        self.set_last_read()
        # Strip off " - The Something Awful Forums"
        name = BeautifulSoup(raw_page.text, "html.parser").title.text[:-29]
        return name

    def check_thread_is_valid(self, raw_page):
        if "Specified thread was not found in the live forum" in raw_page.text:
            raise ThreadNotFoundError(f"Thread {self.thread} not accessible.")
        if "Sorry, you must be a registered forums member" in raw_page.text:
            raise ThreadNotFoundError(f"""Thread {self.thread} is paywalled.
            You must enter your login credentials in config.ini to access.""")

    def get_raw_page(self, page_number):
        payload = {
            "threadid": self.thread, "pagenumber": str(page_number)}
        response = self.dispatcher.get_thread(params=payload)

        return response

    def get_page(self, page_number=None):
        page_number = self.page_number if page_number is None else page_number
        raw_page = self.get_raw_page(page_number).text
        if "The page number you requested" in raw_page:
            print("Last page of thread reached.")
            self.page_number -= 1
            return None

        print(f"Parsing posts from {self.name}, "
              + f"page {self.page_number}")
        page = Page(raw_page)
        return page

    def get_last_page_number(self):
        payload = {"threadid": self.thread, "goto": "lastpost"}
        response = self.dispatcher.get_thread(params=payload,
                                              allow_redirects=False)
        return scrape_page_number(response)

    def get_last_post(self):
        raw_page = self.get_raw_page(self.page_number).text
        page = Page(raw_page)
        return len(page.posts)

    def new_posts(self):
        new_posts = []

        while True:
            page = self.get_page()
            if not page:
                # Last page of thread reached, has 40 posts
                break

            new_last_post = len(page.posts)
            new_posts += page.posts[self.last_post:new_last_post]
            if new_last_post < 40:
                # Last page of thread reached
                self.last_post = new_last_post
                break

            self.page_number += 1
            self.last_post = 0
            # Wait so as not to flood server with requests
            time.sleep(1)

        if new_posts:
            self.update_config_values()
        else:
            print(f"No new posts in thread {self.thread}.")

        self.set_last_read()
        return new_posts

    # This method assumes that the thread has been read at some point.
    # If the thread is totally unread, it will set the last-read marker such
    # that the whole first page has been read
    def get_last_read_index(self):
        if not self.dispatcher.logged_in:
            return None

        response = self.dispatcher.get_thread(
            params={"threadid": self.thread, "goto": "newpost"},
            allow_redirects=False)

        try:
            post_number = scrape_redirect_url(response, r"#pti(\d+)")
        except IndexError:
            # Noseen behaves exactly the same for threads that are entirely
            # unread and threads that have no unread replies, if the thread is
            # only one page long. So, we guess the page has been fully read :/
            post_number = 40

        posts_per_page = scrape_redirect_url(response, r"perpage=(\d+)")
        page_number = scrape_page_number(response)

        index = ((posts_per_page * (page_number - 1)) + post_number - 1)
        return index

    def set_last_read(self):
        if self.dispatcher.logged_in and self.last_read_index:
            self.dispatcher.get_thread(params={
                "action": "setseen",
                "threadid": self.thread,
                "index": self.last_read_index
            })

    def update_config_values(self):
        self.dispatcher.config[self.thread] = {
            "page": self.page_number,
            "last_post": self.last_post
        }
        self.dispatcher.save_config()


class Page:
    def __init__(self, raw_page):
        self.soup = BeautifulSoup(raw_page, "html.parser")
        self.thread = self.soup.body["data-thread"]
        self.posts = []
        self.unread_posts = []
        self.read_posts = []
        self.parse_posts()

    # Posts will currently all return as unread if the user does not have the
    # option selected to mark read posts in a different color.
    def parse_posts(self):
        raw_posts = self.soup.find_all("table")
        for raw_post in raw_posts:
            post = Post(raw_post)
            if post.username == "Adbot":
                continue
            self.posts.append(post)
            if post.unread():
                self.unread_posts.append(post)
            else:
                self.read_posts.append(post)

    def number(self):
        return int(self.soup.find("option", selected="selected")["value"])


class Post:
    CELL_TAG = "td"

    def __init__(self, raw_post):
        self.raw_post = raw_post

        self.cells = self.raw_post.find_all(self.CELL_TAG)
        self.username = self.raw_post.find(self.CELL_TAG, "userinfo").dt.text
        # id attribute has "post" at the beginning, so we strip it
        self.post_id = self.raw_post["id"][4::]
        self.index = self.raw_post["data-idx"]
        self.body = self.raw_post.find(self.CELL_TAG, "postbody")

    def text(self):
        return self.body.get_text()

    def unread(self):
        # Read posts have a first "tr" with class "seen1" or "seen2"
        # Unread posts have "altcolor1" or "altcolor2"
        # Use matching for unread so if this breaks all posts default to read
        return "altcolor" in self.raw_post.tr["class"][0]

    def timestamp(self):
        try:
            raw = self.raw_post.find(self.CELL_TAG, "postdate").text
            # Remove the # and ? signs and extra whitespace
            return raw.translate({35: None, 63: None}).strip()
        except AttributeError:
            return "Parsing error. Could not parse timestamp."

    def get_avatar_url(self):
        # Always grabs actual avatar image. May need special case for Fungah!
        try:
            return self.raw_post.find(self.CELL_TAG, "userinfo").img["src"]
        # User has no avatar
        except TypeError:
            return ""

    def remove_quotes(self):
        quotes = self.body.find_all("div", "bbc-block")
        for quote in quotes:
            quote.decompose()

    def image_urls(self):
        images = self.body.find_all("img")
        return list(map(lambda img: img["src"], images))

    def link(self):
        return "https://forums.somethingawful.com/showthread.php?goto=post&" \
               f"postid={self.post_id}#post{self.post_id}"
