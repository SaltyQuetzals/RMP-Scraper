import json
import argparse
import datetime
import math
import collections

import pandas as pd
import requests

BASE_URL = 'http://search.mtvnservices.com/typeahead/suggest/?solrformat=false&rows=300000&q=*%3A*+AND+schoolid_s%3A{}&defType=edismax&qf=teacherfirstname_t%5E2000+teacherlastname_t%5E2000+teacherfullname_t%5E2000+autosuggest&bf=pow(total_number_of_ratings_i%2C2.1)&sort=total_number_of_ratings_i+desc&siteName=rmp&rows=20&start=0&fl=pk_id+teacherfirstname_t+teacherlastname_t+total_number_of_ratings_i+averageratingscore_rf+schoolid_s&fq='

json_to_csv = {
    'attendance': 'attendance_required',
    'rOverall': 'overall_quality',
    'rEasy': 'difficulty_level',
    'helpCount': 'num_found_helpful',
    'notHelpCount': 'num_found_unhelpful',
    'rDate': 'date_submitted',
    'rClass': 'class_name',
    'rTextBookUse': 'textbook_used',
    'rWouldTakeAgain': 'would_take_again',
    'takenForCredit': 'taken_for_credit',
    'teacherGrade': 'grade_achieved',
    'rClarity': 'clarity',
    'rComments': 'comment'
}

key_boolean_values = {
    'attendance_required': ['Mandatory', 'Not Mandatory'],
    'textbook_used': ['Yes', 'No'],
    'taken_for_credit': ['Yes', 'No'],
    'would_take_again': ['Yes', 'No']
}


def build_professor_csv(school_id) -> pd.DataFrame:
    """
    Requests the list of professors for a given school,
    and creates a Pandas DataFrame containing their information.

    Args:
        school_id: The sid that identifies a school on RateMyProfessors.com
    Returns:
        A Pandas DataFrame with three columns: "first_name", "last_name", and "pk_id"
    """
    professors = {'first_name': [], 'last_name': [], 'pk_id': []}
    response = requests.get(BASE_URL.format(school_id))
    response.raise_for_status()  # Throw an exception if the request fails
    json_response = json.loads(response.content)

    solr_docs = json_response['response']['docs']
    for doc in solr_docs:
        teacher_firstname = doc['teacherfirstname_t']
        teacher_lastname = doc['teacherlastname_t']
        pk_id = doc['pk_id']
        professors['first_name'].append(teacher_firstname.strip())
        professors['last_name'].append(teacher_lastname.strip())
        professors['pk_id'].append(pk_id)

    df = pd.DataFrame(data=professors)
    df.to_csv(f'data/{school_id}_professors.csv', index=False)
    return df


def scrape_reviews(pk_id, retry_depth=0) -> pd.DataFrame:
    """
    Scrapes a RateMyProfessors page for a specific professor, and extracts
    data about their reviews.

    Args:
        pk_id: The unique identifier of a professor on RateMyProfessors.com
    Returns:
        A Pandas DataFrame
    """
    reviews = {value: [] for value in json_to_csv.values()}
    reviews['pk_id'] = []
    if retry_depth > 5:
        return pd.DataFrame(data=reviews)
    URL = 'http://www.ratemyprofessors.com/paginate/professors/ratings?tid=' + \
        str(pk_id) + '&filter=&courseCode=&page={}'
    page_number = 0
    response = requests.get(URL.format(page_number))
    response.raise_for_status()
    json_response = response.json()

    TRUE_VALUE = 0
    while json_response['remaining'] != 0:
        for rating in json_response['ratings']:
            for key in rating:
                if key in json_to_csv:
                    json_value = rating[key]
                    if isinstance(json_value, str):
                        json_value = json_value.strip()
                    csv_key = json_to_csv[key]
                    if csv_key in key_boolean_values:
                        if json_value == 'N/A':
                            json_value = None
                        elif json_value == key_boolean_values[csv_key][TRUE_VALUE]:
                            json_value = True
                        else:
                            json_value = False
                    elif csv_key == 'date_submitted':
                        json_value = datetime.datetime.strptime(json_value, '%m/%d/%Y').date()
                    reviews[csv_key].append(json_value)
            reviews['pk_id'].append(pk_id)
        page_number += 1
        response = requests.get(URL.format(page_number))
        response.raise_for_status()
        try:
            json_response = response.json()
        except json.decoder.JSONDecodeError:
            retry_depth += 1
            print(f'JSONDecodeError. Attempt: {retry_depth}/5')
            return scrape_reviews(pk_id, retry_depth)
    return pd.DataFrame(data=reviews)


def main(school_id):
    keys = ['date_submitted',
            'overall_quality',
            'level_of_difficulty',
            'class_name',
            'taken_for_credit',
            'attendance_required',
            'textbook_used',
            'would_take_again',
            'grade_received',
            'comment',
            'found_useful', 'found_not_useful']
    professor_df = build_professor_csv(school_id)
    reviews_df = pd.DataFrame(columns=keys)
    for _, row in professor_df.iterrows():
        print('-------------------------------------')
        print(BASE_URL.format(row['pk_id']))
        print(row['first_name'] + ' ' + row['last_name'])
        new_reviews = scrape_reviews(row['pk_id'])
        reviews_df = pd.concat([reviews_df, new_reviews])
        reviews_df.to_csv(f'data/{school_id}_reviews.csv')

        print(reviews_df)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'school_id', help='The sid found in RateMyProfessors.com urls')
    args = parser.parse_args()
    main(args.school_id)
