import json
import os
from curl_cffi import requests

BASE_URL = "https://www.uga.org/gn-api/facility-api/Facility?facilityId="

OUTPUTS_DIR = "outputs"
COURSES_DIR = "individual_course_data"

# Paste fresh cookies from your browser here when they expire.
# In Chrome: DevTools → Network → any uga.org request → right-click → Copy as cURL,
# then extract the cookies from that output.
COOKIES = {
    'feathr_session_id': '6a375a59786879ee6dc40406',
    'PHPSESSID': 'bd45ivvtt1n02n66k7at4fjolm',
    'cf_clearance': 'L6BfBP7TZVTnTUiWySxT6o4xcOoMkB2owgocrddM4qQ-1782012506-1.2.1.1-J2X1mM.sYdxNZt3I_FI0qszkeVQcTk9OvRPpIOyk5Toqm5GKilryaPA.a9B7TfWsSKwbTyH0jX961iFobcAFMKeuKhX.NKFgL53vBhH9aNc.qi72yrdWiThOZE_5ncV1iABwV3fsegcK4H0muJaslq_lB9ID4v57pDhKXWJUF_mDbU.TrIEZ7puQY2qufqMkQu8wj.C_jtB7OExJLIMJTzDoXZlVrYQv.ce_JK.qJP.QALDRYuWWqR9M_RDjrrU_kmLxptnyVlzD4Zh6zUkaGRdLxuPdGkDBqaYnAivQqKshcaLCCf0yFyzqCxMtHQcT2ZkypXMAyNfnNMAwNHYOWQ',
    '_gid': 'GA1.2.1817216069.1782012506',
    '__hstc': '247795032.c6d3e0fd1e139cc916931c1d15d1d35f.1782012506603.1782012506603.1782012506603.1',
    'hubspotutk': 'c6d3e0fd1e139cc916931c1d15d1d35f',
    '__hssrc': '1',
    '_ga_S22M4RSXJ0': 'GS2.1.s1782012506$o1$g1$t1782012530$j36$l0$h0',
    '_ga': 'GA1.1.402323578.1782012506',
    '_ga_NXL1T5G8Q3': 'GS2.1.s1782012505$o1$g1$t1782012531$j34$l0$h0',
    '__hssc': '247795032.3.1782012506603',
}

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Basic YW5vbnltb3VzfjExOmFub255bW91cw==',
    'content-type': 'application/json',
    'referer': 'https://www.uga.org/gn-web-app/facilities/25323',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

def get_data(facility_id):
    response = requests.get(
        'https://www.uga.org/gn-api/facility-api/Facility',
        params={'facilityId': facility_id},
        cookies=COOKIES,
        headers=HEADERS,
        impersonate="chrome",
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"  HTTP {response.status_code} for facility {facility_id}")
        return {"error": f"HTTP {response.status_code}"}


def read_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def write_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def parse_data(raw_json_data):
    all_data = []
    for course in raw_json_data["Courses"]:
        print(f"  Course {course['CourseId']} | {course['CourseName']}")
        course_data = {}
        for tee_data in course["CourseTeeViews"]:
            tee_name = tee_data["GenderTypeCd"] + " - " + tee_data["TeeName"]
            course_data[tee_name] = {
                "Rating": tee_data["UsgaRating18"],
                "Bogey":  tee_data["UsgaBogey18"],
                "Slope":  tee_data["UsgaSlope18"],
            }
        write_json(course_data, os.path.join(COURSES_DIR, f"course_{course['CourseId']}.json"))
        all_data.append(course_data)
    return all_data

def main():
    facility_data = read_json("courses.json")
    output = {}
    skipped = []
    for facility in facility_data["Facilities"]:
        facility_id = facility["FacilityId"]
        human_course_name = facility["FacilityName"] + " - " + str(facility_id)
        print(f"Processing facility {human_course_name}")
        raw_outputs = get_data(facility_id)
        if "error" in raw_outputs:
            print(f"  Skipping {human_course_name}: {raw_outputs['error']}")
            skipped.append(human_course_name)
            continue
        try:
            output[human_course_name] = parse_data(raw_outputs)
        except Exception as e:
            print(f"  Skipping {human_course_name}: parse error — {e}")
            skipped.append(human_course_name)

    write_json(output, os.path.join(OUTPUTS_DIR, "output.json"))
    if skipped:
        print(f"\nSkipped {len(skipped)} facilities:")
        for name in skipped:
            print(f"  - {name}")

def single_test(facility_id):
    raw_outputs = get_data(facility_id)
    if "error" in raw_outputs:
        print(f"Error for facility {facility_id}: {raw_outputs['error']}")
        return
    human_course_name = raw_outputs["FacilityName"] + " - " + str(raw_outputs["FacilityId"])
    output = parse_data(raw_outputs)
    write_json(output, os.path.join(OUTPUTS_DIR, f"output_{facility_id}.json"))


if __name__ == "__main__":
    main()  
    # single_test("7176")