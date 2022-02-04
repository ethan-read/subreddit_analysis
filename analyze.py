import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from random import randint
import pandas as pd
import datetime



def get_averages(response: dict) -> tuple:
    """
    Returns the average character length of the comments and a crude approximation
    of the average word length
    """
    comments = response['data']
    total_chars = 0
    total_spaces = 1
    for comment in comments:
        total_chars += len(comment['body'])
        total_spaces += comment['body'].count(' ')

    return total_chars / len(comments), total_chars / total_spaces


def analyze(start_time: int, subreddit: str, sample_size: int,
            end_time=int(time.time())) -> pd.DataFrame:

    if start_time >= end_time:
        raise ValueError("start_time must be smaller than end_time")
    days = (end_time - start_time) // 86400
    data = np.zeros((days, 4))

    for i in range(days):
        print(i)
        daily_time = start_time + i * 86400 + randint(0, 50000)
        url = 'https://api.pushshift.io/reddit/search/comment/' + \
        f'?subreddit={subreddit}&after={daily_time}&fields=body&size={sample_size}'
        comments = requests.get(url)

        if comments.status_code !=200:  # Server eror, try one more time
            time.sleep(0.5)
            comments = requests.get(url)
            if comments.status_code != 200:
                print(f"Request failed, status code {comments.status_code}")
                com_length = word_length = 0
        else:
            com_length, word_length = get_averages(comments.json())


        data[i][0] = daily_time
        data[i][1] = com_length
        data[i][2] = word_length
        data[i][3] = comments.status_code
        time.sleep(0.5)  # The server has a limit of 120 requests/minute

    results = pd.DataFrame(data, columns=
                           ['Retrieval Time', 'Comment Length',
                            'Word Length', 'Response Code'])

    return results


def rolling_avg(values: np.ndarray, period: int) -> np.ndarray:
    period = min(period, len(values))
    smoothed = values.copy()
    for i in range(1, period):
        smoothed[i] = np.mean(values[:period + i])
    for i in range(period, len(values)):
        if values[i] > 0:
            smoothed[i] = np.mean(values[i - period: i])
        else:
            smoothed[i] = smoothed[i - 1]

    return smoothed


def make_plots(results: pd.DataFrame, subreddit: str, smoothing=50) -> None:

    # Remove all unsuccsesful requests
    cleaned_results = results[results['Response Code'] == 200]

    # Make the retrieval times readable for the x-axis
    dates = list(map(lambda utc: str(datetime.date.fromtimestamp(utc)),
                         cleaned_results['Retrieval Time'].values))

    plt.figure()
    plt.title(f'Average /r/{subreddit} Comment Length')
    plt.plot(rolling_avg(cleaned_results['Comment Length'].values, smoothing))
    ax = plt.axes()
    ax.set_xticks([0, int(len(dates)/3), 2*int(len(dates)/3), len(dates)-1])
    ax.set_xticklabels([dates[0], dates[int(len(dates)/3)],
                        dates[2*int(len(dates)/3)], dates[-1]])
    ax.set_ylabel('Characters per Comment')
    plt.show()

    plt.figure()
    plt.title(f'Average /r/{subreddit} Word Length')
    plt.plot(rolling_avg(cleaned_results['Word Length'].values, smoothing), 'red')
    ax = plt.axes()
    ax.set_xticks([0, int(len(dates)/3), 2*int(len(dates)/3), len(dates)-1])
    ax.set_xticklabels([dates[0], dates[int(len(dates)/3)],
                        dates[2*int(len(dates)/3)], dates[-1]])
    ax.set_ylabel('Characters per Space')
    plt.show()


if __name__ == '__main__':

    SUBREDDIT = 'pics'  # no slashes
    SAMPLE_SIZE = 300  # Number of comments per day, maximum 500
    NUMBER_OF_DAYS = 800  # Total processing time will require about 1 sec per day
    start_time = int(time.time()) - NUMBER_OF_DAYS * 86400


    # results = analyze(start_time, SUBREDDIT, SAMPLE_SIZE)
    # results.to_csv(f'{SUBREDDIT}_analysis.csv')
    # make_plots(results, SUBREDDIT)


    # For replotting without running the whole thing again

    results = pd.read_csv('{SUBREDDIT}_analysis.csv')
    make_plots(results, SUBREDDIT,smoothing=100)




