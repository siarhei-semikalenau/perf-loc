#!/usr/bin/env python

'''
	Test to check GGRC-2857
	Works only on empty db
	Deletes all created objects after test
'''

#import unittest
from integration.ggrc import TestCase, read_imported_file
from integration.ggrc.api_helper import Api
from integration.ggrc.access_control import acl_helper
from integration.ggrc.query_helper import WithQueryApi
from ggrc.models import all_models
from StringIO import StringIO
from mock import patch

class TestGGRC2857(TestCase, WithQueryApi):

	def setUp(self):
		self.client.get("/login")
		self.api = Api()
		program_creator_id = 1;

		#		acl = [acl_helper.get_acl_json(ac_roles["Program Managers"], program_creator_id)]

		""" Create Program """

		response = self.api.post(all_models.Program, {
			"program": {
				"title": "Program GGRC-2857", 
				"context": None,
				"access_control_list": [] #acl
			},
		})
		self.program_id = response.json.get("program").get("id")
#		print('Program id : %s' % self.program_id)

		""" Create Audit """

		response = self.api.post(all_models.Audit, {
			"audit": {
    			"title": "Program GGRC-2857 audit",
    			'program': {'id': self.program_id, "type": "Program"},
    			"status": "Planned",
    			"context": None,
				"modified_by_id": program_creator_id,
    			"access_control_list": []
			}
		})

		self.audit_id = response.json.get("audit").get("id")
		context = response.json.get("audit").get("context")

#		print('Audit id : %s' % self.audit_id)

		""" Create Assessment """

		response = self.api.post(all_models.Assessment, {
			"assessment": {
				"title": "Assessment GGRC-2857",
				"context": context,
				"recipients": "Assignees,Creators,Verifiers",
				"audit": {
					"id": self.audit_id,
					"href": "/api/audits/" + str(self.audit_id),
					"type": "Audit"
				},
				"access_control_list": [],
			},
		})

		self.assessment_id = response.json.get("assessment").get("id")
#		print('Assessment id : %s' % self.assessment_id)

		""" Create Regulation """

		response = self.api.post(all_models.Regulation, {
			"regulation":{
				"title":"Regulation GGRC-2857",
				"recipients":"Admin,Primary Contacts,Secondary Contacts",
				"status":"Draft",
				"context": None,
				"kind":"Regulation",
				"access_control_list":[],
			},
		})
		self.regulation_id = response.json.get("regulation").get("id")
		regulation_slug = response.json.get("regulation").get("slug")
#		print('Regulation id : %s' % self.regulation_id)

		""" Map Regulation to Audit """
		response = self.api.post(all_models.Relationship, {
			"relationship":{
				"source":{
					"id":self.audit_id,
					"href":"/api/audits/"+ str(self.audit_id),
					"type":"Audit"},
				"destination":{
					"id":self.regulation_id,
					"href":"/api/regulations/" + str(self.regulation_id),
					"type":"Regulation",
				},
				"context": None,
			},			
		})
		self.relationship_id = response.json.get("relationship").get("id")
#		print('Relationship id : %s' % self.relationship_id)

		""" Export Assessment """
		data = [{
			"object_name": "Assessment",
			"filters": {
    			"expression": {},
			},
			"fields": "all",
		}]
		response = self.export_csv(data)
		
		""" Change Assessment """
		imp = (response.data.replace(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,", ",,,,,,,,,,,,,,,,,,,,,,,,"+regulation_slug+",,,,,,,",1)).encode('ascii','ignore')
		self._file = StringIO(imp)

	def tearDown(self):
		asmnt = all_models.Assessment.query.get(self.assessment_id)
		self.api.delete(asmnt)
		regul = all_models.Regulation.query.get(self.regulation_id)
		self.api.delete(regul)
		prog = all_models.Program.query.get(self.program_id)
		self.api.delete(prog)

		return

	@patch("ggrc.gdrive.file_actions.get_gdrive_file",
		new=read_imported_file)
	def test_GGRC2857(self):

		""" Import/Check Assessment """
		data = {"file": (self._file, "test.csv")}
		response = self.send_import_request(data)
		self.assertEqual(response[0]["updated"], 1, msg="Only 1 assessment should be updated")
		
		""" Check Assessment """
		self.snap_types = ["Standard", "Regulation", "Section", "Objective", "Control", "Product", "System", "Process", "AccessGroup", "Clause", "Contract", "DataAsset", "Facility", "Market", "OrgGroup", "Policy", "Risk", "Threat", "Vendor",]
		self.rel_types = ["Audit", "Evidence", "Issue",]

		query_data = []
		relevant = {"object_name": "Assessment", "op": {"name": "relevant"}, "ids": [self.assessment_id]}

		for snap_type in self.snap_types:
			child = self.make_filter_expression(expression=["child_type","=", snap_type])
			filters = {"expression": self.make_filter_expression(expression=[child, "AND", relevant])}
			query_data.append(self._make_query_dict_base("Snapshot", type_="count", filters=filters))

		filters = {"expression": relevant}
		for rel_type in self.rel_types:
			query_data.append(self._make_query_dict_base(rel_type, type_="count", filters=filters))

		response = self.api.send_request(
        	self.api.client.post,
        	data=query_data,
        	api_link="/query"
    	)
		self.assertEqual(response.json[1]["Snapshot"]["count"], 1, msg="Only 1 regulation should be relevant to our assessment")

		""" Check Regulation/Audit """
		query_data = []
		relevant = {"object_name": "Assessment", "op": {"name": "relevant"}, "ids": [self.assessment_id]}
		child = self.make_filter_expression(expression=["child_type","=", "Regulation"])
		filters = {"expression": self.make_filter_expression(expression=[child, "AND", relevant])}
		query_data.append({
				"object_name": "Snapshot",
				"filters": filters,
				"limit": [0, 1],
				"fields": ["child_id", "child_type", "context", "email", "id", "is_latest_revision", "name", "revision", "revisions", "selfLink", "slug", "status", "title", "type", "viewLink", "workflow_state", "archived", "program", "DEFAULT_PEOPLE_LABELS", "object_people", "user_roles"],
			})
		filters = {"expression": relevant}
		query_data.append({
				"object_name": "Audit",
				"filters": filters,
				"limit": [0, 1],
				"fields": ["child_id", "child_type", "context", "email", "id", "is_latest_revision", "name", "revision", "revisions", "selfLink", "slug", "status", "title", "type", "viewLink", "workflow_state", "archived", "program", "DEFAULT_PEOPLE_LABELS", "object_people", "user_roles"],
			})

		relevant = {"object_name": "Audit", "op": {"name": "relevant"}, "ids": [self.audit_id]}
		for snap_type in self.snap_types:
			child = self.make_filter_expression(expression=["child_type","=", snap_type])
			filters = {"expression": self.make_filter_expression(expression=[child, "AND", relevant])}
			query_data.append(self._make_query_dict_base("Snapshot", type_="ids", filters=filters))

		filters = {"expression": relevant}
		query_data.append({
				"object_name": "Issue",
				"filters": filters,
				"type": "ids",
			})

		response = self.api.send_request(
        	self.api.client.post,
        	data=query_data,
        	api_link="/query"
    	)
		
		self.assertEqual(response.json[0]["Snapshot"]["values"][0]["id"], self.relationship_id, msg="Relashionship Id doesn't match with created")
		self.assertEqual(response.json[1]["Audit"]["values"][0]["id"], self.audit_id, msg="Audit Id doesn't match with created")
		
		return
