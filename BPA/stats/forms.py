from django import forms

class LimitForm(forms.Form):
	OPTIONS = (
			("All", "All"),
			("NL", "No Limit"),
			("PL", "Pot Limit"),
			("L", "Limit"),
		)
	Limits = forms.MultipleChoiceField(widget=forms.SelectMultiple, choices = OPTIONS)