# How to use it
## First Steps
When you open the app for the first time you will see the minimal example.
Try to run it by pressing the "Run All" button.

<img width="661" alt="init" src="https://user-images.githubusercontent.com/32932460/102920181-886db980-448a-11eb-9609-a6f4b638a2ca.PNG">

The setting dialog should pop up,
where you can enter the save path (the save path is the folder 
where everything gets stored).

<img width="381" alt="init settings" src="https://user-images.githubusercontent.com/32932460/102920260-b5ba6780-448a-11eb-89d1-7ab87c98a353.PNG">

Try to run the minimal example again.
Now it should work.

<img width="688" alt="right" src="https://user-images.githubusercontent.com/32932460/102920864-ba335000-448b-11eb-9cf1-78f408cd8e3c.PNG">

If you want you can now open the folder at the save path,
either by manuel opening it via the explorer/finder or 
you can right click the "Minimal Example" item and click "Open Folder".

<img width="661" alt="open folder1" src="https://user-images.githubusercontent.com/32932460/102920484-25c8ed80-448b-11eb-8850-a6d650d06d06.PNG">

Inside the "Polybox" folder should now be a hello_word.txt

You could have opened the hello_word.txt also directly via the application.
By selecting the Polybox item and clicking the "Folder" button at the bottom.

<img width="688" alt="open folder2" src="https://user-images.githubusercontent.com/32932460/102920675-6a548900-448b-11eb-946c-9b597d06269f.PNG">

You should now see the content of the Polybox folder.
Now you can open the hello_word.txt file by double clicking it.

## Adding your own Sites
You can add your own sites by clicking on the "Edit" button

<img width="688" alt="12" src="https://user-images.githubusercontent.com/32932460/102921071-10a08e80-448c-11eb-9656-038afa00fd48.PNG"> 
 
and then double clicking on the "Add Site" item.

<img width="315" alt="add1" src="https://user-images.githubusercontent.com/32932460/102921187-40e82d00-448c-11eb-9d9c-c9580a5e1a50.PNG">

In this tutorial we will add another shared polybox folder.<br>
We want to add this link: https://polybox.ethz.ch/index.php/s/UFfLsy8gX84eLw1

<img width="327" alt="3" src="https://user-images.githubusercontent.com/32932460/102981863-e55c8480-4509-11eb-8c57-062a5a273d80.PNG">

After you inserted the right values you can press the Ok button.<br>
The items support drag'n drop, so that the can be rearranged.

![ezgif-7-18824102d4c6](https://user-images.githubusercontent.com/32932460/102984118-5fdad380-450d-11eb-9a63-e1de59092bcc.gif)

Now you can save the template and run it again

<img width="668" alt="Unbenannt" src="https://user-images.githubusercontent.com/32932460/102984596-1b9c0300-450e-11eb-80a0-65681353da6a.PNG">

> Note: You now have 2 Polybox folder, this is because 
the application never deletes files.

>Note: If you change the order or rename a item,
all files from these websites will be downloaded again.

For are more detailed explanation of every available website 
and there settings click [here](./SITES.md)

Also if you are lucky there might be already a preset template 
for your department and semester at the menu bar File->Open Presets->...
> Note: The preset templates don't store any passwords, that means you have to 
replace every "INSERT PASSWORD" with the correct password.

<img width="668" alt="preset" src="https://user-images.githubusercontent.com/32932460/102985349-52bee400-450f-11eb-9c7e-8f9599952bbf.PNG">

## Command Line Interface (CLI)
If you are using the GUI there is no reason to use the CLI and you can skip this section.

The CLI is in no way faster then the GUI, but it can be useful 
if you want to run the process on a server and sync the folder with your pc.

To be able to run the CLI you need to be running from source (See the README).
The pre-build binaries don't support the CLI.

Firstly run `python main.py --help`, this will show your all the possible options

```
usage: main.py [-h] [--loglevel {ERROR,WARNING,INFO,DEBUG}]
               [--check_for_updates | --no-check_for_updates] [--template_path TEMPLATE_PATH]
               [--username USERNAME] [--password PASSWORD] [--base_path BASE_PATH]
               [--allowed_extensions [ALLOWED_EXTENSIONS ...]]
               [--forbidden_extensions [FORBIDDEN_EXTENSIONS ...]]
               [--keep_replaced_files | --no-keep_replaced_files]
               [--highlight_difference | --no-highlight_difference]
               [--force_download | --no-force_download] [--conn_limit CONN_LIMIT]
               [--conn_limit_per_host CONN_LIMIT_PER_HOST]

optional arguments:
  -h, --help            show this help message and exit
  --loglevel {ERROR,WARNING,INFO,DEBUG}
  --check_for_updates
  --no-check_for_updates
  --template_path TEMPLATE_PATH
  --username USERNAME
  --password PASSWORD
  --base_path BASE_PATH
  --allowed_extensions [ALLOWED_EXTENSIONS ...]
  --forbidden_extensions [FORBIDDEN_EXTENSIONS ...]
  --keep_replaced_files
  --no-keep_replaced_files
  --highlight_difference
  --no-highlight_difference
  --force_download
  --no-force_download
  --conn_limit CONN_LIMIT
  --conn_limit_per_host CONN_LIMIT_PER_HOST
```

Every argument is optional. The reason behind this is, that it will 
try to read the values first from the setting file, which is generated by the GUI.
So it's possible, that everything works on your local pc, but not on your server.
We recommend to explict set each possible setting.

The only argument which is not in the GUI settings is the template_path.
You can create the template via the GUI and then set the correct template_path.

>Note: The base_path argument is the save path from the GUI settings

