# Imp Tools
A set of thread-reading and -parsing utilities for use with the SA Forums and 
Imp Zone. 

## Setup: 
- [Install python locally](https://wiki.python.org/moin/BeginnersGuide/Download)
- In a local terminal, run `pip3 install -r requirements.txt`.
- Make a copy of the `config.ini.example` file, named `config.ini`
- (Optional) enter your SA username/password into your `config.ini`. This is 
only visible to your local machine and the SA forums, never sent anywhere 
  else.
  - If you opt not to enter your credentials, the forums will be viewed as an
    unregistered user, enabling all the word filters. I added functionality to
    filter out posts by Adbot, so those shouldn't affect the results.
  - If you are logged in, the utilities will attempt to set your last read
    post in a given thread to where it was prior to running them. There's no
    way to mark a thread as completely unread, so if it was previously unread
    it will mark the first post as last read.
  - Logging in is necessary for any utility which accesses a thread that is 
    paywalled.
- If you are going to use a utility that accesses the IZGC Firebase DB, you'll
need to [generate a service account key](https://cloud.google.com/docs/authentication/provide-credentials-adc#local-key). 
Put the resulting JSON file in the `imp_tools` directory and rename it to 
`service_account.json`.

---

## Currently working utilities:

### IZGC Trophy Scanner

This utility scans the Imp Zone Game Club thread for posts containing the
trophy images we use to announce having earned a game club trophy.

To run, call `python read_izgc_trophies.py` from the project root. This tool
prints a list of imps and trophies earned since the previous execution. It also
saves a record of new trophies earned to the local file
`trophy_timestamps.json`

The first time you run this utility, it will add the current end of the thread
to the `config.ini` file and not find any new trophies unless you run all pages
or specify a starting page (see below).

You may run this command against all pages in the thread with
`python read_izgc_trophies.py --all-pages`.

You may also run this command starting at a set page with
`python read_izgc_trophies.py --start-page {page number}`.

### Thread Recent Contributor Scanner

This utility will return a list of posters in a given thread, along with the
time stamp of their most recent post. The list is sorted from most recent to 
least recent.

To run, call `python recent_contributors.py` and put in the thread id of the 
thread when prompted.