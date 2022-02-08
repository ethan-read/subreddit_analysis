import requests
import time
import matplotlib.pyplot as plt
import numpy as np
from random import randint
import pandas as pd
import datetime


def analyze_sample(url: str, data: pd.DataFrame, row: int) -> None:
    """
    Queries the PushShift API for one sample of comments and updates <data>
    with information about the sample.
    """
    response = requests.get(url)
    if response.status_code !=200:  # Server eror, try one more time
        time.sleep(0.5)
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Request failed, status code {response.status_code}")
            data[row][3] = response.status_code
            return

    comments = response.json()['data']
    total_chars = 0
    total_spaces = 1
    for comment in comments:
        total_chars += len(comment['body'])
        total_spaces += comment['body'].count(' ')

    com_length = total_chars / len(comments)
    word_length = total_chars / total_spaces

    data[row][1] = com_length
    data[row][2] = word_length
    data[row][3] = response.status_code
    data[row][4] = len(comments)


def analyze(start_time: int, subreddit: str, sample_size=100,
            end_time=int(time.time()), daily_offset=30000, small_sample_regime=0) -> pd.DataFrame:
    """
    Returns a DataFrame with daily average comment and word length.

    start_time: A UTC timestamp that determines the starting point of the analysis.

    sample_size: The number of comments sampled each day, maximum 100.

    daily_offset: A random number of seconds are added to the daily sampling time to
    avoid sampling bias. This parameter is the upper bound for the offset.

    small_sample_regime: Specifies a number of days for which the daily offset is 0
    and the program limits itself to 24 hours of comments. Useful if a subreddit grows quickly.
    """
    if start_time >= end_time:
        raise ValueError("start_time must be smaller than end_time")
    days = (end_time - start_time) // 86400
    data = np.zeros((days, 5))

    for i in range(days):
        print(i)
        daily_start_time = start_time + i * 86400 + randint(0, 30000)
        url = 'https://api.pushshift.io/reddit/search/comment/' + \
        f'?subreddit={subreddit}&after={daily_start_time}&fields=body&size={sample_size}'
        if i < small_sample_regime:
            daily_end_time = daily_start_time + 86400
            extra = f'&before={daily_end_time}'
            url += extra
        data[i][0] = daily_start_time
        analyze_sample(url, data, i)
        time.sleep(0.5)  # The pushshift api has a limit of 120 requests/minute

    results = pd.DataFrame(data, columns=
                           ['Retrieval Time', 'Comment Length',
                            'Word Length', 'Response Code', 'Sample Size'])

    return results


def moving_avg(values: np.ndarray, interval: int, front_trim=20, end_trim=0) -> np.ndarray:
    """
    Since the values near the endpoints are not fully averaged, there are optional arguments
    to remove them from the final result.'
    """

    smoothed = np.zeros(len(values))
    for i in range(interval):
        smoothed[i] = np.mean(values[:i])
    for i in range(interval, len(values)):
        smoothed[i] = np.mean(values[i - interval : i])

    return smoothed[front_trim : len(values) - end_trim]


def make_plots(results: pd.DataFrame, subreddit: str, smoothing=75, front_trim=20) -> None:
    # Remove all unsuccsesful requests
    cleaned_results = results[results['Response Code'] == 200]

    # Make the retrieval times readable for the x-axis
    dates = list(map(lambda utc: str(datetime.date.fromtimestamp(utc)),
                         cleaned_results['Retrieval Time'].values))

    plt.figure()
    plt.title(f'Average /r/{subreddit} Comment Length')
    plt.plot(moving_avg(cleaned_results['Comment Length'].values, smoothing, front_trim=front_trim))
    ax = plt.axes()
    ax.set_xticks([0, int(len(dates)/3), 2*int(len(dates)/3), len(dates)-1])
    ax.set_xticklabels([dates[0], dates[int(len(dates)/3)],
                        dates[2*int(len(dates)/3)], dates[-1]])
    ax.set_ylabel('Characters per Comment')
    plt.show()

    plt.figure()
    plt.title(f'Average /r/{subreddit} Word Length')
    plt.plot(moving_avg(cleaned_results['Word Length'].values, smoothing, front_trim=front_trim), 'red')
    ax = plt.axes()
    ax.set_xticks([0, int(len(dates)/3), 2*int(len(dates)/3), len(dates)-1])
    ax.set_xticklabels([dates[0], dates[int(len(dates)/3)],
                        dates[2*int(len(dates)/3)], dates[-1]])
    ax.set_ylabel('Characters per Space')
    plt.show()


if __name__ == '__main__':

    SUBREDDIT = 'pics'  # no slashes
    NUMBER_OF_DAYS = 850  # Total processing time will require about 1 sec per day

    start_time = int(time.time()) - NUMBER_OF_DAYS * 86400
    results = analyze(start_time, SUBREDDIT)
    results.to_csv(f'{SUBREDDIT}_analysis.csv')
    make_plots(results, SUBREDDIT)


    # For replotting without running the whole thing again

    # results = pd.read_csv(f'{SUBREDDIT}_analysis.csv')
    # make_plots(results, SUBREDDIT,smoothing=70)




