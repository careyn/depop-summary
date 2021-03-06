from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import mysql.connector

# Takes the data from an individual product's URL, returns the SQL statement to add it to products table
def scrape_data(url):
    # Open the chrome web driver
    driver = webdriver.Chrome('./chromedriver')
    driver.get(url)

    # ensure the page loads image source (dynamic property)
    time.sleep(0.5)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    # Find the values with a class equal to that which contains the product description
    description_html = soup.find(class_="Text-yok90d-0 styles__DescriptionContainer-uwktmu-9 bWcgji")

    # Clean the desc data by removing the <div> tag, removing non-ascii characters, and removing "'"
    ''' desc = description_html.contents[0].encode("ascii", "ignore").decode() '''
    desc = description_html.contents[0].replace("'", "")

    # Find text with price information
    price_html = soup.find("span", {"data-testid": "fullPrice"})

    # (pull contents[0] to remove the <span> tag)
    price = price_html.contents[0]

    # Find the images that have the class representing product images
    img = soup.find("div", {"data-testid": "product__images"})

    # pull the src from the <div> holding the <img>
    src = img.contents[0].contents[0].get("src")

    # close the web driver
    driver.close()

    return "INSERT INTO products VALUES ('" + price + "', '" + src + "', '" + desc + "');"

    '''
        if soup.find("div", {"data-testid": "productPurchase"}).contents[0].contents[0] == "Sold":
            sold = "1"

        else:
            sold = "0"
    '''


# Scrolls through the home page and generates the URLs for every product on their store
# Then calls the scrape_function for each URL and returns the complete list of commands to convert to SQL
def create_sql(username):
    commands = []

    # generate homepage url using the username
    home = "https://www.depop.com/" + username

    # open the web driver
    driver = webdriver.Chrome('./chromedriver')
    driver.get(home)

    # allow time for dynamic elements to load
    time.sleep(1)

    elem = driver.find_element_by_tag_name("body")

    # pagedown with selenium to ensure that we load every JS element that Depop stores
    no_of_pagedowns = 100

    while no_of_pagedowns:
        elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.1)
        no_of_pagedowns -= 1

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    # Pull the URLs for every item with the product tag
    urls = soup.find_all("a", {"data-testid": "product__item"})

    for i in urls:
        commands.append((scrape_data("https://www.depop.com" + i.get("href"))))

    # close the driver
    driver.close()

    return commands


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


mydatabase = mysql.connector.connect(
    host='127.0.0.1', user='root',
    passwd='password', database='testing')

mycursor = mydatabase.cursor()


# Gets the username from the HTML form and calls the SQL generator for that username
# Before running the new INSERT commands generated by create_SQL, drop all records from the table
# Finish by selecting all to return and rendering with our stock template
@app.route('/button')
def button():
    # The table in the local database that we are appending to
    print("CREATE TABLE products (price varchar(255), src LONGTEXT, descr LONGTEXT); ")
    q = request.args.get("username")
    d = str(q)
    mycursor.execute('DELETE FROM products;')
    for command in create_sql(d):
        print(command)
        mycursor.execute(command)
    mycursor.execute('SELECT * FROM products;')
    data = mycursor.fetchall()
    html = render_template('stock.html', output_data=data)
    return html


if __name__ == '__main__':
    app.run()
