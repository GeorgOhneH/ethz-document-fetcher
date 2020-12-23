# Sites

## Overview

| Module Name | Requires Password | Has File Updates | Note   |
|-------------|------------------|--------------| -----  |
|[dropbox](#dropbox)|     :x:  |   :heavy_check_mark:  |        |
|[ilias](#ilias)| :heavy_check_mark: | :heavy_check_mark: |        |
|[link_collector](#link-collector)| :x: | :x: |Is complicated, but very powerful|
|[moodle](#moodle)| :heavy_check_mark: | :heavy_check_mark: |        |
|[nethz](#nethz)| :x: | :heavy_check_mark: | It works for all Apache Server |
|[one_drive](#one-drive)| :x: | :heavy_check_mark: |        |
|[polybox](#polybox)| :x: | :heavy_check_mark: | Supports public and private folders |
|[video_portal](#video-portal)| :heavy_check_mark: | :x: |        |

> Note: Most urls on this page don't work. They are only there to show how they should look.

## Dropbox


| Parameter Name | Comment |
|-------------|------------------|
|Url| The url should look something like this:<br>https://www.dropbox.com/sh/maqgw1rp2utf89k/AACMGK0P8ltSwI9qxWZxz_WXa  |

## Ilias

| Parameter Name | Comment |
|-------------|------------------|
|ID| Example url: https://ilias-app2.let.ethz.ch/ilias.php?ref_id=187834&cmd=view<br>The id would be: 187834 |

## Link Collector

The link collector module can be very complicated, but it's very powerful.

The idea of the module:
1) Collect every link on a website
2) Filter out which you want
3) Download them

To understand how it exactly works let's look at an example:

Consider this url https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/
and we want to download every exercise and there solutions.

If we click for an example on the first exercise, we will be directed to
https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/serie/Serie01.pdf,
on the second to 
https://metaphor.ethz.ch/x/2020/fs/401-0232-10L/serie/Serie02.pdf.

We find out that only the number in the url changes.
We could not apply a filter if this wasn't the case.

Now we need a filter which let's only the exercise url through.
The link collector uses regex for this. 
If you are unfamiliar with regex you can look at [this](https://github.com/ziishaned/learn-regex).

The regex expression which works for these urls looks like this `.*serie/Serie([0-9]+)\.pdf`.
The parenthesis are python specified and are used to group specific string so we can reuse them
in our naming scheme. In the example the parenthesis enclose the number of the exercise.

> Note: We use the `.*` at the beginning, because we want to match the whole link. 
> Else the the beginning of the link get copied to the folder and file name.

Now it's time to chose how we should call our files and in which directory we should but them.
In this example we want to but each exercise and solution in a separate Folder.

We call this folder `Week \1`, where `\1` is the first group of the regex, which in this example
is the number of the specific exercise. The link collector uses for this the [re.sub](https://docs.python.org/3/library/re.html#re.sub)
function and is the reason why we write it like this.

We call the file `Exercise \1`, where `\1` has the same reason as above.
We could also name it `<name>`, because `<name>` will be replaced with the name of the link, 
which in our case would be more or less the same as the first option.

Everything together we get the exercise filter:

| Parameter Name | Value |
|-------------|------------------|
|Pattern| `.*serie/Serie([0-9]+)\.pdf`|
|Folder Name|`Week \1`|
|File Name|`Exercise \1`|

And similar for the solution filter we get:

| Parameter Name | Value |
|-------------|------------------|
|Pattern| `.*serie/Loesung([0-9]+)\.pdf`|
|Folder Name|`Week \1`|
|File Name|`Solution \1`|


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
To find the right url is not always easy and sometimes even impossible.

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
|Password| Some shared folders need a Password. You can ignore this field if it's a private folder |

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