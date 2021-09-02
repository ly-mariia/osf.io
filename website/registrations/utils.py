# -*- coding: utf-8 -*-
import re
import csv
import io
import functools
import json

from rest_framework.exceptions import NotFound, ValidationError

from osf.models.licenses import NodeLicense
from osf.models import AbstractNode, RegistrationProvider, Subject, RegistrationSchema, Institution
from website import settings


METADATA_FIELDS = {'title': {'format': 'string', 'required': True},
                   'description': {'format': 'string', 'required': True},
                   'admin': {'format': 'list', 'required': True},
                   'read-write': {'format': 'list'},
                   'read-only': {'format': 'list'},
                   'bibliographic contributors': {'format': 'list'},
                   'category': {'format': 'string'},
                   'affiliated institutions': {'format': 'list'},
                   'license': {'format': 'object', 'required': True},
                   'subjects': {'format': 'list', 'required': True},
                   'tags': {'format': 'list'},
                   'project guid': {'format': 'string'},
                   'external id': {'format': 'string'}}
CONTRIBUTOR_METADATA_FIELDS = ['admin', 'read-write', 'read-only', 'bibliographic contributors']

class BulkRegistrationUpload():
    @property
    def is_valid(self):
        return not len(self.errors)

    def __init__(self, bulk_upload_csv, provider_id):
        self.raw_csv = bulk_upload_csv.read()
        # self.raw_csv = bulk_upload_csv.read().decode('utf-8')
        self.reader = csv.DictReader(io.StringIO(self.raw_csv))
        self.headers = [header.lower() for header in self.reader.fieldnames]
        schema_id_row = next(self.reader)
        self.schema_id = schema_id_row[self.reader.fieldnames[0]]
        self.provider_id = provider_id
        if self.schema_id:
            try:
                self.registration_provider = RegistrationProvider.load(self.provider_id)
                self.registration_schema = self.registration_provider.schemas.get(_id=self.schema_id)
            except RegistrationSchema.DoesNotExist:
                raise NotFound(detail='Schema with id "{}" was not found'.format(self.schema_id))
            except RegistrationProvider.DoesNotExist:
                raise NotFound(detail='Registration provider with id "{}" was not found').format(self.provider_id)
        self.schema_questions = BulkRegistrationUpload.get_questions_validations(self.registration_schema)
        self.validations = {**self.schema_questions, **METADATA_FIELDS}
        self.errors = []
        self.rows = [Row(row,
                         self.validations,
                         functools.partial(self.log_error, row_index=self.reader.line_num))
                     for row in self.reader]

    @classmethod
    def get_questions_validations(cls, registration_schema):
        schema_questions = {}
        get_question_validations = lambda question: {'required': question.get('required', False),
                                   'format': question.get('format', ''),
                                   'type': question.get('type', 'string'),
                                   'options': question.get('options', [])}
        for page in registration_schema.schema['pages']:
            for question in page['questions']:
                schema_questions[question['qid']] = get_question_validations(question)
                if 'properties' in question:
                    for nested_question in question['properties']:
                        qid="{}{}".format(question['qid'], nested_question['id'])
                        schema_questions[qid] = get_question_validations(nested_question)
        return schema_questions

    def log_error(self, **kwargs):
        self.errors.append({
            'header': kwargs['header'],
            # TODO: add a method to generate human friendly excel column index
            'column_index': kwargs['column_index'],
            'row_index': kwargs['row_index'],
            'missing': kwargs.get('missing', False),
            'invalid': kwargs.get('invalid', False)
        })

    def validate_csv_header_list(self):
        expected_headers = self.validations.keys()
        actual_headers = self.headers
        diff = set(expected_headers) - set(actual_headers)
        if len(diff):
            raise ValidationError('Invalid csv headers: {}'.format(','.join(diff)))

    def get_parsed(self):
        parsed = []
        for row in self.rows:
            parsed.append({ 'csv_raw': row.get_raw_value(), 'csv_parsed': row.get_parsed_value()})
        return {'schema_id': self.schema_id, 'registrations': parsed}

    def validate(self):
        self.validate_csv_header_list()
        for row in self.rows:
            row.validate()

