# API.AI assistant model
#
# Written by Manuel Iglesias for wger Workout Manager as add on.
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

# Standard Library
import datetime
import logging
import requests
import json
import ast   # fix the double quote of json

from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from django.db.models import IntegerField
from django import forms
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator
)
from django_fsm import FSMField, transition
import datetime

logger = logging.getLogger(__name__)

STATES = ('new', 'find_workout', 'overview', 'performing', 'set_in_progress', 'set_done', 'end_workout')
STATES = list(zip(STATES, STATES))

WGER_TOKEN = 'Token c5cd813fd3568577ef2a5004fab8e5a4880a2738'

#
# Classes
#
@python_2_unicode_compatible
class workoutNavigator(models.Model):
	state = FSMField(default='new', choices=STATES, protected=False)

	exercise_number = IntegerField(verbose_name=('exercise sequence number'),
						  default=1,
                          blank=False,
                          validators=[MinValueValidator(1), MaxValueValidator(20)],
                          null=True)

	exercise_day = IntegerField(verbose_name=('exercise day number'),
						  default=0,
                          blank=False,
                          null=True)


	@transition(field=state, source='new', target='find_workout')
	def at_the_gym(self, date_time):
		# self.exercise_day will be based on the actual day of query
		# self.exercise_day = datetime.datetime.today().weekday() + 1
		# hardwired now for testing until we fill up a whole massive week ;)
		self.exercise_day = 2
		# add the workouts locally and enable following line instead of wger.de
		# url = "http://127.0.0.1:8000/api/v2/day/?day=%s" % self.exercise_day
		url = "https://wger.de/api/v2/day/?day=%d" % self.exercise_day
		headers = {'Authorization' : WGER_TOKEN}
		r = requests.get(url, headers=headers)
		if r.status_code == 200:
			recv = r.json()
			self.training = recv['results'][0]['training']
			retExJson = {}
			retExJson['Training_Number'] = self.training
			return(ast.literal_eval(json.dumps(retExJson)))
		else:
			raise Exception("day not found")

	@transition(field=state, source='find_workout', target='overview')
	def workout_info(self, date_time):
		print("training day = %d" % self.training)
		# Go get the canonical JSON
		url = "https://wger.de/api/v2/workout/%d/canonical_representation/" % self.training
		headers = {'Authorization' : WGER_TOKEN}
		# url = "https://wger.de/api/v2/set/?exerciseday=%s"  % self.exercise_day
		r = requests.get(url, headers=headers)
		if r.status_code == 200:
			canonical = r.json()
			# Loop over all possible training days lookin for ours
			day_index = None
			for item in range(len(canonical['day_list'])):
				if canonical['day_list'][item]['obj']['day'][0] == self.exercise_day:
					day_index = item
					break
			if day_index is None:
				return "No workout schedule for Today"
			workout = canonical['day_list'][day_index]['set_list']
			# let's total super set the totakl number of sets
			tot_super_sets = len(workout)
			exList = []
			for item in range(tot_super_sets):
				# let's call it super_set buyt it can be compoesed of only one exercise
				super_set = len(workout[item]['exercise_list'])
				for ex_item in range(super_set):
					exDict = {}
					exDict['name'] = workout[item]['exercise_list'][ex_item]['obj']['name']
					exDict['reps_list'] = workout[item]['exercise_list'][ex_item]['reps_list']
					exDict['weight_list'] = workout[item]['exercise_list'][ex_item]['weight_list']
					print(exDict)
					exList.append(exDict)
			print(exList)
			retExJson = {}
			retExJson['Exercise_List'] = exList
			return(ast.literal_eval(json.dumps(retExJson)))
		else:
			raise Exception("day not found")

	@transition(field=state, source='overview', target='overview')
	def workout_sequence(self, sequence):
		# for now just build a response, but this method will
		# * allow correct state transition
		# * provide addictional features
		retExJson = {}
		retExJson['sequence'] = sequence
		return(ast.literal_eval(json.dumps(retExJson)))

	# @transition(field=state, source='overview', target='performing')
	def perform_exercise(self):
		retExJson = {}
		retExJson["perform"] = "True"
		return(ast.literal_eval(json.dumps(retExJson)))

	# @transition(field=state, source='performing', target=['performing', 'overview'])
	def workout_action(self, parameters):
		# self.state = 'performing'
		action = parameters['exercise_action']
		parameter = 'action'
		parse_action = {}
		parse_action['error'] = "NoErr"
		if action == "start set" or action == "go" or action == "let's go":
			# application action
			parse_action['log_entry'] = 'new'
		elif action == "change weight":
			if 'number-integer' in parameters.keys():
				parse_action['weight'] = parameters['number-integer']
			else:
				parse_action['error'] = "WtErr"
		elif action == "add set":
			pass
		elif action == "done with set":
			# some houskeeping such as receiving log of this exercise
			pass
			# self.state = 'overview'
		else:
			pass
			# self.state = 'overview'
		retExJson = {}
		retExJson[parameter] = parse_action
		return(ast.literal_eval(json.dumps(retExJson)))

myPersonalNavigator = workoutNavigator()
