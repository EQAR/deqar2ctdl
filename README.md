QA Actions Pilot DEQAR x Credential Engine
==========================================

This repository contains technical material related to [EQAR](https://www.eqar.eu) participating in a pilot on recording information on Quality Assurance Actions in the registry operated by [Credential Engine](https://credentialengine.org/).

Mapping
-------

This is an illustration how [DEQAR](https://www.deqar.eu/) objects map to [CTDL](https://credreg.net/ctdl/terms) classes and how the relationships are described in CTDL properties:

![diagram illustrating the relationship between DEQAR and CTDL data models](images/EQAR%20-%20DEQAR%20-%20CTDL%20simple%20-%20open%20issues.png)

Static data
-----------

Data on EQAR (class: QACredentialOrganization) was entered manually in the Credential Registry Sandbox, the CTID is `ce-be0685bc-fa10-4529-9a1a-a667881c2007`.

Agency registration on EQAR was set up as a QualityAssuranceCredential manually, with the CTID `ce-1f75547d-e352-42fc-873d-4044bf23f806`.

DEQAR report types were created as QualityAssuranceCredentials using the Registry Assistant API (see files under `static/`, HTTP POST requests were made to `https://sandbox.credentialengine.org/assistant/credential/publish`). These use the following CTIDs:

 - Institutional reports: `uuid.uuid5(uuid.NAMESPACE_URL,'https://data.test.deqar.eu/activity/institutional')` - `ce-92560c7e-3106-569d-9c91-304cc9f17684`
 - Programme reports: `uuid.uuid5(uuid.NAMESPACE_URL,'https://data.test.deqar.eu/activity/programme')` - `ce-0ab77ad3-cfdf-5b0c-8978-5195c3170bcc`
 - Joint programme reports: `uuid.uuid5(uuid.NAMESPACE_URL,'https://data.test.deqar.eu/activity/joint-programme')` - `ce-7340b2df-d2b1-5bd6-bef8-22506322a11b`
 - Mixed institutional/programme reports: `uuid.uuid5(uuid.NAMESPACE_URL,'https://data.test.deqar.eu/activity/institutional-programme')` - `ce-bc9b47c0-1c29-589f-b9aa-89924f0e44be`

API uploads
-----------

A number of agency registrations as well as DEQAR reports were uploaded using the Registry Assistant API.

For the purpose of the pilot, the *upload.py* script contains static lists with a small number of agency and report IDs for upload.

The data is fetched from DEQAR using the [Web API](https://docs.deqar.eu/web_api_intro/) and then submitted to the Credential Registry.

