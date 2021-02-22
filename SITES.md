# Sites

## Overview

| Module Name | Requires Password | Has File Updates | Note   |
|-------------|------------------|--------------| -----  |
|[dropbox](#dropbox)|     :x:  |   :heavy_check_mark:  |        |
|[google_drive](#google-drive)|     :x:  |   :heavy_check_mark:  |        |
|[ilias](#ilias)| :heavy_check_mark: | :heavy_check_mark: |        |
|[link_collector](#link-collector)| :x: | :x: |Is complicated, but very powerful|
|[moodle](#moodle)| :heavy_check_mark: | :heavy_check_mark: |        |
|[nethz](#nethz)| :x: | :heavy_check_mark: | It works for all Apache Server |
|[one_drive](#one-drive)| :x: | :heavy_check_mark: |        |
|[polybox](#polybox)| :x: | :heavy_check_mark: | Supports public and private folders |
|[video_portal](#video-portal)| :heavy_check_mark: | :x: |        |

> Note: Most urls on this page don't work. They are only there to show how they should look.

> Note: It might help to look at the preset examples (Menu Bar->File->Open Presets->...)

## Dropbox

| Parameter Name | Comment |
|-------------|------------------|
|Url| The url should look something like this:<br>https://www.dropbox.com/sh/maqgw1rp2utf89k/AACMGK0P8ltSwI9qxWZxz_WXa  |

## Google Drive


| Parameter Name | Comment |
|-------------|------------------|
|ID| Example url: https://drive.google.com/drive/folders/1bcHP2jqtMksjhEdpY2wdeH8MqziF4CQM <br>The id would be: 1bcHP2jqtMksjhEdpY2wdeH8MqziF4CQM |

## Ilias

| Parameter Name | Comment |
|-------------|------------------|
|ID| Example url: https://ilias-app2.let.ethz.ch/ilias.php?ref_id=187834&cmd=view <br>The id would be: 187834 |

## Link Collector

The link collector module can be very complicated, but it's very powerful.

The idea of the module:
1) Collect every link on a website
2) Filter out which you want
3) Download them

To understand how it exactly works let's look at an example:

Consider this url https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/.
Our goal is it to download each exercise and solutions.

If we click on the first exercise, we will be directed to
https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/serie/Serie01.pdf,
on the second to 
https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/serie/Serie02.pdf.

We find out that only the number in the url changes.
If something like this does not exist, then we can't apply a filter and this module would be useless.

Now we need a to filter the exercise links.
The link collector uses regex for this. 
If you are unfamiliar with regex you can look at [this](https://github.com/ziishaned/learn-regex).

The regex expression which works for these urls looks like this `.*serie/Serie([0-9]+)\.pdf`.
The parentheses are python specified and are used to group a specific string so we can reuse them
in our naming scheme. In the example the parentheses enclose the number of the current exercise.

> Note: We use the `.*` at the beginning, because we want to match the whole link.

Now it's time to choose how we should call our files and in which directory we should but them.
In this example we but each exercise and solution in a separate Folder.

We call this folder `Week \1`, where `\1` is the first group of the regex, which in this example
is the number of the specific exercise. The link collector uses for this the [re.sub](https://docs.python.org/3/library/re.html#re.sub)
function and is the reason why we write it like this.

We call the file `Exercise \1`, where `\1` has the same meaning as above.
We could also name it `<name>`, because `<name>` will be replaced with the name of the link, 
which in our case would be more or less the same as the first option.

Everything together we get the exercise filter:

| Parameter Name | Value |
|-------------|------------------|
|Pattern| `.*serie/Serie([0-9]+)\.pdf`|
|Folder Name|`Week \1`|
|File Name|`Exercise \1`|
|Link Modifier||

And similar for the solution filter we get:

| Parameter Name | Value |
|-------------|------------------|
|Pattern| `.*serie/Loesung([0-9]+)\.pdf`|
|Folder Name|`Week \1`|
|File Name|`Solution \1`|
|Link Modifier||

The 'Link Modifier' is an optional field, which can alter the link.
It works exactly the same as the 'Folder Name' and 'File Name' fields and
is not needed in this example.


The Header options is for custom request headers, but it's not needed in most use cases.

## Moodle

| Parameter Name | Comment |
|-------------|------------------|
| ID|Example url: https://moodle-app2.let.ethz.ch/course/view.php?id=13642<br>The id would be: 13642 |
| Process External Links | If an external links points to a polybox, onedrive or zoom url, it will try to fetch these files too|
| Keep Section Order | Keeps the section order like it is on moodle |

## nethz

All the n.ethz student websites run on Apache, 
which means that this module not only works on n.ethz websites, 
but on all Website which use Apache.

| Parameter Name | Comment |
|-------------|------------------|
|Url| see Url section |

### Url
Finding the right url is not always easy and sometimes even impossible.

You are looking for a url which returns something like this:

<img width="394" alt="nethz" src="https://user-images.githubusercontent.com/32932460/103020467-b9142880-4548-11eb-9b7d-081c0fde4b83.PNG">

If this is the case you found the directory where the owner stores his files.
But sometimes the naming scheme is bad or it contains other files that you don't want, 
then you are better of with the link_collector.

**How to find the url**: The easiest way to do it is by opening a file you want to download
and then removing the last part of the url.
For example from `.../slides/DT_03.10.19.pdf` to `.../slides/`

> Note: This does not always work and then it's often just easier to use the link_collector


## One Drive

| Parameter Name | Comment |
|-------------|------------------|
|Url| The url should look something like this:<br>https://onedrive.live.com/?authkey=!APFF5FVMjgYLHL8&id=B8180E91F886EA8A!155601  |

## Polybox
This module supports public and private folders.

A public url looks like this: <code>polybox.ethz.ch/index.php/s/<b>SU2lkCtdoLH3X1w</b></code><br>
A private url looks like this: <code>polybox.ethz.ch/index.php/apps/files/?fileid=<b>2075289019</b></code>
<br>
where the corresponding ids are bold

| Parameter Name | Comment |
|-------------|------------------|
|ID| |
|Type| Type s is for shared folder and Type f is for private folder|
|Password| Some shared folders need a password. You can ignore this field if it's a private folder |

> Note: To use the private folders you need to set your username and password in the settings

## Video Portal

Example url: https://video.ethz.ch/lectures/d-itet/2019/spring/227-0002-00L.html

| Parameter Name | Value from Example Url |
|-------------|------------------|
|Department| d-itet |
|Year| 2019 |
|Semester| spring |
|Course ID| 227-0002-00L |
|Series Username| Only required if the website asks for it. Can be ignored if the ETH Username is required |
|Series Password| Only required if the website asks for it. Can be ignored if the ETH Password is required |

> Note: Some videos require your ETH username and ETH password. 
>To download these videos you need to set your username and password in the settings. 


## Custom
If a website is too complicated for the other modules, 
you can code your own functions to handle it.
  