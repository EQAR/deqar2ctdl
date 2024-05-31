#!/usr/bin/env python3

import argparse
import coloredlogs
import logging
import os
import uuid
import json

import requests

from urllib.parse import urljoin

from deqarclient.api import EqarApi
from deqarclient.auth import EqarApiInteractiveAuth


class NotYetImplemented(Exception):
    pass


class DeqarIterator:
    """
    Iterate over DEQAR objects
    """
    PATH_TEMPLATE = None
    ID_SEQUENCE = None

    def __init__(self, api, sequence=None):
        self.api = api
        self.id_iterator = iter(sequence or self.ID_SEQUENCE)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            object_id = next(self.id_iterator)
        except StopIteration:
            raise StopIteration

        return self.api.get(self.PATH_TEMPLATE % object_id)

class AgencyIterator(DeqarIterator):
    """
    Agencies
    """
    PATH_TEMPLATE = '/webapi/v2/browse/agencies/%s'
    ID_SEQUENCE = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 27, 37 ]

class ReportIterator(DeqarIterator):
    """
    QA Reports
    """
    PATH_TEMPLATE = '/webapi/v2/browse/reports/%s'
    ID_SEQUENCE = [ 2, 9913, 78053, 47851, 190, 211, 83359, 78828, 93411, 87996, 48198, 49779, 9698, 97454, 49780, 9824, 101457, 101456, 101455, 101454, 101453, 101452, 101451, 101450, 101449, 101448, 101447, 101446, 101445, 101444, 101443, 101442, 101441 ]

class CredentialRegistryApi:
    """
    Interactions with the Credential Registry (lookup, format, publish)
    """
    _version = '0.1'

    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.req = requests.Session()
        self.req.headers.update({
            'user-agent': f'EQAR-CTDL-pilot/{self._version} ' + self.req.headers['User-Agent'],
            'accept': 'application/json',
            'authorization': f'ApiToken {token}',
        })

    def format(self, data):
        r = self.req.post(urljoin(self.url, 'assistant/CredentialingAction/format'), json=data)
        r.raise_for_status()
        response = r.json()
        if response['Successful']:
            return json.loads(response['Payload'])
        else:
            raise Exception(response['Messages'])

    def publish(self, data):
        r = self.req.post(urljoin(self.url, 'assistant/CredentialingAction/publish'), json=data)
        r.raise_for_status()
        response = r.json()
        if response['Successful']:
            return { k: response[k] for k in ("Successful", "CTID", "CredentialFinderUrl", "EnvelopeUrl", "GraphUrl") }
        else:
            raise Exception(response['Messages'])


def make_ctid(uri):
    """
    create CTID based on UUID v5 from DEQAR URL
    """
    return f'ce-{uuid.uuid5(uuid.NAMESPACE_URL, uri)}'


class AgencyAction:
    """
    Represent registered agency as QAAction
    """

    EQAR_CTID = "ce-be0685bc-fa10-4529-9a1a-a667881c2007"
    INSTRUMENT_CTID = "ce-1f75547d-e352-42fc-873d-4044bf23f806" # ESG 2015 Agency Registration
    URI_TEMPLATE = "https://data.test.deqar.eu/agency/%s/registration"
    PAGE_TEMPLATE = "https://data.deqar.eu/agency/%s"

    def __init__(self, data):
        self.data = data
        if not self.data['is_registered']:
            raise NotYetImplemented('class only supports currently registered agencies so far')

    @property
    def name_primary(self):
        for name in self.data['names']:
            if name['name_valid_to'] is None:
                for version in name['name_versions']:
                    if version['name_is_primary']:
                        return version['name']

    @property
    def acronym_primary(self):
        for name in self.data['names']:
            if name['name_valid_to'] is None:
                for version in name['name_versions']:
                    if version['acronym_is_primary']:
                        return version['acronym']

    def serialize(self):
        ref_id = f"_:{uuid.uuid4()}"
        return {
            "CredentialingAction": {
                "Type": "ApproveAction",
                "Name": f"{self.acronym_primary} Registration",
                "Description": f"{self.name_primary} ({self.acronym_primary}) has demonstrated substantial compliance with the ESG and is registered on EQAR",
                "CTID": make_ctid(self.URI_TEMPLATE % self.data['deqar_id']),
                "Instrument": [
                    self.INSTRUMENT_CTID
                ],
                "ActingAgent": [
                    {
                        "CTID": self.EQAR_CTID
                    }
                ],
                "EvidenceOfAction": self.PAGE_TEMPLATE % self.data['deqar_id'],
                "Object": ref_id,
                "StartDate": self.data['registration_start'],
                "EndDate": self.data['registration_valid_to']
            },
            "ReferenceObjects": [
                {
                    "Id": ref_id,
                    "Type": "ceterms:QACredentialOrganization",
                    "Name": f"{self.name_primary} ({self.acronym_primary})",
                    "Description": self.data['description_note'],
                    "SubjectWebpage": self.PAGE_TEMPLATE % self.data['deqar_id']
                }
            ],
            "PublishForOrganizationIdentifier": self.EQAR_CTID,
            "DefaultLanguage": "en-US"
        }


