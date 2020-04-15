import re
from requests_html import HTMLSession, HTML
from datetime import datetime
from urllib.parse import quote
from lxml.etree import ParserError
import mechanicalsoup
import xlsxwriter # for writing to excel wkbk

session = HTMLSession()


browser = mechanicalsoup.StatefulBrowser()
browser.addheaders = [('User-agent', 'Firefox')]

def get_tweets(query, party, numTweets = 500):
    """Gets tweets for a given user, via the Twitter frontend API."""

    after_part = f'include_available_features=1&include_entities=1&include_new_items_bar=true'
    url = f'https://twitter.com/i/profiles/show/{query}/timeline/tweets?'
    url += after_part
    workbook = xlsxwriter.Workbook('scrubbed_tweets/' + query + '.xlsx')
    worksheet = workbook.add_worksheet()


    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'https://twitter.com/{query}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
        'X-Twitter-Active-User': 'yes',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'en-US'
    }

    def gen_tweets(party,numTweets):
        r = session.get(url, headers=headers)
        row = 0
        pages = 1

        while pages > 0:
            try:
                html = HTML(html=r.json()['items_html'],
                            url='bunk', default_encoding='utf-8')
            except KeyError:
                raise ValueError(
                    f'Oops! Either "{query}" does not exist or is private.')
            except ParserError:
                break

            comma = ","
            dot = "."
            tweets = []
            for tweet in html.find('.stream-item'):
                # 10~11 html elements have `.stream-item` class and also their `data-item-type` is `tweet`
                # but their content doesn't look like a tweet's content
                try:
                    text = tweet.find('.tweet-text')[0].full_text
                except IndexError:  # issue #50
                    continue
                tweets.append(text)


            last_tweet = html.find('.stream-item')[-1].attrs['data-item-id']

            for tweet in tweets:
                    uncleaned = tweet
                    tweet = re.sub(r'https?:\/\/\S+', '', tweet) # remove links
                    tweet = re.sub(r'pic\.twitter\S+', '', tweet) # remove pictures
                    # if no text left... delete that tweet! punctuation?
                    stripped = tweet.strip()
                    if stripped == '':
                        tweets.remove(uncleaned)
                        continue
                    worksheet.write(row, 0, tweet)
                    worksheet.write(row, 1, party)
                    row += 1
                    if row == numTweets:
                        pages = 0
                        break
                    yield tweet


            r = session.get(url, params={'max_position': last_tweet}, headers=headers)
            pages += 1

    yield from gen_tweets(party, numTweets)
    workbook.close()


# for searching:
#
# https://twitter.com/i/search/timeline?vertical=default&q=foof&src=typd&composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&latent_count=0
# replace 'foof' with your query string.  Not sure how to decode yet but it seems to work.
