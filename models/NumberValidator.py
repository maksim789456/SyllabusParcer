from prompt_toolkit.validation import Validator, ValidationError


class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(message='Введите пожалуйста число')
