# Sites

## Overview

| Module Name | Requires Password | Has File Updates | Note   |
|-------------|------------------|--------------| -----  |
|[dropbox](#dropbox)|     :x:  |   :heavy_check_mark:  |        |
|[ilias](#ilias)| :heavy_check_mark: | :heavy_check_mark: |        |
|[link_collector](#link_collector)| :x: | :x: |Is complicated to use, but very powerful|
|[moodle](#moodle)| :heavy_check_mark: | :heavy_check_mark: |        |
|[nethz](#nethz)| :x: | :heavy_check_mark: | It's basically for a Apache Server |
|[one_drive](#one-drive)| :x: | :heavy_check_mark: |        |
|[polybox](#polybox)| :x: | :heavy_check_mark: | Supports public and private folders |
|[video_portal](#video-portal)| :heavy_check_mark: | :x: |        |

> Note: Most urls don't work. They are only there to show how they should look


Basic Headers

## Dropbox


| Parameter Name | Comment |
|-------------|------------------|
|Url| The url should look something like this:<br>https://www.dropbox.com/sh/maqgw1rp2utf89k/AACMGK0P8ltSwI9qxWZxz_WXa  |

## Ilias

| Parameter Name | Comment |
|-------------|------------------|
|ID| Example url: https://ilias-app2.let.ethz.ch/ilias.php?ref_id=187834&cmd=view<br>The id would be: 187834 |

## link_collector



## Moodle

| Parameter Name | Comment |
|-------------|------------------|
| ID|Example url: https://moodle-app2.let.ethz.ch/course/view.php?id=13642<br>The id would be: 13642 |
| Process External Links | If an external links points to a polybox, onedrive or zoomlink, it will try to fetch these files also |
| Keep Section Order | Keeps the section order like it is on moodle |

## nethz

All the n.ethz student websites run on Apache, which means every folder from Apache can be downloaded.

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


## Video Portal