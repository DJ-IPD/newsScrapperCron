import datetime
import logging
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from bs4 import NavigableString, Comment


def str_is_set(string):
    """
    Return False if string is empty True otherwise.
    """
    return string


def is_string(obj):
    """
    Returns True if obj is string False if not.
    """
    return not isinstance(obj, Comment) and isinstance(obj, NavigableString)


def to_utc(timestamp):
    return timestamp.astimezone(tz=timezone.utc)


def set_ist_zone(timestamp):
    timestamp.replace(
        tzinfo=timezone(timedelta(hours=5, minutes=30))
    )


def ist_to_utc(timestamp):
    set_ist_zone(timestamp)
    return to_utc(timestamp)


def remove_duplicate_entries(objects, key, prefer=None):
    """
    Return a new list of objects after removing all duplicate objects based on
    key. If prefer argument is provided, among duplicate objects, the one whose
    obj[prefer] giving False value is discarded
    """
    unique_set = set()
    def is_unique(obj):
        "Return False x[key] is present in set, True otherwise."
        if obj[key] not in unique_set:
            unique_set.add(obj[key])
            return True
        return False

    if prefer is None:
        return list(filter(is_unique, objects))
    
    preferred = {}
    for obj in objects:
        # obj[key] assumed always hashable
        prkey = obj[key]
        if preferred.get(prkey) is None:
            preferred[prkey] = obj
            continue
        if not preferred[prkey][prefer]:
            preferred[prkey] = obj

    return list(preferred.values())
    


def get_headline_details(obj):
    try:
        from datetime import datetime
        timestamp_tag = obj.parent.parent.find(
            "div", {"class": "nstory_dateline"}
        )
        if timestamp_tag is None:
            timestamp = datetime.now()
        else:
            content = timestamp_tag.contents[-1].strip()
            date = content.split("| ")[-1].split(", ")
            if date[-1].isdigit():
                date = " ".join(date)
            else:
                for i in range(1, 10):
                    if date[-i].isdigit():
                        break
                i -= 1
                date = " ".join(date[:-i])
            timestamp = datetime.strptime(
                date + " 05:30",
                "%A %B %d %Y %H:%M"
            )
        return {
            "content": "NA",
            "link": obj["href"].split("?")[0],
            "scraped_at": datetime.utcnow().isoformat(),
            "published_at": ist_to_utc(timestamp).isoformat(),
            "title": "\n".join(filter(
                str_is_set,
                map(
                    str.strip,
                    filter(is_string, obj.children)
                )
            ))
        }
    except KeyError:
        import pdb
        pdb.set_trace()




def get_trending_headlines(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        soup.find("div", { "class": "opinion_opt" }).decompose()
        # Some anchor tags in div[class="lhs_col_two"] are not parsed by the following
        a_tags = soup.find("div", { "class": "hmpage_lhs" }).find_all(
            "a", { "class": "item-title" }
        )
        headlines = remove_duplicate_entries(
            map(get_headline_details, a_tags),
            "link"
        )
        return headlines
    return None



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def run(event, context):
    current_time = 10
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(current_time))

    json_object=json.dumps(
        get_trending_headlines("https://www.ndtv.com/"),
        sort_keys=True,
        indent=4
    )
    print(json_object)
    # with open("sample.json", "w") as outfile:
    #     outfile.write(json_object)
