# ethz-document-fetcher
ethz-document-fetcher is an application which can fetch 
and organise all files from ethz websites like
moodle, ilias, polybox and many others.
 
 <img width="791" alt="ethz-document-fetcher-screenshot" src="https://user-images.githubusercontent.com/32932460/102875780-90a30600-4444-11eb-8512-ecaa5fce8e5d.png">
 
 # Features
 * Downloads all new and updated files from specified websites
 * Customisable folder structure
 * You can open files directly from the application
 * GUI and CLI support
 * Highlights difference between the updated and old file (pdf only) 
 
 # Installation
 ## Pre-Build Binaries
 You can download the latest release [here](https://github.com/GeorgOhneH/ethz-document-fetcher/releases/latest).

## Running from source
1) Install python version 3.7 or greater
2) Clone this repo `git clone https://github.com/GeorgOhneH/ethz-document-fetcher.git`
3) Install all dependencies `pip install -r requirements.txt`
4) Run `python main_gui.py` for the gui version or `python main.py` for the cli version

# How to use it
Click [here](./TUTORIAL.md) for a detailed tutorial on how to use the GUI and CLI

# Disclaimer
I can not give any guarantees that the application will work properly.
You should never rely on on the correctness of the application and 
always check the website if the file has any importance.

# Limitations
 ## File Updates
 Due to limitation of specific websites, it's not always possible
 to update files.
 
 Files from these websites will be updated:
 * Polybox
 * one drive
 * nethz
 * ilias
 * moodle
 * dropbox
 
Files from other websites will **not** be updated.<br>
But you can update these files by enabling force 
download.<br>
**Caution:** Force download is very stressful for a website
and should only be rarely used.

## VPN
If a websites require a vpn, the application will not be able
to access this website, unless you enable your vpn.