class ReportAction:
    """
    Represent DEQAR report as QAAction
    """

    EQAR_CTID = "ce-be0685bc-fa10-4529-9a1a-a667881c2007"
    ACTIVITY_TYPE_CTID = {
        "joint programme": "ce-7340b2df-d2b1-5bd6-bef8-22506322a11b",           # ESG 2015 Joint Programme External Quality Assurance
        "institutional": "ce-92560c7e-3106-569d-9c91-304cc9f17684",             # ESG 2015 Institutional External Quality Assurance
        "institutional/programme": "ce-bc9b47c0-1c29-589f-b9aa-89924f0e44be",   # ESG 2015 Mixed Institutional/Programme External Quality Assurance
        "programme": "ce-0ab77ad3-cfdf-5b0c-8978-5195c3170bcc",                 # ESG 2015 Programme-Level External Quality Assurance
    }
    URI_TEMPLATE = "https://data.test.deqar.eu/report/%s"
    AGENCY_PAGE_TEMPLATE = "https://data.deqar.eu/report/%s"
    REPORT_PAGE_TEMPLATE = "https://data.deqar.eu/report/%s"
    PROVIDER_PAGE_TEMPLATE = "https://data.deqar.eu/institution/%s"

    def __init__(self, data):
        self.data = data
        if self.data['decision'] == 'negative':
            raise NotYetImplemented(f"Report ID {self.data['id']}: class only supports positive or no decision")
        if 'programmes' in self.data and len(self.data['programmes']) > 1:
            raise NotYetImplemented(f"Report ID {self.data['id']}: clustered programme reports currently cannot be exported to CTDL")
        if len(self.data['institutions']) > 1 and self.data['agency_esg_activity_type'] != 'joint programme':
            raise NotYetImplemented(f"Report ID {self.data['id']}: class only supports joint programme reports on multi-institution")

    @property
    def institution_names(self):
        return " / ".join([ i['name_primary'] for i in self.data['institutions'] ])

    @property
    def name(self):
        if self.data['agency_esg_activity_type'] in [ 'programme', 'joint programme' ]:
            return f"{self.data['name']}: {self.data['programmes'][0]['name_primary']}, {self.institution_names}"
        else:
            return f"{self.data['name']}: {self.institution_names}"

    def serialize(self):
        ref_id = f"_:{uuid.uuid4()}"
        record = {
            "CredentialingAction": {
                "Type": "AccreditAction",
                "Name": self.name,
                "Description": f"Externally quality-assured in line with the ESG / Activity: {self.data['agency_esg_activity']} / Decision: {self.data['decision']} / Status: {self.data['status']}",
                "CTID": make_ctid(self.URI_TEMPLATE % self.data['id']),
                "Instrument": [
                    self.ACTIVITY_TYPE_CTID[self.data["agency_esg_activity_type"]]
                ],
                "ActingAgent": [
                    {
                        "Type": "ceterms:QACredentialOrganization",
                        "Name": f"{self.data['agency_name']} ({self.data['agency_acronym']})",
                        "SubjectWebpage": self.AGENCY_PAGE_TEMPLATE % self.data['agency_id']
                    },
                    {
                        "CTID": self.EQAR_CTID
                    }
                ],
                #"Participant": [
                #   {
                #       "CTID": self.EQAR_CTID
                #   }
                #],
                "EvidenceOfAction": self.REPORT_PAGE_TEMPLATE % self.data['id'],
                "Object": ref_id,
                "StartDate": self.data['valid_from']
            },
            "PublishForOrganizationIdentifier": self.EQAR_CTID,
            "DefaultLanguage": "en-US"
        }
        if self.data['valid_to']:
            record["CredentialingAction"]["EndDate"] = self.data['valid_to']

        def serialise_institution(institution):
            return {
                "Type": "ceterms:CredentialOrganization",
                "Name": institution['name_primary'],
                "Description": institution['deqar_id'] + ", " +
                    ( "other provider" if institution['is_other_provider'] else "higher education institution" ),
                "SubjectWebpage": self.PROVIDER_PAGE_TEMPLATE % institution['id'],
            }

        if self.data['agency_esg_activity_type'] in [ 'programme', 'joint programme' ]:
            ref_object = {
                "Id": ref_id,
                "Type": "LearningProgram",
                "Name": self.data['programmes'][0]['name_primary'],
                "Description": f"{self.data['programmes'][0]['programme_type']}, {self.data['programmes'][0]['qf_ehea_level']}",
                "OfferedBy": []
            }
            for inst in self.data['institutions']:
                ref_object["OfferedBy"].append(serialise_institution(inst))
        else:
            ref_object = serialise_institution(self.data['institutions'][0])
            ref_object["Id"] = ref_id
        record["ReferenceObjects"] = [ ref_object ]
        return record

