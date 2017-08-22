from django.forms.widgets import TextInput
from django.utils.dateparse import parse_duration

class DurationInput(TextInput):
	input_type = 'number'