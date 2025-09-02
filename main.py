# partially stolen from https://medium.com/@alf.19x/letterboxd-friends-ranker-simple-movie-recommendation-system-80a38dcfb0da

from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
from time import sleep

DOMAIN = "https://letterboxd.com"
movies_dict = {}
friends_dict = {}
hmn_movies_dict = {}
friendlist = []
username = None

#converts star ratings in page to real numbers
def transform_ratings(some_str):
    stars = {
        "★": 1,
        "★★": 2,
        "★★★": 3,
        "★★★★": 4,
        "★★★★★": 5,
        "½": 0.5,
        "★½": 1.5,
        "★★½": 2.5,
        "★★★½": 3.5,
        "★★★★½": 4.5
    }
    try:
        return stars[some_str]
    except:
        return -1
    
def scrape_films(username):
    idlist = []
    titlelist = []
    ratinglist = []
    likedlist = []
    linklist = []
    userlist = []
    url = DOMAIN + "/" + username + "/films/"

    print(f"Scraping films from {username}'s profile...")

    #starts while loop to handle pagination
    while True:
        url_page = requests.get(url)
        soup = BeautifulSoup(url_page.content, 'html.parser')

        #find single html element containing all data we need
        ul = soup.find("ul", {"class": "grid -p70"})
        if (ul != None):
            movies = ul.find_all("li") #get all html "list" elements to iterate through them 
        for movie in movies:
            idlist.append(movie.find('div')['data-film-id']) #get value of "data-film-id" and append to list
            titlelist.append(movie.find('div')['data-item-name'])
            ratinglist.append(transform_ratings(movie.find('p', {"class": "poster-viewingdata"}).get_text().strip()))
            likedlist.append(movie.find('span', {'class': 'like'})!=None)
            linklist.append("https://letterboxd.com" + movie.find('div')['data-target-link'])
            userlist.append(username)
            print(movie.find('div')['data-item-name'])
            sleep(0.2) #rate limit protection, 0.2 seems to work well

        #if there is no next page button, break the loop
        if soup.find('a', {'class':'next'}) is None:
            break
        
        #if there is a next page button, go to it
        else:
            url = DOMAIN + soup.find('a', {'class':'next'})['href']

    #add lists as values to dictionary
    movies_dict['id'] = idlist
    movies_dict['title'] = titlelist
    movies_dict['rating'] = ratinglist
    movies_dict['liked'] = likedlist
    movies_dict['link'] = linklist
    movies_dict['user'] = userlist

    ratings_dict = {}
    for k, v in zip(titlelist, ratinglist):
        ratings_dict[k] = v

    df = pd.DataFrame(movies_dict)
    df.to_csv(f'{username}_movies.csv', encoding="utf-8-sig", index=False)

    return movies_dict, ratings_dict

def scrape_list_films(username, url):
    idlist = []
    titlelist = []
    linklist = []
    userlist = []
    
    print(f"Scraping films from {url} via {username}'s profile...")

    # check number of pages
    while True:
        url_page = requests.get(url)
        soup = BeautifulSoup(url_page.content, 'html.parser')

        ul = soup.find("ul", {"class": "js-list-entries poster-list -p125 -grid"})
        if (ul != None):
            movies = ul.find_all("li")
        for movie in movies:
            idlist.append(movie.find('div')['data-film-id'])
            titlelist.append(movie.find('div')['data-item-name'])
            linklist.append("https://letterboxd.com" + movie.find('div')['data-target-link'])
            userlist.append(username)
            print(movie.find('div')['data-item-name'])
            sleep(0.2) #rate limit protection, 0.2 seems to work well

        if soup.find('a', {'class':'next'}) is None:
            break

        else:
            url = DOMAIN + soup.find('a', {'class':'next'})['href']

    hmn_movies_dict['id'] = idlist
    hmn_movies_dict['title'] = titlelist
    hmn_movies_dict['link'] = linklist
    hmn_movies_dict['user'] = userlist

    print(f"Getting ratings from {username}...")
    profilefull, profileratings = scrape_films(username)

    #creates list of ratings for HMN movies, using None if movie has not been watched
    hmn_ratings_list = list(map(profileratings.get, titlelist))
   
    #add ratings to hmn_movies_dict
    hmn_movies_dict['ratings'] = hmn_ratings_list

    df = pd.DataFrame(hmn_movies_dict)
    df.to_csv(f'{username}_listmovies.csv', encoding="utf-8-sig", index=False)

    return hmn_movies_dict

def get_friends(username):
    url = DOMAIN + "/" + username + "/following/"

    while True:
        url_page = requests.get(url)
        soup = BeautifulSoup(url_page.content, 'html.parser')

        table = soup.find("table", {"class": "table-base member-table"})
        table_body = table.find("tbody")
        friends = table_body.find_all('div', {"class": "person-summary"})
        for friend in friends:
            friendlist.append(friend.find('a')['href'].strip("/"))

        if soup.find('a', {'class':'next'}) is None:
            break

        else:
            url = DOMAIN + soup.find('a', {'class':'next'})['href']

    friends_dict['following'] = friendlist

    df = pd.DataFrame(friends_dict)
    df.to_csv(f'{username}_following.csv', encoding="utf-8-sig", index=False)

    return friends_dict

def scrape_list_custom_friends():
    url = input("Enter url of list: ")
    friends = list(input("Enter users separated by comma: ").split(","))

    for friend in friends:
        print(f"Scraping {friend}")
        scrape_list_films(friend, url)

def scrape_list_all_friends(username):
    url = input("Enter url of list: ")
    friends = get_friends(username).get('following')

    for friend in friends:
        print(f"Scraping {friend}")
        scrape_list_films(friend, url)

def scrape_custom_friends():
    friends = list(input("Enter users separated by comma: ").split(","))
    for friend in friends:
        print(f"Scraping {friend}")
        scrape_films(friend)

def scrape_all_friends(username):
    friends = get_friends(username).get('following')

    for friend in friends:
        print(f"Scraping {friend}")
        scrape_films(friend)

def main_menu():
    print("Choose an option:")
    print("1. Scrape single profile")
    print("2. Scrape multiple profiles")
    print("3. Scrape profiles of everyone you are following")
    print("4. Scrape single profile for list")
    print("5. Scrape multiple profiles for list")
    print("6. Scrape profiles of everyone you are following for list")
    print("0. Exit")

    while True:
        choice = input("Enter your choice (0-5): ")

        if choice == "1":
            print("Enter username to scrape:")
            username = input()
            scrape_films(username)
        elif choice == "2":
            scrape_custom_friends()
        elif choice == "3":
            print("Enter username to scrape:")
            username = input()
            scrape_all_friends(username)
        elif choice == "4":
            print("Enter username to scrape:")
            username = input()
            print("Enter list URL: ")
            lblist = input()
            scrape_list_films(username, lblist)
        elif choice == "5":
            scrape_list_custom_friends()
        elif choice == "6":
            print("Enter username to scrape:")
            username = input()
            scrape_list_all_friends(username)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()

#get_friends(username)
#scrape_films(username)
#scrape_list_films(username)
#get_friends_ratings(username)