#!/usr/bin/env python

# --------------------------------------------------------------------
# stats_sql
# --------------------------------------------------------------------

from sys import stderr

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import configs
from database import Account, RawData, Survey

DATABASE_URL = configs.DATABASE_URL


# Returns stats; specifically, [dict of class year counts, dict of res college counts]
def get_stats():
    # connect to database
    try:
        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()

        # Get res college & class year stats
        years = {"2022": 0, "2023": 0, "2024": 0, "2025": 0}
        res = {"Butler": 0, "Whitman": 0, "Rockefeller": 0, "Forbes": 0, "Mathey": 0, "First": 0}
        accounts = (session.query(Account).all())
        for account in accounts:
            if account.class_year in ["2022", "2023", "2024", "2025"]:
                years[account.class_year] += 1
            if account.res_college in ["Butler", "Whitman", "Rockefeller", "Forbes", "Mathey", "First"]:
                res[account.res_college] += 1

        responses = {"21": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, },
                     "13": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, },
                     "23": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, }}  # questions displayed = #13, #21, #23
        user_responses = (session.query(RawData).all())
        for response in user_responses:
            responses["13"][str(response.q13_response)] += 1
            responses["21"][str(response.q21_response)] += 1
            responses["23"][str(response.q23_response)] += 1

        questions = (session.query(Survey).all())
        formatted_responses = {}
        for q in questions:
            if q.q_num in [13, 21, 23]:
                print(q.q_num)
                formatted_responses[q.question] = {}
                answers = responses[str(q.q_num)]
                formatted_responses[q.question][q.answer1] = answers["1"]
                formatted_responses[q.question][q.answer2] = answers["2"]
                formatted_responses[q.question][q.answer3] = answers["3"]
                formatted_responses[q.question][q.answer4] = answers["4"]
                formatted_responses[q.question][q.answer5] = answers["5"]

        session.close()
        engine.dispose()

        return [years, res, formatted_responses]

    except Exception as ex:
        print(ex, file=stderr)
        print("Stats get failed", file=stderr)


# --------------------------------------------------------------------

if __name__ == '__main__':
    stats = get_stats()
    print(stats)
