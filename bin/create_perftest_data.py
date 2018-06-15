#!/usr/bin/env python

""" Script to test adding comments to assessment for multiple users"""
"""
	Launch string
		python create_perftest_data.py
	Required modules from
		src/ggrc
		test/integration
	Doesn't check presense of data. It is better to run it after bin/db_reset
"""
from ggrc.models import all_models
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.access_control import acl_helper
import random

""" Creating users needed by the test cases """
""" 20 creators """
""" 20 editors """

users = []

object_generator = ObjectGenerator()

for i in range (1,21):
	name = 'PerfCreator' + ('%03d' % i)
	res, user = object_generator.generate_person(
		data={"name": name, "email": name + "@example.com"}, user_role='Creator')
	users.append(user.id)
	print('User %s, id : %s' % (name, user.id))

for i in range (1,21):
	name = 'PerfEditor' + ('%03d' % i)
	res, user = object_generator.generate_person(
		data={"name": name, "email": name + "@example.com"}, user_role='Editor')
	users.append(user.id)
	print('User %s, id : %s' % (name, user.id))

model_ac_roles = all_models.AccessControlRole.query.all()
ac_roles = {}
for ac_role in model_ac_roles:
	ac_roles[ac_role.name] = ac_role.id

prog = "001"

""" Creating program with random user """
program_creator_id = users[random.randrange(len(users))]
print('Program creator id : %s' % program_creator_id)

api = Api()
acl = [acl_helper.get_acl_json(ac_roles["Program Managers"], program_creator_id)]

response = api.post(all_models.Program, {
	"program": {
		"title": "Perf Program " + prog, 
		"context": None,
		"access_control_list": acl
	},
})
program_id = response.json.get("program").get("id")
print('Program id : %s' % program_id)

""" Creating audit with random Audit Captain """
auditcaptain_id = users[random.randrange(len(users))]
print('Audit captain id : %s' % auditcaptain_id)
acl = [acl_helper.get_acl_json(ac_roles["Audit Captains"], auditcaptain_id)]

response = api.post(all_models.Audit, {
	"audit": {
    	"title": "Program " + prog + " audit",
    	'program': {'id': program_id, "type": "Program"},
    	"status": "Planned",
    	"context": None,
		"modified_by_id": program_creator_id,
    	"access_control_list": acl
	}
})

audit_id = response.json.get("audit").get("id")
context = response.json.get("audit").get("context")

print('Audit id : %s' % audit_id)

""" Creating 1000 Audits with 2 Assignees and 2 Verifiers """

for i in range(1, 1001):
	assessment_users_ids = list(users)
	assessment_users = (
		("Creators", assessment_users_ids.pop(random.randrange(len(assessment_users_ids)))),
		("Assignees", assessment_users_ids.pop(random.randrange(len(assessment_users_ids)))),
		("Assignees", assessment_users_ids.pop(random.randrange(len(assessment_users_ids)))),
		("Verifiers", assessment_users_ids.pop(random.randrange(len(assessment_users_ids)))),
		("Verifiers", assessment_users_ids.pop(random.randrange(len(assessment_users_ids))))
	)

	acl = [acl_helper.get_acl_json(ac_roles[user[0]], user[1]) for user in assessment_users]

	response = api.post(all_models.Assessment, {
		"assessment": {
			"title": "Assessment " + ('%04d' % i),
			"context": context,
			"recipients": "Assignees,Creators,Verifiers",
			"audit": {
				"id": audit_id,
				"href": "/api/audits/" + str(audit_id),
				"type": "Audit"
			},
			"access_control_list": acl,
		},
	})

	assessment_id = response.json.get("assessment").get("id")
	print('Assessment id : %s' % assessment_id)
