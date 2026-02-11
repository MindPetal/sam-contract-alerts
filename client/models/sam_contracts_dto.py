"""Combined SAM.gov contract models"""
import pprint
import six


class ReasonForModification(object):
    """Reason for contract modification"""

    types = {"name": "str"}
    attribute_map = {"name": "name"}

    def __init__(self, name=None):
        self._name = None
        self.discriminator = None
        if name is not None:
            self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(ReasonForModification, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, ReasonForModification):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class ContractId(object):
    """Contract identification details"""

    types = {
        "piid": "str",
        "modification_number": "str",
        "reason_for_modification": "ReasonForModification",
    }
    attribute_map = {
        "piid": "piid",
        "modification_number": "modificationNumber",
        "reason_for_modification": "reasonForModification",
    }

    def __init__(self, piid=None, modification_number=None, reason_for_modification=None):
        self._piid = None
        self._modification_number = None
        self._reason_for_modification = None
        self.discriminator = None
        if piid is not None:
            self.piid = piid
        if modification_number is not None:
            self.modification_number = modification_number
        if reason_for_modification is not None:
            self.reason_for_modification = reason_for_modification

    @property
    def piid(self):
        return self._piid

    @piid.setter
    def piid(self, piid):
        self._piid = piid

    @property
    def modification_number(self):
        return self._modification_number

    @modification_number.setter
    def modification_number(self, modification_number):
        self._modification_number = modification_number

    @property
    def reason_for_modification(self):
        return self._reason_for_modification

    @reason_for_modification.setter
    def reason_for_modification(self, reason_for_modification):
        self._reason_for_modification = reason_for_modification

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(ContractId, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, ContractId):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class Dates(object):
    """Contract dates"""

    types = {"date_signed": "str"}
    attribute_map = {"date_signed": "dateSigned"}

    def __init__(self, date_signed=None):
        self._date_signed = None
        self.discriminator = None
        if date_signed is not None:
            self.date_signed = date_signed

    @property
    def date_signed(self):
        return self._date_signed

    @date_signed.setter
    def date_signed(self, date_signed):
        self._date_signed = date_signed

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(Dates, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, Dates):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class Dollars(object):
    """Contract dollar amounts"""

    types = {"action_obligation": "str"}
    attribute_map = {"action_obligation": "actionObligation"}

    def __init__(self, action_obligation=None):
        self._action_obligation = None
        self.discriminator = None
        if action_obligation is not None:
            self.action_obligation = action_obligation

    @property
    def action_obligation(self):
        return self._action_obligation

    @action_obligation.setter
    def action_obligation(self, action_obligation):
        self._action_obligation = action_obligation

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(Dollars, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, Dollars):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class AwardeeHeader(object):
    """Awardee header information"""

    types = {"awardee_name": "str", "legal_business_name": "str"}
    attribute_map = {
        "awardee_name": "awardeeName",
        "legal_business_name": "legalBusinessName",
    }

    def __init__(self, awardee_name=None, legal_business_name=None):
        self._awardee_name = None
        self._legal_business_name = None
        self.discriminator = None
        if awardee_name is not None:
            self.awardee_name = awardee_name
        if legal_business_name is not None:
            self.legal_business_name = legal_business_name

    @property
    def awardee_name(self):
        return self._awardee_name

    @awardee_name.setter
    def awardee_name(self, awardee_name):
        self._awardee_name = awardee_name

    @property
    def legal_business_name(self):
        return self._legal_business_name

    @legal_business_name.setter
    def legal_business_name(self, legal_business_name):
        self._legal_business_name = legal_business_name

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(AwardeeHeader, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AwardeeHeader):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class AwardeeLocation(object):
    """Awardee location information"""

    types = {}
    attribute_map = {}

    def __init__(self):
        self.discriminator = None

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(AwardeeLocation, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AwardeeLocation):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class AwardeeData(object):
    """Awardee data"""

    types = {
        "awardee_header": "AwardeeHeader",
        "awardee_location": "AwardeeLocation",
    }
    attribute_map = {
        "awardee_header": "awardeeHeader",
        "awardee_location": "awardeeLocation",
    }

    def __init__(self, awardee_header=None, awardee_location=None):
        self._awardee_header = None
        self._awardee_location = None
        self.discriminator = None
        if awardee_header is not None:
            self.awardee_header = awardee_header
        if awardee_location is not None:
            self.awardee_location = awardee_location

    @property
    def awardee_header(self):
        return self._awardee_header

    @awardee_header.setter
    def awardee_header(self, awardee_header):
        self._awardee_header = awardee_header

    @property
    def awardee_location(self):
        return self._awardee_location

    @awardee_location.setter
    def awardee_location(self, awardee_location):
        self._awardee_location = awardee_location

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(AwardeeData, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AwardeeData):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class ProductOrServiceInformation(object):
    """Product or service information"""

    types = {"description_of_contract_requirement": "str"}
    attribute_map = {"description_of_contract_requirement": "descriptionOfContractRequirement"}

    def __init__(self, description_of_contract_requirement=None):
        self._description_of_contract_requirement = None
        self.discriminator = None
        if description_of_contract_requirement is not None:
            self.description_of_contract_requirement = description_of_contract_requirement

    @property
    def description_of_contract_requirement(self):
        return self._description_of_contract_requirement

    @description_of_contract_requirement.setter
    def description_of_contract_requirement(self, description_of_contract_requirement):
        self._description_of_contract_requirement = description_of_contract_requirement

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(ProductOrServiceInformation, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, ProductOrServiceInformation):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class AwardDetails(object):
    """Award details"""

    types = {
        "dates": "Dates",
        "dollars": "Dollars",
        "awardee_data": "AwardeeData",
        "product_or_service_information": "ProductOrServiceInformation",
    }
    attribute_map = {
        "dates": "dates",
        "dollars": "dollars",
        "awardee_data": "awardeeData",
        "product_or_service_information": "productOrServiceInformation",
    }

    def __init__(self, dates=None, dollars=None, awardee_data=None, product_or_service_information=None):
        self._dates = None
        self._dollars = None
        self._awardee_data = None
        self._product_or_service_information = None
        self.discriminator = None
        if dates is not None:
            self.dates = dates
        if dollars is not None:
            self.dollars = dollars
        if awardee_data is not None:
            self.awardee_data = awardee_data
        if product_or_service_information is not None:
            self.product_or_service_information = product_or_service_information

    @property
    def dates(self):
        return self._dates

    @dates.setter
    def dates(self, dates):
        self._dates = dates

    @property
    def dollars(self):
        return self._dollars

    @dollars.setter
    def dollars(self, dollars):
        self._dollars = dollars

    @property
    def awardee_data(self):
        return self._awardee_data

    @awardee_data.setter
    def awardee_data(self, awardee_data):
        self._awardee_data = awardee_data

    @property
    def product_or_service_information(self):
        return self._product_or_service_information

    @product_or_service_information.setter
    def product_or_service_information(self, product_or_service_information):
        self._product_or_service_information = product_or_service_information

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(AwardDetails, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AwardDetails):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class AwardSummary(object):
    """Award summary"""

    types = {
        "contract_id": "ContractId",
        "award_details": "AwardDetails",
    }
    attribute_map = {
        "contract_id": "contractId",
        "award_details": "awardDetails",
    }

    def __init__(self, contract_id=None, award_details=None):
        self._contract_id = None
        self._award_details = None
        self.discriminator = None
        if contract_id is not None:
            self.contract_id = contract_id
        if award_details is not None:
            self.award_details = award_details

    @property
    def contract_id(self):
        return self._contract_id

    @contract_id.setter
    def contract_id(self, contract_id):
        self._contract_id = contract_id

    @property
    def award_details(self):
        return self._award_details

    @award_details.setter
    def award_details(self, award_details):
        self._award_details = award_details

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(AwardSummary, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AwardSummary):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class AwardResponse(object):
    """Award API response"""

    types = {
        "award_summary": "list[AwardSummary]",
        "total_records": "str",
        "limit": "str",
        "offset": "str",
    }
    attribute_map = {
        "award_summary": "awardSummary",
        "total_records": "totalRecords",
        "limit": "limit",
        "offset": "offset",
    }

    def __init__(self, award_summary=None, total_records=None, limit=None, offset=None):
        self._award_summary = None
        self._total_records = None
        self._limit = None
        self._offset = None
        self.discriminator = None
        if award_summary is not None:
            self.award_summary = award_summary
        if total_records is not None:
            self.total_records = total_records
        if limit is not None:
            self.limit = limit
        if offset is not None:
            self.offset = offset

    @property
    def award_summary(self):
        return self._award_summary

    @award_summary.setter
    def award_summary(self, award_summary):
        self._award_summary = award_summary

    @property
    def total_records(self):
        return self._total_records

    @total_records.setter
    def total_records(self, total_records):
        self._total_records = total_records

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, limit):
        self._limit = limit

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        self._offset = offset

    def to_dict(self):
        result = {}
        for attr, _ in six.iteritems(self.types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(lambda item: (item[0], item[1].to_dict()) if hasattr(item[1], "to_dict") else item, value.items()))
            else:
                result[attr] = value
        if issubclass(AwardResponse, dict):
            for key, value in self.items():
                result[key] = value
        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, AwardResponse):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