class Row():
    def __init__(self, row_dict, validations, log_error):
        self.row_dict = row_dict
        self.cells = [Cell(header.lower(),
                           value, validations[header.lower()],
                           functools.partial(log_error, column_index=column_index))
                           for column_index, (header, value) in enumerate(row_dict.items())]

    def to_json(self):
        json_value = {}
        for cell in self.cells:
            json_value.update(cell.get_parsed_value())
        return json.dumps(json_value)

    def get_metadata(self):
        parsed_metadata = {}
        for cell in self.cells:
            if cell.is_metadata:
                parsed_metadata.update(cell.get_parsed_value())
        return parsed_metadata

    def get_registration_responses(self):
        parsed_responses = {}
        for cell in self.cells:
            if not cell.is_metadata:
                parsed_responses.update(cell.get_parsed_value())
        return parsed_responses

    def get_parsed_value(self):
        return {'metadata': self.get_metadata(),
                'registration_responses': self.get_registration_responses()}

    def get_raw_value(self):
        raw_value = []
        for cell in self.cells:
            raw_value.append(cell.get_raw_value())
        return ','.join(raw_value)

    def validate(self):
        for cell in self.cells:
            cell.validate()

class Cell():
    @property
    def is_metadata(self):
        return self.header in METADATA_FIELDS.keys()

    def __init__(self, header, value, validations, log_error):
        self.header = header
        self.value = value
        self.validations = validations
        self.field = Cell.field_instance_for(self.header.lower(),
                                             value=self.value,
                                             validations=self.validations,
                                             log_error=functools.partial(log_error, header=self.header))

    def validate(self):
        self.field.parse()

    def get_parsed_value(self):
        return {self.header: self.field.parse()}

    def get_raw_value(self):
        return self.value

    def to_json(self):
        return json.dumps({self.header: self.field.parse()})

    @classmethod
    def field_instance_for(cls, name, **kwargs):
        field_instance = None
        if name in METADATA_FIELDS.keys():
            if name in CONTRIBUTOR_METADATA_FIELDS:
                field_instance = ContributorField(**kwargs)
            elif name == 'license':
            	field_instance = LicenseField(**kwargs)
            elif name == 'category':
                field_instance = CategoryField(**kwargs)
            elif name == 'subjects':
                field_instance = SubjectsField(**kwargs)
            elif name == 'affiliated institutions':
                field_instance = InstitutionsField(**kwargs)
            elif name == 'project guid':
                field_instance = ProjectIDField(**kwargs)
            else:
                field_instance = MetadataField(**kwargs)
        else:
            field_instance = RegistrationResponseField(**kwargs)
        return field_instance

class RegistrationResponseField():
    def __init__(self, **kwargs):
        response_validations = kwargs['validations']
        self.required = response_validations.get('required', False)
        self.type = response_validations.get('type', 'string')
        self.format = response_validations.get('format')
        self.options = response_validations.get('options', [])
        self.value = kwargs.get('value', '').strip()
        self.log_error = kwargs['log_error']
        self._parsed_value = None

    def _validate(self):
        parsed_value = None
        if self.required and not bool(self.value):
            self.log_error(missing=True)
        else:
            if self.type == 'string':
                parsed_value = self.value
            elif self.type == 'choose' and self.format in ['singleselect', 'multiselect']:
                if self.format == 'singleselect':
                    if self.value not in self.options:
                        self.log_error(invalid=True)
                    else:
                        parsed_value = self.value
                else:
                    parsed_value = []
                    choices = [val.strip() for val in self.value.split(';')]
                    for choice in choices:
                        if choice not in self.options:
                            self.log_error(invalid=True)
                        else:
                            parse_value.append(choice)
            self._parsed_value = parsed_value

    def parse(self):
        if self._parsed_value is None:
            self._validate()
        return self._parsed_value if self._parsed_value is not None else ''

