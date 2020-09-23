from prompt_toolkit.validation import Validator, ValidationError
import re


class ColumnsValidator(Validator):
    def validate(self, document):
        ok = re.match(r'^[0-9](,[0-9])*$', document.text)
        if not ok:
            raise ValidationError(message='Введите пожайлуста стобцы в формате: 0,1,2,3')
