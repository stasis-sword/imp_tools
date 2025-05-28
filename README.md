# Imp Tools
A set of thread-reading and -parsing utilities for use with the SA Forums and 
Imp Zone. Also, a web app that uses some of these utilities and others in
order to populate and serve data from a Cloud Firestore database for use with
Imp Zone Game Club, and to serve randomized flag image urls for use within
the Imp Zone forum. For more details on the app, see the README within the /app
directory.

## Setup: 
- [Install python locally](
https://wiki.python.org/moin/BeginnersGuide/Download)
- In a local terminal, run `pip3 install -r requirements.txt`.
- Make a copy of the `config.ini.example` file, named `config.ini`
- (Optional) enter your SA username/password into your `config.ini`. This is 
only visible to your local machine and the SA forums, never sent anywhere 
  else.
  - If you opt not to enter your credentials, the forums will be viewed as an
    unregistered user, enabling all the word filters. I added functionality to
    filter out posts by Adbot, so those shouldn't affect the results.
  - If you are logged in, the utilities will attempt to set your last read
    post in a given thread to where it was prior to running. There's no
    way to mark a thread as completely unread, so if it was previously unread
    it will mark the first post as last read.
  - Logging in is necessary for any utility which accesses a thread that is 
    pay-walled.
- If you are going to use a utility that accesses the IZGC Firebase DB, you'll
need to [generate a service account key](
https://cloud.google.com/docs/authentication/provide-credentials-adc#local-key) 
for the firestore db. If you don't know what this is, you probably shouldn't be 
doing this. Put the resulting JSON file in the `imp_tools` directory and rename 
it to `service_account.json`.

## Usage:
To use a tool, open a terminal such as command.exe or powershell in the
project root. Then, invoke the utility with `python -m utility_name 
(arguments)`. For more information on each tool's usage, call it with `-h` or 
`--help`, e.g. `python -m snipe_countdown -h`.

Currently, tools that accept thread ID numbers as arguments default to the IZGC
thread, but can be overridden (see tool help for exact usage).

---

## Currently working utilities:

### IZGC Trophy Scanner

This utility scans the Imp Zone Game Club thread for posts containing the
trophy images we use to announce having earned a game club trophy.

It prints a list of imps and trophies earned since the previous execution. It 
also saves a record of new trophies earned to the local file 
`trophy_timestamps.json`  and uploads new trophies to the db.

The first time you run this utility, it will add the current end of the thread
to the `config.ini` file and not find any new trophies unless you run all pages
or specify a starting page (see below).

You can run this tool against all pages in the thread with the argument
`--all-pages` or specify a starting page with `--start-page {page number}`.

### Thread Recent Contributor Scanner

This utility will return a list of posters in a given thread, along with the
time stamp of their most recent post. The list is sorted from most recent to 
least recent. 

It accepts a single argument, the ID of the thread to check, and defaults to
the IZGC thread.

### Trophy Migrator

This utility scans the master trophy list at the club website, and creates
games and trophies in the db to match. It is safe to run with existing
trophies.

### Snipe Countdown

This tool will tell you how many posts you must await before a thread can be 
sniped. I was born on a battlefield. Raised on a battlefield. Gunfire, sirens, 
and screams... They were my lullabies...

It accepts a single argument, the ID of the thread to check, and defaults to
the IZGC thread.
