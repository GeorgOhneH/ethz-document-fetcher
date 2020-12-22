# ethz-document-fetcher
ethz-document-fetcher is an application which can fetch 
and organise all files from ethz websites like
moodle, ilias, polybox and many others.
 
 <img width="791" alt="ethz-document-fetcher-screenshot" src="https://user-images.githubusercontent.com/32932460/102875780-90a30600-4444-11eb-8512-ecaa5fce8e5d.png">
 
 ## Features
 * Easy to add new websites 
 * Downloads all new and updated files from the specified websites
 * Customisable folder structure
 * You can open files directly from the application
 * GUI and CLI support
 
 ## Installation
 ### Pre-Build Binaries
 You can download the latest release [here](https://github.com/GeorgOhneH/ethz-document-fetcher/releases/latest).

### Running from source
1) Install python version 3.7 or greater
2) Clone this repo `https://github.com/GeorgOhneH/ethz-document-fetcher.git`
3) Install all dependencies `pip install -r requirements.txt`
4) Run `python main_gui.py` for the gui version and `python main.py` for the cli version

## How to use it
### First Steps
When you open the app for the first time you will see the minimal example.
Try to run it by pressing the "Run All" button. The setting dialog should pop up,
where you can enter the save path (the save path is the folder 
where everything gets stored). Try to run the minimal example again.
Now it should work.

If you want you can now open the folder at the save path,
either by manuel opening it via the explorer/finder or 
you can right click the "Minimal Example" item and click "Open Folder".
Inside the "Polybox" folder should now be a hello_word.txt

You could have opened the hello_word.txt also directly via the application.
By selecting the Polybox item and clicking the "Folder" button at the bottom.
You should now see the content of the Polybox folder.
Now you can open the hello_word.txt file by double clicking it.

### Adding your own Sites
You can add your own sites by clicking on the "Edit" button and 
double clicking on the "Add Site" item.

Most required values can be found in the url.
But if something is not clear, try to look at the more complicated example
at the menu bar File->Open Presets->...


 
 The main goal of this project is, that you can easily check if
 new exercises (or any other files) have been released/updated.
 
 Existing files from these sites will be updated:
 * Polybox
 * one drive
 * nethz
 * ilias
 * moodle
 * dropbox
 
 Existing files from other sites will **not** be updated.

## Command Line

You can also run the script over the command line. Run `python main.py --help` 
for more info.