################
### __main__ ###
################

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--base", help="Base URL to the DEQAR admin API (can also be set as DEQAR_BASE environment variable)")
    parser.add_argument("-c", "--credreg", help="Base URL to the Credential Registry APIs (can also be set as CREDREG_BASE environment variable)")
    parser.add_argument("-n", "--dry-run", help="Format only, but do not publish", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        coloredlogs.install(level='DEBUG')
    else:
        coloredlogs.install(level='INFO', fmt='%(name)s: %(message)s')
    logger = logging.getLogger(__name__)

    if args.base:
        api = EqarApi(args.base, authclass=EqarApiInteractiveAuth)
    elif 'DEQAR_BASE' in os.environ and os.environ['DEQAR_BASE']:
        api = EqarApi(os.environ['DEQAR_BASE'], authclass=EqarApiInteractiveAuth)
    else:
        raise Exception("Base URL needs to be passed as argument or in DEQAR_BASE environment variable")

    if 'CREDREG_TOKEN' not in os.environ:
        raise Exception("Credential Registry API token needs to be in CREDREG_TOKEN environment variable")

    if args.credreg:
        cr_api = CredentialRegistryApi(args.credreg, os.environ['CREDREG_TOKEN'])
    elif 'CREDREG_BASE' in os.environ and os.environ['CREDREG_BASE']:
        cr_api = CredentialRegistryApi(os.environ['CREDREG_BASE'], os.environ['CREDREG_TOKEN'])
    else:
        raise Exception("Base URL needs to be passed as argument or in CREDREG_BASE environment variable")

    ################

    for agency in AgencyIterator(api):
        try:
            srlzr = AgencyAction(agency)
        except NotYetImplemented as e:
            print(f'\n============== Agency {agency["deqar_id"]} ====================================================\nException: {e}')
            continue
        print(f'\n============== {srlzr.acronym_primary} ====================================================\n')
        if args.dry_run:
            print(json.dumps(cr_api.format(srlzr.serialize()), indent=4, sort_keys=True))
        else:
            print(json.dumps(cr_api.publish(srlzr.serialize()), indent=4, sort_keys=True))

    for report in ReportIterator(api):
        try:
            srlzr = ReportAction(report)
        except NotYetImplemented as e:
            print(f'\n===== Report {report["id"]} ====================================================\nException: {e}')
            continue
        print(f'\n===== {srlzr.name} =====\n')
        if args.dry_run:
            print(json.dumps(cr_api.format(srlzr.serialize()), indent=4, sort_keys=True))
        else:
            print(json.dumps(cr_api.publish(srlzr.serialize()), indent=4, sort_keys=True))

