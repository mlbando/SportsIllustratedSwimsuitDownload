import os
import json
import requests
from bs4 import BeautifulSoup as bs
import m3u8

def get_model_list():
    """Get the list of all models from the SI Swimsuit catalog"""
    #This is the fetching url I will use, somewhat arbitrary
    get_url = "http://www.si.com/swimsuit/model/nina-agdal/2017/photos"
    page = requests.get(get_url)
    soup = bs(page.content, "html.parser")
    model_list_elements = soup.find("ul", class_=\
    "psuedo-element-list js-psuedo-element-list model-name js-psuedo-list-model-name")
    model_list = model_list_elements.find_all("li")
    return [{"name": model.get_text(), "attr": model.get_text().replace(" ", "-").lower()} \
      for model in model_list]

def get_years_from_page(page_content):
    """get the years the model posed from the webpage"""
    years_ul = bs(page_content, "html.parser").find("ul", class_=\
      "psuedo-element-list js-psuedo-element-list model-year js-psuedo-list-model-year")
    years_li = years_ul.find_all("li")
    return [years.get_text() for years in years_li]

def get_years(model_attr):
    """get the years the model posed"""
    years = ["2014", "2015", "2016", "2017"]
    years_posed = []
    for year in years:
        model_page = requests.get("https://www.si.com/swimsuit/model/" + model_attr \
         + "/" + year +"/photos")
        if model_page.status_code == 200:
            years_posed = get_years_from_page(model_page.content)
            break
    return years_posed

def get_img_urls(page_content):
    """Get the image URLs from the page"""
    soup = bs(page_content, "html.parser")
    img_class = soup.find_all(class_="media-img")
    return [img.find("img").get("src").split("?")[0] for img in img_class]

def get_videoId(page_content):
    """Get the videoId from the video webpage"""
    soup = bs(page_content, "html.parser")
    video_div = soup.find("video", class_="video-js")
    return video_div.get("data-video-id")

def get_assetId_link(videoId):
    """Get the AssetId for the video of choice"""
    pubId = "2157889318001"
    url = "https://secure.brightcove.com/services/mobile/streaming/index/master.m3u8?pubId=" + \
        pubId+"&videoId="+videoId
    page = requests.get(url)
    links = m3u8.loads(page.text)
    return links.playlists[-1].uri

