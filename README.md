# ethz-document-fetcher
ethz-document-fetcher is a script/program which fetches all files from ethz websites like
 moodle, ilias, polybox and others.
 
 This should allow you to get all documents, exercises and any other file from
 these websites, without having to download and organize them yourself.
 
 The main goal of this project is, that you can easily check if
 new exercises (or any other files) have been released.
 
 **IMPORTANT**: The default behavior of the fetcher does **not** replace files,
 which were updated (and have kept the same name) on the original website.
 <br>Exceptions: Polybox, one drive, nethz, ilias, moodle

## Installation
1. Make sure at least [python](https://www.python.org/downloads/) 3.7 is installed
2. Install [git](https://git-scm.com/downloads) if you haven't
3. Open a console in the directory where you want to install the fetcher
4. run `git clone https://github.com/GeorgOhneH/ethz-document-fetcher.git`
5. run `cd ethz-document-fetcher`
6. run `pip install -r requirements.txt`
7. run `python setup.py` (This will ask you to input your
 settings and create a `settings.config` file)
    
    You can also edit the settings directly in the `settings.config` file
8. run `python main.py` (All) or double click the `run.bat` file (Windows only)
or double click the `run.sh` file (Mac/Linux only)

    Note: You can use the `run.bat` and `run.sh` files from any directory
    
## Settings
The settings in your `settings.config` file:

| Name        | Type      | Default |  Note           |
| ------------- | -------- | --------   |-------------|
| username      | String | None | LDAP ETH username. Is optional, but all sites, which require your username and password won't work.|
| password      | String | None |LDAP ETH password. Is optional, but all sites, which require your username and password won't work.    |
| base_path | Path |current working directory |  Absolute path to the directory where the files will be stored      |
| template_path | Path| path to an example |path to your template |
| loglevel | String| INFO |ERROR or WARNING or INFO or DEBUG |
| allowed_extensions |List | [] | A list of extension which are allowed to be downloaded. A empty list means that everything is allowed. Add 'video' for all video types extensions|
| forbidden_extensions | List| [video] | A list of extension which are prohibited to be downloaded. Add 'video' for all video types extensions|
| keep_replaced_files | Bool| False | If a file gets updated, it will be renamed, so it doesn't get overwritten. If the file is pdf, a new pdf will be created that will highlight the difference between the new and old file.  |

To change the settings run `python setup.py`
<br>
Note: You can also give the settings directly over the command line. Run `python main.py --help` for more infos.

## Template
The template file is where you specify your folder structure and the websites you want to scrape.

See examples in the template folder. Note that in some examples some values are `null`.
These must be replaced with there actual values if you want the producer to be used.

### Start
You need to start with a `folder` or/and `producers`

```yaml
folder:
    ...
producers:
    ...
```

### Folder

```yaml
folder:
    name: folder_name
    producers:
      ...
```

### Producers

```yaml
producers:
    - <producer>
        ...
    - <producer>
        ...
    - <producer>
        ...
    ...
```

### Producer
Parameters for every producer, all optional

if no folder name is given, it takes the title of the website

```yaml
<producer>:
    allowed_extensions: [extension1, extension2, pdf, ...]
    forbidden_extensions: [extension1, extension2, pdf, ...]
    folder_name: folder_name
    use_folder: (true or false, default: true)
    ...
    producers:
        ...
    folder:
        ...
      
```

#### Moodle

```yaml
moodle:
    id: moodle_id
    use_external_links: (true or false, default: true) (optional)
    ...
```
#### Ilias

```yaml
ilias:
    id: ilias_id
    ...
```
#### nethz

```yaml
nethz:
    url: nethz_url
    ...
```
#### One Drive

```yaml
one_drive:
    url: one_drive_url
    ...
```
#### Polybox

```yaml
polybox:
    id: polybox_id
    password: password (optional)
    ...
```
#### Video Portal

```yaml
video_portal:
    department: department
    year: year
    semester: semester
    course_id: course_id
    pwd_username: pwd_username (optional)
    pwd_password: pwd_password (optional)
    ...
```
#### Custom
You can write your own functions.

```python
async def your_function(session, queue, base_path, **kwargs):
```

The function must be located in the custom folder.

The function should parse the website and give the queue a dictionary 
 `queue.put({url: your_url, path: path_to_file})` with the url where
  the document can be downloaded.

The producer requires `folder_name`, `use_folder: false`
 or a `your_folder_name_function`

`your_folder_name_function` should return the name of the folder

Note: the `your_folder_name_function` must also be located in the custom folder

```python
async def your_folder_name_function(session, queue, base_path, **kwargs):
```

```yaml
custom:
    function: module.to.your_function
    folder_function: module.to.your_folder_name_function (optional)
    kwarg1: kwarg1_value1
    kwarg2: kwarg1_value2
```

## Contribution
If you made your own template, consider making a pull request so other people can use it.
Please replace all passwords and sensitive values with `null`.

### Writing your own module
You will need 2 functions, `producer` and `get_folder_name`.
If your module needs a one time login then the `login` 
function should also be implemented.

The rest will be handled internally.

#### producer
```python
async def producer(session, queue, base_path, **kwargs):
```
The producer function should parse the website and give the queue a dictionary 
 `queue.put({url: your_url, path: path_to_file})` with the url where
  the document can be downloaded.

#### get_folder_name
```python
async def get_folder_name(session, **kwargs):
```
`get_folder_name` should return the name of the folder
 #### login
```python
async def login(session):
```
The login function, which will only be called once.




