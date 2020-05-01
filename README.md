# ethz-document-fetcher
ethz-document-fetcher is a script/program which fetches all files from ethz websites like
 moodle, ilias, polybox and others.
 
 This should allow you to get all documents, exercises and any other file from
 these websites, without having to download and organize them yourself.

## Installation
1. make sure at least python 3.7 is installed
2. cd in the directory
3. run `pip install -r requirements.txt`
4. run `python setup.py`
    
    You can also edit the settings directly in the `settings.config` file
5. run `python main.py` or execute the `run.bat` file

    Note: You can use the `run.bat` file from anywhere
    
## Settings

| Name        | Note           |
| ------------- |-------------|
| username      | LDAP ETH username |
| password      |  LDAP ETH password    |
| base_path |  Absolute path to the directory where the files will be stored      |
| model_path | path to your model |
| loglevel | ERROR or WARNING or INFO or DEBUG |
| allowed_extensions | extension: 'video' for all video types |
| forbidden_extensions | extension: 'video' for all video types |

## Model
The model file is where you specify your folder structure and the websites you want to scrape.

See examples in the models folder. Note that in some examples 

### Start
You need to start with a `folder` or/and `producers`

```yaml
folder:
    ...
producers:
    ...
```

### folder

```yaml
folder:
    name: folder_name
    producers:
      ...
```

### producers

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

### producer
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

#### moodle

```yaml
moodle:
    id: moodle_id
```
#### ilias

```yaml
ilias:
    id: ilias_id
```
#### nethz

```yaml
nethz:
    url: nethz_url
```
#### one_drive

```yaml
one_drive:
    url: one_drive_url
```
#### polybox

```yaml
polybox:
    id: polybox_id
```
#### video portal

```yaml
video_portal:
    department: department
    year: year
    semester: semester
    course_id: course_id
    pwd_username: pwd_username (optional)
    pwd_password: pwd_password (optional)
```
##### custom
You can write your own functions.

The function must be located in the custom folder.

requires `folder_name`, `use_folder: false` or `folder_function`

`folder_function` must also be located in the custom folder

```yaml
custom:
    function: module.to.function
    folder_function: module.to.folder_function (optional)
```
