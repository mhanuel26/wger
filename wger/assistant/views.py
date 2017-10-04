from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson as json
from wger.assistant.models import myPersonalNavigator


@csrf_exempt
def webhook(request):
	if request.method=='POST':
		received_json_data = json.loads(request.body.decode("utf-8"))
		parameters = received_json_data['result']['parameters']
		print(parameters)
		data = ''
		response = ''
		try:
			if 'new_workout' in parameters.keys():
				try:
					data = myPersonalNavigator.at_the_gym(date_time=parameters['date-time'])
				except:
					response = "Did you have a scheduled workout?"
					return JsonResponse({"speech": response, "displayText": response})
				if 'date-time' in parameters.keys():
					response = "you arrive at %s" % parameters['date-time']
			elif 'workout' in parameters.keys():
				try:
					data = myPersonalNavigator.workout_info(date_time=parameters['date-time'])
				except:
					response = "Could not get Workout details"
					return JsonResponse({"speech": response, "displayText": response})
				if data == '':
					response = "Could not get Workout details"
				else:
					response = "Filling table with workout details"
			elif 'sequence' in parameters.keys():
				try:
					data = myPersonalNavigator.workout_sequence(sequence=parameters['sequence'])
					response = '' # API client will handle this
				except:
					response = "Are you at the gym? Let me know to be in a correct state!"
			elif 'exercise_action' in parameters.keys():
				try:
					data = myPersonalNavigator.workout_action(parameters=parameters)
					response = ''  # API client will handle this
				except:
					response = "You are not in a state to do any action!"
			elif 'perfoming' in parameters.keys():
				try:
					data = myPersonalNavigator.perform_exercise()
					response = "Load the bar and lift hard"
				except:
					response = "You are already performing"
			else:
				response = "Sorry didn't get that"
		except KeyError:
			response = "Sorry didn't get that"
		return JsonResponse({"speech": response, "displayText": response, "data" : data })
	return HttpResponse("Error processing POST")