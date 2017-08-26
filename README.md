This is a set of scripts that will download all the videos
and images from the 2017 Sports Illustrated Swimsuit online 
catalog. This catalog contains years 2014 through 2017.
To run, clone the repo and run:

```
python3  downloader
```

Be sure to run the script in the directory where you want the files saved.
The script will create a folder structure: `SISwim/model_name/year`.
All videos and images for that model will be saved in the 
corresponding folder. The script also grabs the videos
on set, behind the tanlines and behind the scenes which 
will be saved in `/SISwim/misc/year`.

There is also a JSON file containing all the videos and images
structured by model name, year, video or image and the download links.
The videos are not regular MPEG but are HTTP stream files so just keep
that in mind.

If you have questions or comments shoot me a message. If you would 
like to add a feature just make a pull request. If this repository
brought you any joy please star it and follow me on my 
website [www.mlbando.com](www.mlbando.com).