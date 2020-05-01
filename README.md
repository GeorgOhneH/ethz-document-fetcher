# ethz-document-fetcher
ethz-document-fetcher is a script/program which fetches all files from ethz websites like
 moodle, ilias, polybox and others.
 
 This should allow you to get all documents, exercises and any other file from
 these websites, without having to download and organize them yourself.

## Installation
1. make sure at least python 3.7 is installed
2. cd in the directory
3. run `pip install -r requirements.txt`
4. run `python setup.py` (This will ask you to input your settings and create a `settings.config`)
    
    You can also edit the settings directly in the `settings.config` file
5. run `python main.py` or execute the `run.bat` file (Windows only)

    Note: You can use the `run.bat` file from anywhere
    
## Settings
The settings in your `settings.config` file 

| Name        | Note           |
| ------------- |-------------|
| username      | LDAP ETH username |
| password      |  LDAP ETH password    |
| base_path |  Absolute path to the directory where the files will be stored      |
| template_path | path to your template |
| loglevel | ERROR or WARNING or INFO or DEBUG |
| allowed_extensions | Is a list. Add 'video' for all video types extensions|
| forbidden_extensions | Is a list. Add 'video' for all video types extensions|

## Template
The template file is where you specify your folder structure and the websites you want to scrape.

See examples in the template folder. Note that in some examples some values are `null`.
These must be replaced with there actual values if you want them to be used.

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
Global parameters, all optional

if no folder name is giving, it takes the title of the website

```yaml
<producer>:
    allowed_extensions: [extension1, extension2, pdf, ...]
    forbidden_extensions: [extension1, extension2, pdf, ...]
    folder_name: folder_name
    use_folder: (true or false, default true)
    producers:
        ...
    folder:
        ...
      
```

#### Moodle

```yaml
moodle:
    id: moodle_id
```
#### Ilias

```yaml
ilias:
    id: ilias_id
```
#### nethz

```yaml
nethz:
    url: nethz_url
```
#### One Drive

```yaml
one_drive:
    url: one_drive_url
```
#### Polybox

```yaml
polybox:
    id: polybox_id
    password: NUS2020
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




