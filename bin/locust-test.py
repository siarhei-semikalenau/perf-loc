#!/usr/bin/env python

""" Script to test adding comments to assessment for multiple users"""
"""
	Launch string
	locust --locustfile=perf/locust-test.py --host=http://192.168.99.100:8080 --no-web --clients=10 --hatch-rate=1 --run-time=60s --only-summary --csv=loc
	options
		--locustfile=<path to this file>
		--host=<URL to installed GGRC>
		--no-web - will be run in console mode
		--clients=<number of simultaneous users>
		--hatch-rate=<interval in sec to start all users>
		--run-time=<time to run test - 60s, 10m, 1h etc>
		--only-summary - print runt stats only at the end of test 
		--csv=<prefix for csv files XXX_requests.csv and XXX_distribution.csv with run stats>
		to change logging 
			--loglevel=<DEBUG/INFO/WARNING/ERROR/CRITICAL>
		to redirct log to file
			--logfile=<path to logfile>
"""
import json
import random
import re
import time
import logging, sys
from locust import HttpLocust, TaskSet, task
from faker import Faker
from datetime import datetime

""" users to authenticate """
USER_CREDENTIALS = [
    ('{"email":"perfcreator011@example.com"}'),
    ('{"email":"perfcreator012@example.com"}'),
    ('{"email":"perfcreator013@example.com"}'),
    ('{"email":"perfcreator014@example.com"}'),
    ('{"email":"perfcreator015@example.com"}'),
    ('{"email":"perfcreator016@example.com"}'),
    ('{"email":"perfcreator017@example.com"}'),
    ('{"email":"perfcreator018@example.com"}'),
    ('{"email":"perfcreator019@example.com"}'),
    ('{"email":"perfcreator020@example.com"}'),
]

