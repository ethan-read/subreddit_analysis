This script takes a daily sample of comments from a chosen subreddit to calculate the average comment length and approximate the average word length, then plots them.


#Usage

To run the script you need to choose two parameters, declared near the bottom. SUBREDDIT is a string of the subreddit name, and NUMBER_OF_DAYS is how many days will be included in the sample. Since the program plots a moving average by default, the plots have the first 20 days cut off, but this beaviour can be altered by using optional arguments in the analyze() and make_plots() functions.

In case you want to make multiple plots without querying the api again or do error checking, the results are saved in a .csv file, and the code to read the file and make new plots is commented out at the bottom. 
