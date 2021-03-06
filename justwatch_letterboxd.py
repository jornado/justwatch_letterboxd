import json
import time
import requests
from bs4 import BeautifulSoup
from justwatch import JustWatch
import yaml


# See config.yml for configuration options


HOST = "https://letterboxd.com"
LINKS_FNAME = "links.txt"
FILMS_FNAME = "films.json"
SUBS_FNAME = "films_with_subs.json"
SVCS_FNAME = "providers.json"
SUBSCRIPTION = "flatrate"


# Load configuration from YAML file
def load_yaml():
    with open('./config.yml') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


class Service():
    def __init__(self, short_name):
        self.films = set()
        self.name = YAML['services'][short_name]
        self.short_name = short_name

    def __repr__(self):
        return self.name


class Film():
    def __init__(
            self, title, year, director, have_svc=False, services=[],
            link="", rating=""):
        self.title = title
        self.year = year
        self.director = director
        self.services = services
        self.have_svc = have_svc
        self.rating = rating
        if link != "":
            self.link = "{}{}".format(HOST, link)
        else:
            self.link = ""

    def __repr__(self):
        return self.title

    # Create a Film object from a dictionary
    @classmethod
    def from_dict(cls, args):
        f = Film(
            director=args["director"],
            have_svc=args["have_svc"],
            link=args["link"],
            rating=args["rating"],
            services=args["services"],
            title=args["title"],
            year=args["year"],
        )
        return f

    # Create dictionary from a Film object
    @classmethod
    def to_dict(cls, f):
        return {
            "director": f.director,
            "have_svc": f.have_svc,
            "link": f.link,
            "rating": f.rating,
            "services": f.services,
            "title": f.title,
            "year": f.year,
        }


# Fetch contents of a URL
def get_text(path):
    url = "{}{}".format(HOST, path)
    r = requests.get(url)
    return r.text


# Fetch contents of a Letterboxd Watchlist URL
def get_links_text(page):
    url = "/{}/watchlist/page/{}".format(YAML['letterboxd_username'], page)
    return get_text(url)


# Parse the out the links to the films' Letterboxd pages
def get_links(text):
    links = []
    soup = BeautifulSoup(text, 'html.parser')
    movies = soup.find_all(attrs={"class": "linked-film-poster"})

    for movie in movies:
        link = movie.attrs['data-film-slug']
        links.append(link)

    return links


# Part 1
# Fetch all the links of the films from all the Letterboxd Watchlist URLs
# (Up to YAML['max_page'])
def write_links_to_file():
    print("\n...Getting links from {}'s Letterboxd Watchlist...\n".format(
        YAML['letterboxd_username']))

    with open(LINKS_FNAME, "w") as fh:
        for x in range(1, YAML['max_page']):
            time.sleep(1)
            text = get_links_text(x)
            links = get_links(text)

            for idx, link in enumerate(links):
                print("Page {}: {}".format(x, link))
                fh.write("{}\n".format(link))


# Parse out the film's title, year, director, and rating
def get_film_details(text, link):
    soup = BeautifulSoup(text, 'html.parser')
    details = soup.find(id="featured-film-header")
    rating_meta = soup.find("meta", attrs={"name": "twitter:data2"})
    rating = ""

    if rating_meta and rating_meta.get('content'):
        ratings = rating_meta['content'].split(" out of ")
        rating = ratings[0]
    else:
        print("! No rating found")

    return Film(
        title=details.h1.text,
        year=details.small.text,
        director=details.span.text,
        link=link.strip(),
        rating=rating,
    )


# Fetch all the films' Letterboxd URLs
def get_films():
    print("\n\n...Getting film detail pages from Letterboxd...\n")
    films = []

    with open(LINKS_FNAME) as fh:
        for idx, link in enumerate(fh.readlines()):
            print(idx, link.strip())
            text = get_text(link.strip())
            films.append(get_film_details(text, link))
            time.sleep(1)

    return films


# Part 2
# Write all the films data to file
def write_films_to_file():
    films = get_films()
    with open(FILMS_FNAME, "w") as fh:
        fh.write(json.dumps(films, default=Film.to_dict))


# Fetch all the streaming info about each of the films
def get_all_subs():
    print("\n\n...Getting streaming information from JustWatch...\n")
    updated = []
    just_watch = JustWatch(country='US')

    with open(FILMS_FNAME) as fh:
        films = json.loads(fh.read())

        for idx, film_json in enumerate(films):
            film = Film(
                film_json['title'],
                film_json['year'],
                film_json['director'],
                film_json['link'],
                film_json['rating'],
            )
            maybe_updated = process_sub(
                idx, film, just_watch.search_for_item(
                    query=film.title,
                ))

            if maybe_updated is not None:
                updated.append(maybe_updated)
            time.sleep(1)

    return updated


# Part 3
# Write the streaming info for all of the films to file
def write_subs_to_file():
    films = get_all_subs()
    with open(SUBS_FNAME, "w") as fh:
        fh.write(json.dumps(films, default=Film.to_dict))


# Parse out the services this film is streaming on
def process_sub(idx, film, results):
    if (len(results) == 0
            or 'items' not in results
            or len(results['items']) == 0):
        return None

    item = None
    for i in results['items']:
        if (i['title'].lower() == film.title.lower()
                and i['original_release_year']):
            item = i

    if item is None:
        print("! Couldn't find film", film.title)
        return None

    print(idx, item['title'], item['full_path'])

    if 'offers' not in item:
        return None

    services = {offer['package_short_name']
                for offer in item['offers']
                if offer['monetization_type'] == SUBSCRIPTION}

    film.services = list(services)
    for svc in services:
        if svc in YAML['services']:
            film.have_svc = True
            return film

    if len(film.services) == 0:
        return None

    return film


# Fetch all service provider data
def get_all_providers():
    just_watch = JustWatch(country='US')
    with open(SVCS_FNAME, "w") as fh:
        fh.write(json.dumps(just_watch.get_providers()))


# Part 4
# Sort all of our film JSON data by service and output it to file in the
# format: Film Title (Year) - Director
def sort_by_service():
    print("\n\n...Writing results to {}...\n\n".format(
        YAML['output_filename']))
    films = []
    services = {short_name: Service(short_name)
                for short_name in YAML['services'].keys()}

    with open(SUBS_FNAME) as fh:
        films = [Film.from_dict(film)
                 for film in json.loads(fh.read()) if "have_svc" in film]

    for film in films:
        for svc in film.services:
            if svc in services.keys():
                services[svc].films.add(film)

    with open(YAML['output_filename'], "w") as fh:
        for svc in sorted(YAML['services'].keys()):
            fh.write("\n")
            fh.write("{}\n".format(services[svc].name.upper()))

            for film in sorted(
                    services[svc].films, key=lambda film: film.title):
                fh.write("{} ({}) - {}\n".format(
                    film.title, film.year, film.director))


YAML = load_yaml()
write_links_to_file()
write_films_to_file()
write_subs_to_file()
sort_by_service()
