# --------------------------------------------------------------------
# matching.py
# --------------------------------------------------------------------
from sys import stderr

import psycopg2

DATABASE_URL = 'file:TigerFriend.sqlite?mode=ro'


# --------------------------------------------------------------------

# Fill in match scores upon account creation of a user
def input_match_scores(net_id):
    try:
        # connect to database
        with psycopg2.connect(host="ec2-3-217-113-25.compute-1.amazonaws.com",
                              database="dd4c5lulvqtkld",
                              user="fpzzhwdkkymqrr",
                              password="b87ef0b3ae33d79f063d25d7ec8dde6871405d7d85b67ddff7f1ddaec3d00361") as connect:
            with connect.cursor() as cursor:
                # get user's survey response
                stmt = "SELECT * FROM rawdata WHERE net_id=\'" + net_id + "\'"
                cursor.execute(stmt)
                user_raw_data = cursor.fetchone()
                # print(user_raw_data)

                # get user's year, major, and res college
                stmt = "SELECT class_year, major, res_college FROM account WHERE net_id=\'" + net_id + "\'"
                cursor.execute(stmt)
                user_info = cursor.fetchone()
                yr = user_info[0]
                major = user_info[1]
                res = user_info[2]

                # get question types
                stmt = "SELECT q_type FROM survey"
                cursor.execute(stmt)
                q_type = cursor.fetchone()
                q_types = []
                while q_type is not None:
                    q_types.append(q_type[0])
                    q_type = cursor.fetchone()
                # print(q_types)

                # compare survey responses with other users
                stmt = "SELECT net_id FROM account Except SELECT net_id FROM rawdata WHERE net_id=\'" + net_id + "\'"
                cursor.execute(stmt)
                other_user = cursor.fetchone()
                other_users = []
                while other_user is not None:
                    other_users.append(str(other_user[0]))
                    other_user = cursor.fetchone()

                for other_user in other_users:

                    overall_match_score = 0
                    academic_match_score = 0
                    extracurricular_match_score = 0
                    personality_match_score = 0
                    opinion_match_score = 0

                    stmt = "SELECT * FROM rawdata WHERE net_id=\'" + other_user + "\'"
                    cursor.execute(stmt)
                    other_raw_data = cursor.fetchone()

                    for i in range(len(q_types)):
                        # print("Question " + str(i + 1))
                        if user_raw_data[i + 1] == other_raw_data[i + 1]:
                            # print(str(user_raw_data[0]) + " and " + other_user +
                            #      " matched  with answer choice " + str(user_raw_data[i+1]))
                            overall_match_score += 1
                            # print("Question type " + str(q_types[i]))
                            if q_types[i] == 1:
                                academic_match_score += 1
                            elif q_types[i] == 2:
                                extracurricular_match_score += 1
                            elif q_types[i] == 3:
                                personality_match_score += 1
                            elif q_types[i] == 4:
                                opinion_match_score += 1

                    stmt = "SELECT class_year, major, res_college FROM account WHERE net_id=\'" + other_user + "\'"
                    cursor.execute(stmt)
                    other_user_info = cursor.fetchone()

                    if str(yr) == str(other_user_info[0]):
                        # print(str(user_raw_data[0]) + " and " + other_user + " matched on year " + str(yr))
                        overall_match_score += 1
                        personality_match_score += 1
                    if str(major) == str(other_user_info[1]):
                        # print(str(user_raw_data[0]) + " and " + other_user + " matched on year " + str(major))
                        overall_match_score += 1
                        academic_match_score += 1
                    if str(res) == str(other_user_info[2]):
                        # print(str(user_raw_data[0]) + " and " + other_user + " matched on year " + str(res))
                        overall_match_score += 1
                        extracurricular_match_score += 1

                    # input scores into data table
                    print(net_id, other_user, overall_match_score)
                    stmt = "INSERT INTO matchscores (net_id1, net_id2, overall_score, academic_score, ec_score, \
                            personality_score, opinion_score) VALUES (\'" + net_id + "\', \'" + other_user + "\', "
                    stmt += str(overall_match_score) + ", " + str(academic_match_score) + ", " + str(
                        extracurricular_match_score)
                    stmt += ", " + str(personality_match_score) + ", " + str(opinion_match_score) + ");"
                    cursor.execute(stmt)
                    connect.commit()

    except (Exception, psycopg2.Error) as ex:
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)