def urls_to_dict():
    """Create the model dictionary and write it to a JSON file"""
    years = ["2014", "2015", "2016", "2017"]
    models = get_model_list()
    model_dict = {}
    #This will be what goes in model_dict["misc"]
    #This format is used so the schema will be the same
    #across the JSON file
    misc_dict = {year: {"photos": [], "videos": []} for year in years}
    url_dict = {}

    for model in models:
        name = model["attr"].replace("-", "_") #Format it to be JSON friendly
        #JSON is supposed to be camelCase but im lazy
        print("Doing " + model["name"] + "\n") #Status update for script
        years = get_years(model["attr"])
        print(years)
        model_dict[name] = {}
        for year in years:
            print("Doing " + year + "\n") #Status update for script
            model_dict[name][year] = {}

            #Run the requests ahead of time so that we can better organize
            #our dictionary structure. I am not sure if every model has a photo
            #set or a video set but we will make sure using this.
            #We will create a dictionary to easily store all of this.
            base_url = "https://www.si.com/swimsuit/model/" + model["attr"] + "/" + year + "/"
            url_dict["photos"] = {"url": base_url + "photos"}
            url_dict["bodypaint"] = {"url": base_url  + "body-paint"}
            url_dict["intimates"] = {"url": base_url + "videos/intimates"}
            url_dict["uncovered"] = {"url": base_url + "videos/uncovered"}
            url_dict["profile"] = {"url": base_url + "videos/profile"}
            url_dict["bodypaint_video"] = {"url": base_url + "videos/body-paint"}
            url_dict["on-set"] = {"url": base_url + "videos/on-set"}
            url_dict["behind-the-scenes"] = {"url": base_url + "vidoes/behind-the-scenes"}
            url_dict["behind-the-tanlines"] = {"url": base_url + "videos/behind-the-tanlines"}

            for key in url_dict.keys():
                url_dict[key]["request"] = requests.get(url_dict[key]["url"])

            #Lets do the Photos
            if url_dict["photos"]["request"].status_code == 200:
                model_dict[name][year]["photos"] = \
                    get_img_urls(url_dict["photos"]["request"].content)

            #Now to get the body painting info
            if (url_dict["bodypaint"]["request"].status_code == 200) and \
            (url_dict["bodypaint"]["request"].content != url_dict["photos"]["request"].content):
                #this is to seperate when there are body paint images along with regular ones
                model_dict[name][year]["bodypaint"] = \
                  get_img_urls(url_dict["bodypaint"]["request"].content)

            #Now lets do the videos intimates, bodypainting, uncovered and profile
            videoIds = []
            for vid in ["uncovered", "intimates", "bodypaint_video", "profile"]:
                if url_dict[vid]["request"].status_code == 200:
                    videoId = get_videoId(url_dict[vid]["request"].content)
                    if videoId not in videoIds:
                        videoIds.append(videoId)
            if len(videoIds) > 0:
                model_dict[name][year]["videos"] = [get_assetId_link(videoId)\
                 for videoId in videoIds]

            #Now lets get the on set, behind the scenes and
            #behind the tan lines videos
            misc_list = ["on-set", "behind-the-scenes", "behind-the-tanlines"]
            for vid in misc_list:
                if url_dict[vid]["request"].status_code == 200:
                    videoId = get_videoId(url_dict[vid]["request"].content)
                    video_url = get_assetId_link(videoId)
                if video_url not in misc_dict[year]["videos"]:
                    misc_dict[year]["videos"].append(video_url)

    model_dict["misc"] = misc_dict

    #This is us writing to the JSON file
    #If you don't want this feature just comment it out.
    with open('SIModelDict.json', 'w') as out:
        json.dump(model_dict, out, sort_keys=True, indent=4, separators=(',', ': '))

    #Go ahead and return the dictionary
    return model_dict

def create_files(model_dict):
    """Create the directories where the files will be downloaded to"""
    basedir = "./SISwim"
    os.system("mkdir " + basedir)
    for name in model_dict.keys():
        os.system("mkdir " + basedir + "/" + name)
        for year in model_dict[name].keys():
            working_directory = basedir + "/" + name + "/" +year
            os.system("mkdir " + working_directory)

def download_images(model_dict):
    """Download all the images from the model dictionary"""
    for model in model_dict.keys():
        for year in model_dict[model].keys():
            print("\n Doing model " + model+ ":" + year)
            working_directory = "./SISwim/" + model + "/" +year
            url_list = model_dict[model][year]["photos"]
            for i in range(0, len(url_list)):
                os.system("wget -P " + working_directory + " " + url_list[i])
            if "bodypaint" in model_dict[model][year]:
                bplist = model_dict[model][year]["bodypaint"]
                for i in range(0, len(bplist)):
                    os.system("wget -P " + working_directory + " " + bplist[i])

def download_videos(model_dict):
    """Download all the videos from the model dictionary"""
    ffmpeg = "ffmpeg -i \""
    params = "\" -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 "
    for name in model_dict.keys():
        for year in model_dict[name].keys():
            basedir = "./SISwim/" + name + "/" + year + "/"
            i = 1
            for video_url in model_dict[name][year]["videos"]:
                os.system(ffmpeg + video_url + params + basedir + "Video" + str(i) + ".mp4")
                i += 1

if __name__ == '__main__':
    with open("SIModelDict.json") as data_file:
        model_dict = json.load(data_file)

    #model_dict = urls_to_dict()
    create_files(model_dict)
    download_images(model_dict)
    download_videos(model_dict)