class MetadataField():
    def __init__(self, **kwargs):
        metadata_validations = kwargs['validations']
        self.format = metadata_validations.get('format', 'string')
        self.required = metadata_validations.get('required', False)
        self.value = kwargs.get('value', '').strip()
        self.log_error = kwargs.get('log_error')
        self._parsed_value = None

    def _validate(self):
        parsed_value = None
        if self.required and not bool(self.value):
            self.log_error(missing=True)
        else:
            if self.format == 'string':
                parsed_value = self.value
            elif self.format == 'list':
                parsed_value = [val.strip() for val in self.value.split(';')]
            self._parsed_value = parsed_value

    def parse(self):
        if self._parsed_value is None:
            self._validate()
        return self._parsed_value if self._parsed_value is not None else ''

class ContributorField(MetadataField):
    # format: contributor_name<contributor_email>;contributor_name<contributor_email>
    contributor_regex = re.compile(r'(?P<full_name>[\w -]+)<(?P<email>.*?)>')
    def _validate(self):
        parsed_value = None
        if self.required and not bool(self.value):
            self.log_error(missing=True)
        else:
            parsed_value = []
            parsed_contributor_list = [val.strip() for val in self.value.split(';')]
            # TODO: use re.findall()
            for contrib in parsed_contributor_list:
                match = self.contributor_regex.match(contrib.strip())
                if match:
                    try:
                        full_name = match.group('full_name')
                        email = match.group('email')
                    except AttributeError:
                        self.log_error(invalid=True)
                    else:
                        parsed_value.append({'full_name': full_name, 'email': email})
            self._parsed_value = parsed_value

class LicenseField(MetadataField):
    # format: license_name;year;copyright_holder_one,copyright_holder_two,...
    with_required_fields_regex = re.compile(r'(?P<name>[\w ]+);(?P<year>[ ][1-3][0-9]{3});(?P<copyright_holders>[\w -,]+)')
    no_required_fields_regex = re.compile(r'(?P<name>[\w ]+)')

    def _validate(self):
        parsed_value = None
        if self.required and not bool(self.value):
            self.log_error(missing=True)
        else:
            license_name_match = self.no_required_fields_regex.match(self.value)
            if license_name_match is not None:
                node_license_name = license_name_match.group('name')
                try:
                    node_license = NodeLicense.objects.get(name__iexact=node_license_name)
                except NodeLicense.DoesNotExist:
                    self.log_error(invalid=True)
                else:
                    has_required_fields = bool(node_license.properties)
                    if has_required_fields:
                        match = self.with_required_fields_regex.match(self.value)
                        if match is not None:
                            name = match.group('name')
                            year = match.group('year')
                            copyright_holders = match.group('copyright_holders')
                            copyright_holders = [val.strip() for val in copyright_holders.split(',')]
                            parsed_value = {'name': name,
                                            'required_field': {'year': year,
                                                               'copyright_holders': copyright_holders}}
                    else:
                        parsed_value = {'name': node_license_name}
                    self._parsed_value = parsed_value
            else:
                self.log_error(invalid=True)

class CategoryField(MetadataField):
    def _validate(self):
        try:
            self._parsed_value = settings.NODE_CATEGORY_MAP[self.value]
        except KeyError:
            self.log_error(invalid=True)

class SubjectsField(MetadataField):
    def _validate(self):
        subjects = [val.strip() for val in self.value.split(';')]
        valid_subjects = list(Subject.objects.filter(text__in=subjects).values_list('text', flat=True))
        invalid_subjects = list(set(subjects) - set(valid_subjects))
        if len(invalid_subjects):
            self.log_error(invalid=True)
        else:
            self._parsed_value = valid_subjects

class InstitutionsField(MetadataField):
    def _validate(self):
        institutions = [val.strip() for val in self.value.split(';')]
        valid_institutions = list(Institution.objects.filter(name__in=institutions).values_list('name', flat=True))
        invalid_institutions = list(set(institutions) - set(valid_institutions))
        if len(invalid_institutions):
            self.log_error(invalid=True)
        else:
            self._parsed_value = valid_institutions

class ProjectIDField(MetadataField):
    def _validate(self):
        try:
            project = AbstractNode.objects.get(guids___id=self.value, is_deleted=False, type='osf.node')
        except AbstractNode.DoesNotExist:
            self.log_error(invalid=True)
        else:
            self._parsed_value = self.value