""" JSON to search assessment-relevant objects """
search_assessment_relevant_json = [
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"AccessGroup"}}},"type":"count"},
	{"object_name":"Audit","filters":{"expression":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Clause"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Contract"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Control"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"DataAsset"}}},"type":"count"},
	{"object_name":"Evidence","filters":{"expression":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Facility"}}},"type":"count"},
	{"object_name":"Issue","filters":{"expression":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Market"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Objective"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"OrgGroup"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Policy"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Process"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Product"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Regulation"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Risk"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Section"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Standard"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"System"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Threat"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Vendor"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Risk"}}},"type":"count"},
	{"object_name":"Snapshot","filters":{"expression":{"left":{"object_name":"Assessment","op":{"name":"relevant"},"ids":["QQQ"]},"op":{"name":"AND"},"right":{"left":"child_type","op":{"name":"="},"right":"Threat"}}},"type":"count"},
]

iteration = 0

class UserBehavior(TaskSet):

	user_id = 0;
	assessment_id = 0;
	user_creds = ""
	header = {}

	def on_start(self):
		""" Selct random user on start """
		self.user_creds = USER_CREDENTIALS.pop(random.randrange(len(USER_CREDENTIALS)))
		self.header = {"X-ggrc-user": self.user_creds}

	def task_count(self):
		name = "010.020 Dashboard /api/people/[id]/task_count"
		headers = self.header.copy()
		response = self.client.get(
			"/api/people/"+ str(self.user_id) +"/task_count?_=" + str(int(time.time())), 
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

	def home_page(self):
		name = "001.010 Home /"
		headers = self.header.copy()
		response = self.client.get(
			"/",
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

	def dashboard(self):
		name = "010.000 Dashboard /dashboard"
		headers = self.header.copy()
		response = self.client.get(
			"/dashboard",
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)
		
		""" get current user info """
		user = json.loads(re.search('GGRC.current_user = ({.*?})', response.text).group(1))
		self.user_id = user["id"]
		
		name = "010.010 Dashboard /api/people/[id]/my_work_count"
		headers = self.header.copy()
		response = self.client.get(
			"/api/people/"+ str(self.user_id) +"/my_work_count?_=" + str(int(time.time())), 
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

		self.task_count()

		name = "010.030 Dashboard /api/people/[id]"
		headers = self.header.copy()
		response = self.client.get(
			"/api/people/"+ str(self.user_id) +"?_=" + str(int(time.time())), 
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

		name = "010.040 Dashboard /search?q=&types=Workflow"
		headers = self.header.copy()
		response = self.client.get(
			"/search?q=&types=Workflow&contact_id="+str(self.user_id)+"&extra_params=Workflow%3Astatus%3DActive", 
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)
		
	def search_assesments(self):
		name = "020.000 Search assessment /query"
		headers = self.header.copy()
		headers.update({"Content-Type": "application/json"})
		response = self.client.post("/query", None,
			[{
				"object_name":"Assessment",
				"filters":{
					"expression":{
						"left":"Title",
						"op":{
							"name":"~"
						},
						"right":""
					}
				},
				"limit":[0,10],
				"order_by":[{
					"name":"updated_at",
					"desc":"true"
				}],
				"permissions":"read",
				"type":"values"
			}],
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

		""" Get assessments and choose random """
		""" TODO: check number of assessments"""
		assessments = (response.json())[0]["Assessment"]["values"]
		assessment_ids = []
		for assessment in assessments:
			assessment_ids.append(assessment["id"])
		return(assessment_ids[random.randrange(len(assessment_ids))])

	def open_assessment(self, assessment_id):
		name = "030.010 Open assessment /assessments/[id]"
		headers = self.header.copy()
		headers.update ({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"})
		response = self.client.get(
			"/assessments/" + str(assessment_id), 
			headers=headers, 
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

		self.task_count()

		""" Prepare search json request"""
		search = json.dumps(search_assessment_relevant_json)
		search = search.replace("QQQ", str(assessment_id))

		name = "030.020 Open assessment (search relevant) /query"
		headers = self.header.copy()
		headers.update({"Content-Type": "application/json"})
		response = self.client.post(
			"/query", 
			search, 
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

		name = "030.030 Open assessment /api/assessments/[id]"
		headers = self.header.copy()
		response = self.client.get(
			"/api/assessments/" + str(assessment_id) + "?_=" + str(int(time.time())),
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)
		return (response.json(), response.headers["Etag"], response.headers["Last-Modified"])

	def add_comment(self, assessment_id, assessment_json, etag, last_mod):

		context = assessment_json["assessment"]["context"]

		fake = Faker()
		comment = [{"comment": {
			"description":"<p>" + fake.text(max_nb_chars=1024) + "</p>",
			"created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
			"modified_by":{"type":"Person","id": self.user_id},
			"comment":{
				"context_id": "null",
				"href":"/api/contexts/13",
				"type":"Context",
				"id":13
			},
			"send_notification": "true",
			"context":{
				"context_id": "null",
				"href":"/api/contexts/13",
				"type":"Context",
				"id":13
			},
			"assignee_type":"Creators"
		}}]
		comment[0]["comment"]["comment"].update(context)
		comment[0]["comment"]["context"].update(context)

		name = "040.010 Add comment /api/comments"
		headers = self.header.copy()
		headers.update({"Content-Type": "application/json"})
		headers.update({"X-Requested-By": "GGRC"})
		headers.update({"X-Requested-With": "XMLHttpRequest"})

		response = self.client.post("/api/comments", 
			None,
			comment,
			headers=headers,
			name=name
		)
		comment_id = response.json()[0][1]["comment"]["id"]
		logging.info('%s : %s', name, response.status_code)

		action = {"actions": {
					"add_related": [{
						"id": comment_id,
						"type": "Comment"
					}]
				}}
		assessment_json["assessment"].update(action)

		name = "040.020 Add comment (link to assessment) /api/assessments/[id]"
		headers = self.header.copy()
		headers.update({"Content-Type": "application/json"})
		headers.update({"X-Requested-By": "GGRC"})
		headers.update({"X-Requested-With": "XMLHttpRequest"})
		headers.update({"Accept": "application/json, text/javascript, */*; q=0.01"})
		headers.update({"If-Match": etag})
		headers.update({"If-Unmodified-Since": last_mod})

		response = self.client.put("/api/assessments/" + str(assessment_id), 
			json.dumps(assessment_json),
			headers=headers,
			name=name
		)
		logging.info('%s : %s', name, response.status_code)

	@task(1)
	def user_behavior(self):
		
		""" Locust creates UserBehavior object per virtual user but not per iteration"""
		""" I can't find an easy way how to get number of current thread/iteration from Locust """
		""" Probably custom object should be implemented to save iteration specific data - username/edited items etc"""

#		global iteration
#		iteration = iteration + 1
#		iteration_id = iteration

		""" Locust can't group time of several calls into one transaction """
		""" Probably this can be done after Locust deep investigation """

		""" Open home page """
		self.home_page()
		""" Open dashboard """
		self.dashboard()
		""" Search assessments available for user """
		assessment_id = self.search_assesments()
		""" Open random assessment """
		assessment_json, etag, last_mod = self.open_assessment(assessment_id)
		""" Adding comment to assessment """
		""" Adding comment requires if-match/if-unmodified-since headers from open assessment page """
		self.add_comment(assessment_id, assessment_json, etag, last_mod)


class WebsiteUser(HttpLocust):
	task_set = UserBehavior
	min_wait = 1000
	max_wait = 3000

