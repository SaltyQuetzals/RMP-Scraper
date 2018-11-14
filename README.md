# RMP-Scraper

A command-line tool to download student reviews of their professors from a popular professor-rating website.


Given a school's RateMyProfessors.com ID, this tool will scrape every user-submitted review of a professor (and associated metadata), and convert that data into an easily-analyzable CSV for data processing.

To use the tool, simply enter:

```
python src/scraper.py <YOUR_SCHOOL_ID>
```

To get your school ID, go [here](http://www.ratemyprofessors.com/), and search for your school. In your URL address bar, you should see a URL along the lines of:

```
http://www.ratemyprofessors.com/campusRatings.jsp?sid=<YOUR_SCHOOL_ID>
```
The value of the query parameter `sid` is the unique identifier for your school that serves as the required command-line argument for the scraper.

The scraper takes a while (about five minutes with decent internet for more than 26,000 examples).

## Examples

**Texas A&M University**
```
python src/scraper.py 1003
```

**Stanford University**
```
python src/scraper.py 953
```

**Cornell University**
```
python src/scraper.py 298
```

**University of Texas at Dallas**
```
python src/scraper.py 1273
```