# --------------------------------------------------------------------

# Returns dict w/"overall", "academic", "ec", "personality", and 
# "opinion" match arrays
def get_matches(net_id):
    try:
        # connect to database
        with psycopg2.connect(host="ec2-3-217-113-25.compute-1.amazonaws.com",
                              database="dd4c5lulvqtkld",
                              user="fpzzhwdkkymqrr",
                              password="b87ef0b3ae33d79f063d25d7ec8dde6871405d7d85b67ddff7f1ddaec3d00361") as connect:
            with connect.cursor() as cursor:
                stmt = "SELECT * FROM matchscores WHERE net_id1=\'" + net_id + "\' OR net_id2=\'" + net_id + "\'"
                cursor.execute(stmt)
                id1 = []
                id2 = []
                over = []
                acad = []
                ec = []
                pers = []
                opin = []

                row = cursor.fetchone()
                while row is not None:
                    id1.append(row[0])
                    id2.append(row[1])
                    over.append(int(row[2]))
                    acad.append(int(row[3]))
                    ec.append(int(row[4]))
                    pers.append(int(row[5]))
                    opin.append(int(row[6]))
                    row = cursor.fetchone()

                scores = [over, acad, ec, pers, opin]

                # print(id1)
                # print(over)

                matches = {"overall": [None, None, None, None],
                           "academic": [None, None, None, None],
                           "ec": [None, None, None, None],
                           "personality": [None, None, None, None],
                           "opinion": [None, None, None, None]}
                match_vals = {"overall": [-1, -1, -1, -1],
                              "academic": [-1, -1, -1, -1],
                              "ec": [-1, -1, -1, -1],
                              "personality": [-1, -1, -1, -1],
                              "opinion": [-1, -1, -1, -1]}
                categories = ["overall", "academic", "ec", "personality", "opinion"]

                for i in range(len(id1)):
                    if id1[i] == net_id:
                        match = id2[i]
                    else:
                        match = id1[i]

                    # get top 4
                    for j in range(len(categories)):
                        if scores[j][i] > match_vals[categories[j]][3]:  # if match is better than worst match currently
                            index = firstSmallerIndex(match_vals[categories[j]], scores[j][i])
                            match_vals[categories[j]] = insertAtIndex(match_vals[categories[j]], index, scores[j][i])
                            matches[categories[j]] = insertAtIndex(matches[categories[j]], index, match)

                # remove extra null entries (if any)
                for i in range(len(categories)):
                    if matches[categories[i]][3] is None:
                        delete = 3
                        while matches[categories[i]][delete] is None:
                            matches[categories[i]].pop(delete)
                            delete = delete - 1
                            if delete == -1:
                                break

                # Replace net_ids with usernames (get bios in this step as well in the future)
                for i in range(len(categories)):
                    for j in range(len(matches[categories[i]])):
                        # print(matches[categories[i]][j])
                        net_id = matches[categories[i]][j]
                        stmt = "SELECT username FROM account WHERE net_id=\'" + str(net_id) + "\'"
                        cursor.execute(stmt)
                        row = cursor.fetchone()
                        matches[categories[i]][j] = row[0]

    except (Exception, psycopg2.Error) as ex:
        print(ex, file=stderr)
        print("Data base connection failed", file=stderr)
        return {"overall": [],
                "academic": [],
                "ec": [],
                "personality": [],
                "opinion": []}

    return matches


# helper functions
def firstSmallerIndex(arr, val):
    for i in reversed(range(len(arr))):
        if val < arr[i]:
            return i + 1
    return 0


def insertAtIndex(arr, index, insert):
    for i in reversed(range(len(arr))):
        if i > index:
            arr[i] = arr[i - 1]
        elif i is index:
            arr[i] = insert
    return arr


# unit test
def main():
    print(get_matches("collado"))


# ----------------------------------------------------------------------

if __name__ == '__main__':
    main()
